"""
chat_routes.py — POST /chat/send  GET /chat/history  DELETE /chat/history
Routers receive requests and return responses. All logic in agents/services.
"""
from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_optional_user
from app.schemas.chat_schema import ChatRequest, ChatResponse, ConversationHistoryResponse
from app.schemas.action_schema import ActionPreview, ExecutionStep
from app.services.llm_service import LLMService, llm_service
from app.services.audit_service import AuditService
from app.agents.base_agent import AgentContext
from app.agents.ai_agent import AIAgent
from app.agents.planner_agent import PlannerAgent
from app.agents.governance_agent import GovernanceAgent
from app.repositories.action_repository import ActionRepository
from app.repositories.audit_repository import AuditRepository
from app.repositories.review_repository import ReviewRepository
from app.core.websocket_manager import ws_manager
from app.core.logger import api_logger

router = APIRouter()


def _build_services(db: AsyncSession):
    audit_repo  = AuditRepository(db)
    action_repo = ActionRepository(db)
    review_repo = ReviewRepository(db)
    return audit_repo, action_repo, review_repo


@router.post("/send", response_model=ChatResponse, summary="Send a chat message to Sentinel AI")
async def send_chat(
    payload: ChatRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[dict] = Depends(get_optional_user),
):
    audit_repo, action_repo, review_repo = _build_services(db)

    requested_by = current_user.get("sub", "anonymous") if current_user else "anonymous"
    role         = current_user.get("role", "user")      if current_user else "user"

    # ── Build context ────────────────────────────────────────
    context = AgentContext(
        natural_language=payload.message,
        conversation_id=payload.conversation_id or str(uuid.uuid4()),
        requested_by=requested_by,
        requestor_role=role,
        department=payload.department,
    )

    # ── AI Agent: NL → structured action ────────────────────
    ai_agent = AIAgent(llm_service)
    context  = await ai_agent.execute(context)

    # ── Planner Agent: generate execution plan ───────────────
    planner  = PlannerAgent()
    context  = await planner.execute(context)

    # ── Governance Agent: risk + policy + decision ───────────
    gov_agent = GovernanceAgent()
    context   = await gov_agent.execute(context)

    # ── Persist Action to DB ─────────────────────────────────
    a = context.action
    db_action = await action_repo.create(
        conversation_id=context.conversation_id,
        requested_by=requested_by,
        department=a.department,
        natural_language=a.natural_language,
        intent=a.intent,
        operation_type=a.operation_type,
        target_resource=a.target_resource,
        target_table=a.target_table,
        affected_records=a.affected_records,
        action_json=a.action_json,
        execution_plan=[s.__dict__ if hasattr(s, "__dict__") else s for s in context.execution_plan],
        parameters=a.parameters,
        reversibility=a.reversibility,
        data_scope=a.data_scope,
        regulatory_category=a.regulatory_category,
        confidence=a.confidence,
        risk_score=a.risk_score,
        risk_level=a.risk_level,
        risk_breakdown=a.risk_breakdown,
        policy_result=a.policy_result,
        policy_violations=a.policy_violations,
        decision=a.decision,
        workflow_stage=a.workflow_stage,
        status="pending",
        rollback_available=True,
    )

    # ── Audit log ─────────────────────────────────────────────
    audit_svc = AuditService(audit_repo)
    await audit_svc.log_chat(
        actor=requested_by,
        natural_language=payload.message,
        conversation_id=context.conversation_id,
        action_id=db_action.id,
        department=a.department,
    )

    # ── If REVIEW decision → create review queue entry ───────
    if context.decision == "review":
        from app.services.websocket_service import websocket_service
        priority = _risk_to_priority(a.risk_level)
        review_item = await review_repo.create(
            action_id=db_action.id,
            action_type=a.operation_type,
            action_description=a.intent,
            action_json=a.action_json,
            target_resource=a.target_resource,
            department=a.department,
            requested_by=requested_by,
            risk_level=a.risk_level,
            risk_score=a.risk_score,
            risk_breakdown=a.risk_breakdown,
            priority=priority,
            status="pending",
            reversibility=a.reversibility,
            affected_records=a.affected_records,
            confidence=a.confidence,
            intent=a.intent,
        )
        await websocket_service.broadcast_new_review(
            review_id=review_item.id,
            action_type=a.operation_type,
            risk_level=a.risk_level,
            priority=priority,
            department=a.department,
        )

    # ── LLM conversational response ───────────────────────────
    action_preview_dict = {
        "operation_type":  a.operation_type,
        "target_resource": a.target_resource,
        "intent":          a.intent,
        "confidence":      a.confidence,
        "risk_level":      a.risk_level,
    }
    ai_response = await llm_service.generate_response(
        payload.message,
        action_preview=action_preview_dict,
    )

    # ── Build ActionPreview for response ──────────────────────
    preview = ActionPreview(
        action_id=db_action.id,
        intent=a.intent,
        operation=a.operation_type,
        target_resource=a.target_resource,
        affected_records=a.affected_records,
        confidence=a.confidence,
        risk_level=a.risk_level,
        reversible=(a.reversibility == "reversible"),
        action_json=a.action_json,
        execution_plan=[
            ExecutionStep(**s) if isinstance(s, dict) else s
            for s in context.execution_plan
        ],
    )

    return ChatResponse(
        response=ai_response,
        conversation_id=context.conversation_id,
        action_preview=preview,
        requires_action=(context.decision != "auto"),
    )


@router.get("/history", response_model=ConversationHistoryResponse, summary="Get conversation history")
async def get_history(
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[dict] = Depends(get_optional_user),
):
    _, action_repo, _ = _build_services(db)
    from datetime import datetime
    return ConversationHistoryResponse(
        items=[], conversation_id="", total=0
    )


@router.delete("/history", summary="Clear conversation history")
async def clear_history(
    db: AsyncSession = Depends(get_db),
    current_user: Optional[dict] = Depends(get_optional_user),
):
    return {"message": "Conversation history cleared"}


def _risk_to_priority(risk_level: str) -> str:
    return {"critical": "critical", "high": "high", "medium": "medium"}.get(risk_level, "low")
