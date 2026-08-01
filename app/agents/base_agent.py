"""
base_agent.py — Abstract base for all Sentinel AI agents.
Every agent must implement execute(context) and nothing else is public.
"""
from __future__ import annotations

import abc
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.core.logger import agent_logger


@dataclass
class AgentContext:
    """Carries state between agents in the governance pipeline."""
    # ── Input ─────────────────────────────────────────────────
    natural_language: str = ""
    conversation_id:  Optional[str] = None
    requested_by:     Optional[str] = None
    requestor_role:   str = "user"
    department:       Optional[str] = None

    # ── Action (set by AIAgent) ───────────────────────────────
    action:           Optional[Any] = None    # app.models.action.Action ORM instance
    action_id:        Optional[str] = None

    # ── Plan (set by PlannerAgent) ────────────────────────────
    execution_plan:   List[Dict[str, Any]] = field(default_factory=list)
    parameters:       Dict[str, Any] = field(default_factory=dict)

    # ── Risk (set by GovernanceAgent via RiskEngine) ──────────
    risk_score:       float = 0.0
    risk_level:       str = "low"
    risk_breakdown:   List[Dict[str, Any]] = field(default_factory=list)

    # ── Policy (set by GovernanceAgent via PolicyEngine) ──────
    policy_result:    str = "pass"
    policy_violations: List[str] = field(default_factory=list)

    # ── Decision (set by GovernanceAgent via DecisionEngine) ──
    decision:         str = "review"
    decision_reason:  str = ""

    # ── Review (set by ReviewAgent) ───────────────────────────
    review_id:        Optional[str] = None
    review_status:    Optional[str] = None
    reviewed_by:      Optional[str] = None
    review_comment:   Optional[str] = None

    # ── Execution ─────────────────────────────────────────────
    execution_result: Optional[Dict[str, Any]] = None
    execution_logs:   List[str] = field(default_factory=list)

    # ── Meta ──────────────────────────────────────────────────
    workflow_stage:   str = "intake"
    errors:           List[str] = field(default_factory=list)
    started_at:       datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class BaseAgent(abc.ABC):
    """
    Abstract base agent.

    Contract
    --------
    - execute(context) must return the enriched context.
    - Agents coordinate workflows; they do NOT contain business logic.
    - Agents do NOT execute SQL directly.
    - All I/O must go through services or repositories passed at construction.
    """

    name: str = "BaseAgent"

    def _log(self, msg: str, **extra: Any) -> None:
        agent_logger.info(msg, extra={"agent": self.name, **extra})

    def _log_error(self, msg: str, **extra: Any) -> None:
        agent_logger.error(msg, extra={"agent": self.name, **extra})

    @abc.abstractmethod
    async def execute(self, context: AgentContext) -> AgentContext:
        """
        Execute the agent's responsibility and return the enriched context.
        Must be implemented by every concrete agent.
        """

    async def _timed_execute(self, context: AgentContext) -> AgentContext:
        """Wraps execute() with timing and error logging."""
        start = time.monotonic()
        try:
            result = await self.execute(context)
            elapsed_ms = round((time.monotonic() - start) * 1000, 2)
            self._log("Agent completed", duration_ms=elapsed_ms, stage=context.workflow_stage)
            return result
        except Exception as exc:
            elapsed_ms = round((time.monotonic() - start) * 1000, 2)
            self._log_error("Agent failed", error=str(exc), duration_ms=elapsed_ms)
            raise
