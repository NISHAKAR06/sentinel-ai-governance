"""
learning_service.py — Adaptive learning: reads audit history, adjusts future risk scores.
"""
from __future__ import annotations

from typing import Dict, Optional

from app.config import settings
from app.core.constants import MAX_RISK_ADJUSTMENT
from app.core.logger import service_logger
from app.repositories.audit_repository import AuditRepository


class LearningService:
    """
    Reads audit history per (operation_type, target_table) combination.
    If approval rate is high → reduce risk adjustment.
    If approval rate is low  → increase risk adjustment.
    Adjustments are bounded to ±MAX_RISK_ADJUSTMENT points.
    """

    def __init__(self, audit_repo: AuditRepository) -> None:
        self._repo   = audit_repo
        self._cache: Dict[str, float] = {}  # key → adjustment value

    async def get_adjustment(
        self,
        operation_type: str,
        target_table: Optional[str] = None,
    ) -> float:
        """Return a risk score adjustment based on learned patterns."""
        if not settings.LEARNING_ENABLED:
            return 0.0

        key = f"{operation_type.upper()}:{(target_table or 'any').lower()}"

        # Return cached value if available
        if key in self._cache:
            return self._cache[key]

        adjustment = await self._compute_adjustment(operation_type, target_table)
        self._cache[key] = adjustment
        return adjustment

    async def invalidate_cache(
        self,
        operation_type: Optional[str] = None,
        target_table: Optional[str] = None,
    ) -> None:
        """Invalidate cached adjustments after new audit data arrives."""
        if operation_type:
            key = f"{operation_type.upper()}:{(target_table or 'any').lower()}"
            self._cache.pop(key, None)
        else:
            self._cache.clear()

    async def _compute_adjustment(
        self,
        operation_type: str,
        target_table: Optional[str],
    ) -> float:
        """
        Fetch outcome distribution from audit logs and compute adjustment.
        - High approval rate (> 80%): lower risk by up to MAX_RISK_ADJUSTMENT
        - Low approval rate  (< 30%): raise risk by up to MAX_RISK_ADJUSTMENT
        """
        try:
            outcome_counts = await self._repo.outcome_counts(days=90)
            total     = sum(outcome_counts.values())
            approved  = outcome_counts.get("approved", 0) + outcome_counts.get("auto", 0)
            rejected  = outcome_counts.get("rejected", 0)

            if total < settings.MIN_SAMPLES_TO_LEARN:
                return 0.0

            approval_rate = approved / total

            if approval_rate >= 0.8:
                # Well-established safe pattern → reduce risk
                adjustment = -round(
                    (approval_rate - 0.8) / 0.2 * MAX_RISK_ADJUSTMENT * settings.LEARNING_RATE, 2
                )
            elif approval_rate <= 0.3:
                # High rejection rate → increase risk
                rejection_rate = rejected / total
                adjustment = round(
                    (0.3 - approval_rate) / 0.3 * MAX_RISK_ADJUSTMENT * settings.LEARNING_RATE, 2
                )
            else:
                adjustment = 0.0

            # Clamp
            adjustment = max(-MAX_RISK_ADJUSTMENT, min(MAX_RISK_ADJUSTMENT, adjustment))

            service_logger.debug(
                "Learning adjustment computed",
                extra={
                    "operation":    operation_type,
                    "table":        target_table,
                    "total":        total,
                    "approval_pct": f"{approval_rate*100:.1f}%",
                    "adjustment":   adjustment,
                },
            )
            return adjustment

        except Exception as exc:
            service_logger.warning("Learning adjustment failed", extra={"error": str(exc)})
            return 0.0
