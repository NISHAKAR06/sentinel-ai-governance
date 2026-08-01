"""
ai_agent.py — Receives natural language, calls Gemini, returns a structured Action.
Does NOT calculate risk. Does NOT execute SQL.
"""
from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from app.agents.base_agent import BaseAgent, AgentContext
from app.core.enums import WorkflowStage
from app.core.exceptions import LLMParseError
from app.core.logger import agent_logger
from app.services.llm_service import LLMService


class AIAgent(BaseAgent):
    name = "AIAgent"

    def __init__(self, llm_service: LLMService) -> None:
        self._llm = llm_service

    async def execute(self, context: AgentContext) -> AgentContext:
        self._log("AI Agent processing", conversation_id=context.conversation_id)
        context.workflow_stage = WorkflowStage.INTAKE.value

        # ── 1. Call LLM ───────────────────────────────────────
        structured = await self._llm.extract_action(
            natural_language=context.natural_language,
            conversation_id=context.conversation_id,
            department=context.department,
        )

        # ── 2. Build Action data dict ─────────────────────────
        action_data = self._to_action_data(structured, context)

        context.action    = type("_ActionProxy", (), action_data)()  # lightweight proxy
        context.action_id = str(action_data["id"])

        # Copy key fields onto the proxy
        for k, v in action_data.items():
            setattr(context.action, k, v)

        self._log(
            "Action extracted",
            action_id=context.action_id,
            operation=action_data.get("operation_type"),
            confidence=action_data.get("confidence"),
        )
        return context

    # ── Helpers ───────────────────────────────────────────────
    def _to_action_data(self, structured: Dict[str, Any], context: AgentContext) -> Dict[str, Any]:
        action_id = uuid.uuid4()
        return {
            "id":                  action_id,
            "conversation_id":     context.conversation_id,
            "requested_by":        context.requested_by,
            "department":          context.department or structured.get("department"),
            "natural_language":    context.natural_language,
            "intent":              structured.get("intent", "Unknown intent"),
            "operation_type":      structured.get("operation_type", "READ").upper(),
            "target_resource":     structured.get("target_resource", "unknown"),
            "target_table":        structured.get("target_table"),
            "affected_records":    int(structured.get("affected_records", 0)),
            "action_json":         structured.get("action_json", {}),
            "execution_plan":      [],
            "parameters":          structured.get("parameters", {}),
            "reversibility":       structured.get("reversibility", "reversible"),
            "data_scope":          structured.get("data_scope", "single_record"),
            "regulatory_category": structured.get("regulatory_category", "none"),
            "confidence":          float(structured.get("confidence", 0.7)),
            # Governance fields filled by GovernanceAgent
            "risk_score":      0.0,
            "risk_level":      "low",
            "risk_breakdown":  {},
            "policy_result":   "pass",
            "policy_violations": [],
            "decision":        "review",
            # Status
            "workflow_stage":  WorkflowStage.INTAKE.value,
            "status":          "pending",
            "execution_result": None,
            "execution_logs":   [],
            "rollback_available": True,
            "rollback_status": None,
            "reviewed_by":     None,
            "review_comment":  None,
            "created_at":      datetime.now(timezone.utc),
            "updated_at":      datetime.now(timezone.utc),
            "executed_at":     None,
            "completed_at":    None,
        }
