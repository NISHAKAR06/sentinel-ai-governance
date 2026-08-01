"""
risk_engine.py — Risk score calculation engine.
Receives an Action context, returns RiskScore + RiskBreakdown.
Never touches the database directly.
"""
from __future__ import annotations

import math
from typing import Any, Dict, List

from app.core.enums import RiskLevel
from app.core.constants import (
    RISK_WEIGHT_REVERSIBILITY,
    RISK_WEIGHT_DATA_SCOPE,
    RISK_WEIGHT_REGULATORY,
    RISK_WEIGHT_LLM_CONFIDENCE,
    REVERSIBILITY_SCORE,
    DATA_SCOPE_SCORE,
    REGULATORY_SCORE,
    OPERATION_BASE_RISK,
    RISK_LOW_MAX,
    RISK_MEDIUM_MAX,
    RISK_HIGH_MAX,
)
from app.core.logger import engine_logger


class RiskResult:
    __slots__ = (
        "score", "level", "breakdown",
        "reversibility_score", "data_scope_score",
        "regulatory_score", "confidence_penalty",
        "operation_base", "final_score",
    )

    def __init__(
        self,
        score: float,
        level: RiskLevel,
        breakdown: List[Dict[str, Any]],
        reversibility_score: float,
        data_scope_score: float,
        regulatory_score: float,
        confidence_penalty: float,
        operation_base: float,
    ) -> None:
        self.score              = score
        self.level              = level
        self.breakdown          = breakdown
        self.reversibility_score   = reversibility_score
        self.data_scope_score      = data_scope_score
        self.regulatory_score      = regulatory_score
        self.confidence_penalty    = confidence_penalty
        self.operation_base        = operation_base
        self.final_score           = score


class RiskEngine:
    """
    Calculates a risk score (0–100) for a proposed AI action.

    Formula
    -------
    base  = OPERATION_BASE_RISK[operation_type]
    rev   = reversibility_raw  * WEIGHT_REVERSIBILITY
    scope = data_scope_raw     * WEIGHT_DATA_SCOPE
    reg   = regulatory_raw     * WEIGHT_REGULATORY
    conf  = confidence_penalty * WEIGHT_CONFIDENCE

    weighted = (rev + scope + reg + conf)
    raw_score = base * 0.40 + weighted * 0.60
    final_score = clamp(raw_score + learning_adjustment, 0, 100)
    """

    def calculate(
        self,
        operation_type: str,
        reversibility: str,
        data_scope: str,
        regulatory_category: str,
        llm_confidence: float,
        learning_adjustment: float = 0.0,
    ) -> RiskResult:
        # ── 1. Base risk from operation type ─────────────────
        op_upper   = operation_type.upper()
        op_base    = float(OPERATION_BASE_RISK.get(op_upper, 30))

        # ── 2. Factor scores ──────────────────────────────────
        rev_raw    = float(REVERSIBILITY_SCORE.get(reversibility, 30))
        scope_raw  = float(DATA_SCOPE_SCORE.get(data_scope, 20))
        reg_raw    = float(REGULATORY_SCORE.get(regulatory_category, 0))

        # Confidence penalty: low confidence → higher risk
        # confidence is 0–1; penalty increases as confidence decreases
        conf_penalty = round((1.0 - max(0.0, min(1.0, llm_confidence))) * 40, 2)

        # ── 3. Weighted component ─────────────────────────────
        weighted = (
            rev_raw    * RISK_WEIGHT_REVERSIBILITY  +
            scope_raw  * RISK_WEIGHT_DATA_SCOPE      +
            reg_raw    * RISK_WEIGHT_REGULATORY      +
            conf_penalty * RISK_WEIGHT_LLM_CONFIDENCE
        )

        # ── 4. Combine base + weighted ────────────────────────
        raw_score = op_base * 0.40 + weighted * 0.60

        # ── 5. Apply learning adjustment ──────────────────────
        adjusted = raw_score + learning_adjustment

        # ── 6. Clamp 0–100 ────────────────────────────────────
        final_score = round(max(0.0, min(100.0, adjusted)), 2)

        # ── 7. Determine level ────────────────────────────────
        level = self._score_to_level(final_score)

        # ── 8. Build breakdown ────────────────────────────────
        breakdown = self._build_breakdown(
            op_base, rev_raw, scope_raw, reg_raw, conf_penalty
        )

        engine_logger.debug(
            "Risk calculated",
            extra={
                "operation":  op_upper,
                "score":      final_score,
                "level":      level.value,
                "adjustment": learning_adjustment,
            },
        )

        return RiskResult(
            score=final_score,
            level=level,
            breakdown=breakdown,
            reversibility_score=rev_raw,
            data_scope_score=scope_raw,
            regulatory_score=reg_raw,
            confidence_penalty=conf_penalty,
            operation_base=op_base,
        )

    # ── Helpers ───────────────────────────────────────────────
    @staticmethod
    def _score_to_level(score: float) -> RiskLevel:
        if score <= RISK_LOW_MAX:
            return RiskLevel.LOW
        if score <= RISK_MEDIUM_MAX:
            return RiskLevel.MEDIUM
        if score <= RISK_HIGH_MAX:
            return RiskLevel.HIGH
        return RiskLevel.CRITICAL

    @staticmethod
    def _build_breakdown(
        op_base: float,
        rev_raw: float,
        scope_raw: float,
        reg_raw: float,
        conf_penalty: float,
    ) -> List[Dict[str, Any]]:
        return [
            {
                "factor":       "Operation Type",
                "score":        op_base,
                "weight":       0.40,
                "contribution": round(op_base * 0.40, 2),
                "icon":         "fa-bolt",
            },
            {
                "factor":       "Reversibility",
                "score":        rev_raw,
                "weight":       RISK_WEIGHT_REVERSIBILITY,
                "contribution": round(rev_raw * RISK_WEIGHT_REVERSIBILITY * 0.60, 2),
                "icon":         "fa-rotate-left",
            },
            {
                "factor":       "Data Scope",
                "score":        scope_raw,
                "weight":       RISK_WEIGHT_DATA_SCOPE,
                "contribution": round(scope_raw * RISK_WEIGHT_DATA_SCOPE * 0.60, 2),
                "icon":         "fa-database",
            },
            {
                "factor":       "Regulatory",
                "score":        reg_raw,
                "weight":       RISK_WEIGHT_REGULATORY,
                "contribution": round(reg_raw * RISK_WEIGHT_REGULATORY * 0.60, 2),
                "icon":         "fa-scale-balanced",
            },
            {
                "factor":       "Confidence Penalty",
                "score":        conf_penalty,
                "weight":       RISK_WEIGHT_LLM_CONFIDENCE,
                "contribution": round(conf_penalty * RISK_WEIGHT_LLM_CONFIDENCE * 0.60, 2),
                "icon":         "fa-brain",
            },
        ]

    @staticmethod
    def level_from_score(score: float) -> RiskLevel:
        return RiskEngine._score_to_level(score)


# ── Module-level singleton ────────────────────────────────────
risk_engine = RiskEngine()
