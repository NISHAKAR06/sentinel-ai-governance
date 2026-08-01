"""
governance_routes.py — GET /governance/assess/{action_id}  POST /governance/decide
                        GET /governance/policies
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_optional_user
from app.repositories.action_repository import ActionRepository
from app.schemas.governance_schema import (
    GovernanceAssessmentResponse,
    DecideRequest,
    DecideResponse,
    RiskBreakdownItem,
    PolicyRuleResult,
)
from app.core.exceptions import RecordNotFoundError, to_http_exception, InvalidDecisionError
from app.core.enums import PolicyResult, DecisionType
from app.core.logger import api_logger

router = APIRouter()


@router.get(
    "/assess/{action_id}",
    response_model=GovernanceAssessmentResponse,
    summary="Get governance assessment for an action",
)
async def assess_action(
    action_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[dict] = Depends(get_optional_user),
):
    repo = ActionRepository(db)
    try:
        action = await repo.get_by_id_or_raise(action_id)
    except RecordNotFoundError as exc:
        raise to_http_exception(exc)

    # Build risk factors from stored breakdown
    raw_breakdown = action.risk_breakdown or {}
    breakdown_items = raw_breakdown.get("breakdown", [])
    risk_factors = [
        RiskBreakdownItem(
            factor=item.get("factor", "Unknown"),
            score=float(item.get("score", 0)),
            weight=float(item.get("weight", 0)),
            contribution=float(item.get("contribution", 0)),
            icon=item.get("icon", "fa-circle"),
        )
        for item in breakdown_items
    ]

    # Build policy rules from violations
    violations = action.policy_violations or []
    policy_rules = [
        PolicyRuleResult(
            rule_id=f"P-0{i+1}",
            name=v,
            description=v,
            status=PolicyResult.WARN,
            icon="fa-triangle-exclamation",
        )
        for i, v in enumerate(violations)
    ]
    if not policy_rules:
        policy_rules = [
            PolicyRuleResult(
                rule_id="P-00",
                name="All Policy Rules Passed",
                description="No policy violations detected",
                status=PolicyResult.PASS,
                icon="fa-shield-check",
            )
        ]

    # Build timeline
    timeline = [
        {"label": "Request received",     "icon": "fa-inbox",              "type": "primary",   "timestamp": action.created_at.isoformat(), "detail": action.intent},
        {"label": "Risk assessed",         "icon": "fa-triangle-exclamation","type": "warning",  "timestamp": action.created_at.isoformat(), "detail": f"Risk score: {action.risk_score}"},
        {"label": "Policy evaluated",      "icon": "fa-shield-halved",      "type": "info",      "timestamp": action.created_at.isoformat(), "detail": f"Policy result: {action.policy_result}"},
        {"label": f"Decision: {action.decision.upper()}", "icon": "fa-scale-balanced", "type": "primary", "timestamp": action.updated_at.isoformat(), "detail": ""},
    ]

    return GovernanceAssessmentResponse(
        action_id=action.id,
        current_stage=action.workflow_stage,
        risk_score=action.risk_score,
        risk_level=action.risk_level,
        risk_factors=risk_factors,
        policy_rules=policy_rules,
        decision=action.decision,
        confidence=action.confidence,
        reversible=(action.reversibility == "reversible"),
        reversibility=action.reversibility,
        data_scope=action.data_scope,
        regulations=[action.regulatory_category] if action.regulatory_category != "none" else [],
        timeline=timeline,
    )


@router.post(
    "/decide",
    response_model=DecideResponse,
    summary="Override governance decision for an action",
)
async def override_decision(
    payload: DecideRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[dict] = Depends(get_optional_user),
):
    repo = ActionRepository(db)
    try:
        action = await repo.get_by_id_or_raise(payload.action_id)
    except RecordNotFoundError as exc:
        raise to_http_exception(exc)

    previous = action.decision
    override_by = payload.override_by or (current_user.get("sub") if current_user else "system")

    await repo.update_by_id(
        payload.action_id,
        decision=payload.decision.value,
        status="pending",
    )

    api_logger.info(
        "Decision overridden",
        extra={
            "action_id":  str(payload.action_id),
            "from":       previous,
            "to":         payload.decision.value,
            "by":         override_by,
        },
    )

    return DecideResponse(
        action_id=payload.action_id,
        decision=payload.decision,
        previous_decision=previous,
        overridden_by=override_by,
        timestamp=datetime.now(timezone.utc),
    )


@router.get("/policies", summary="Get active policy rules list")
async def get_policies():
    """Returns the static list of active policy rules."""
    from app.engines.policy_engine import policy_engine
    rules = policy_engine.evaluate(
        operation_type="READ",
        target_table=None,
        target_resource="test",
        affected_records=1,
        regulatory_category="none",
        risk_score=0.0,
        requestor_role="user",
    ).rules
    return {
        "rules": [
            {
                "rule_id":     r.rule_id,
                "name":        r.name,
                "description": r.description,
                "status":      r.status.value,
                "icon":        r.icon,
            }
            for r in rules
        ]
    }
