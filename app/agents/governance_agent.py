"""
governance_agent.py — Main governance orchestrator.
Calls RiskEngine → PolicyEngine → DecisionEngine.
Returns AUTO / CONFIRM / REVIEW in the context.
"""
from __future__ import annotations

from datetime import datetime, timezone

from app.agents.base_agent import BaseAgent, AgentContext
from app.core.enums import WorkflowStage, PolicyResult
from app.engines.risk_engine import risk_engine
from app.engines.policy_engine import policy_engine
from app.engines.decision_engine import decision_engine
from app.core.logger import engine_logger


class GovernanceAgent(BaseAgent):
    name = "GovernanceAgent"

    async def execute(self, context: AgentContext) -> AgentContext:
        self._log("Governance evaluation started", action_id=context.action_id)
        context.workflow_stage = WorkflowStage.RISK.value

        action = context.action
        if action is None:
            context.errors.append("GovernanceAgent: No action in context")
            return context

        # ── 1. Risk Engine ────────────────────────────────────
        risk_result = risk_engine.calculate(
            operation_type=action.operation_type,
            reversibility=action.reversibility,
            data_scope=action.data_scope,
            regulatory_category=action.regulatory_category,
            llm_confidence=float(action.confidence or 0.7),
            learning_adjustment=0.0,  # applied later by learning service
        )

        context.risk_score    = risk_result.score
        context.risk_level    = risk_result.level.value
        context.risk_breakdown = risk_result.breakdown

        # Persist to action model
        action.risk_score    = risk_result.score
        action.risk_level    = risk_result.level.value
        action.risk_breakdown = {
            "breakdown":          risk_result.breakdown,
            "reversibility_score": risk_result.reversibility_score,
            "data_scope_score":    risk_result.data_scope_score,
            "regulatory_score":    risk_result.regulatory_score,
            "confidence_penalty":  risk_result.confidence_penalty,
        }
        self._log("Risk calculated", score=risk_result.score, level=risk_result.level.value)

        # ── 2. Policy Engine ──────────────────────────────────
        context.workflow_stage = WorkflowStage.POLICY.value
        action.workflow_stage  = WorkflowStage.POLICY.value

        policy_result = policy_engine.evaluate(
            operation_type=action.operation_type,
            target_table=action.target_table,
            target_resource=action.target_resource,
            affected_records=int(action.affected_records or 0),
            regulatory_category=action.regulatory_category,
            risk_score=risk_result.score,
            requestor_role=context.requestor_role,
        )

        context.policy_result    = policy_result.overall.value
        context.policy_violations = [
            r.message or r.name
            for r in policy_result.rules
            if r.status != PolicyResult.PASS
        ]

        action.policy_result    = policy_result.overall.value
        action.policy_violations = context.policy_violations

        self._log("Policy evaluated", overall=policy_result.overall.value)

        # ── 3. Decision Engine ────────────────────────────────
        context.workflow_stage = WorkflowStage.DECISION.value
        action.workflow_stage  = WorkflowStage.DECISION.value

        decision_result = decision_engine.decide(
            risk_score=risk_result.score,
            policy_result=policy_result.overall,
            risk_level=risk_result.level,
        )

        context.decision       = decision_result.decision.value
        context.decision_reason = decision_result.reason

        action.decision        = decision_result.decision.value
        action.workflow_stage  = WorkflowStage.DECISION.value

        self._log(
            "Decision made",
            decision=decision_result.decision.value,
            reason=decision_result.reason,
        )

        return context
