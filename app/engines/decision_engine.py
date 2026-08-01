"""
decision_engine.py — Combines risk score + policy result → AUTO / CONFIRM / REVIEW.
Pure logic, no I/O.
"""
from __future__ import annotations

from typing import Optional

from app.config import settings
from app.core.enums import DecisionType, PolicyResult, RiskLevel
from app.core.logger import engine_logger


class DecisionResult:
    __slots__ = ("decision", "reason", "risk_score", "policy_result")

    def __init__(
        self,
        decision: DecisionType,
        reason: str,
        risk_score: float,
        policy_result: PolicyResult,
    ) -> None:
        self.decision      = decision
        self.reason        = reason
        self.risk_score    = risk_score
        self.policy_result = policy_result


class DecisionEngine:
    """
    Decision matrix
    ---------------
    Policy BLOCK                          → REVIEW  (blocked — escalate)
    Policy WARN  + risk > review_thresh   → REVIEW
    Policy WARN  + risk > confirm_thresh  → CONFIRM
    Policy PASS  + risk > review_thresh   → REVIEW
    Policy PASS  + risk > confirm_thresh  → CONFIRM
    else                                  → AUTO
    """

    def decide(
        self,
        risk_score: float,
        policy_result: PolicyResult,
        risk_level: RiskLevel,
        override: Optional[DecisionType] = None,
    ) -> DecisionResult:
        # ── Hard override (human governance override) ─────────
        if override is not None:
            reason = f"Manual override to {override.value}"
            engine_logger.info("Decision override applied", extra={"override": override.value})
            return DecisionResult(
                decision=override,
                reason=reason,
                risk_score=risk_score,
                policy_result=policy_result,
            )

        auto_thresh    = float(settings.AUTO_APPROVE_THRESHOLD)
        confirm_thresh = float(settings.CONFIRM_THRESHOLD)
        review_thresh  = float(settings.HUMAN_REVIEW_THRESHOLD)

        # ── Policy block always → REVIEW ──────────────────────
        if policy_result == PolicyResult.BLOCK:
            decision = DecisionType.REVIEW
            reason   = "Blocked by policy — requires human review"

        # ── High risk → REVIEW ────────────────────────────────
        elif risk_score > review_thresh:
            decision = DecisionType.REVIEW
            reason   = f"Risk score {risk_score:.1f} exceeds review threshold {review_thresh}"

        # ── Medium-high risk or policy warnings → CONFIRM ─────
        elif risk_score > confirm_thresh or policy_result == PolicyResult.WARN:
            decision = DecisionType.CONFIRM
            if policy_result == PolicyResult.WARN:
                reason = f"Policy warning raised — confirmation required (risk {risk_score:.1f})"
            else:
                reason = f"Risk score {risk_score:.1f} exceeds confirmation threshold {confirm_thresh}"

        # ── Low risk, clean policy → AUTO ─────────────────────
        else:
            decision = DecisionType.AUTO
            reason   = f"Risk score {risk_score:.1f} is within auto-approve threshold {auto_thresh}"

        engine_logger.info(
            "Decision made",
            extra={
                "decision":  decision.value,
                "risk":      risk_score,
                "policy":    policy_result.value,
                "reason":    reason,
            },
        )

        return DecisionResult(
            decision=decision,
            reason=reason,
            risk_score=risk_score,
            policy_result=policy_result,
        )


# ── Singleton ─────────────────────────────────────────────────
decision_engine = DecisionEngine()
