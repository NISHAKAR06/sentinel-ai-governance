"""
policy_engine.py — Organisational policy rule evaluation engine.
Returns a PolicyCheckResult with per-rule pass/warn/block verdicts.
Never touches the database.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.config import settings
from app.core.enums import PolicyResult
from app.core.logger import engine_logger


class PolicyRuleResult:
    __slots__ = ("rule_id", "name", "description", "status", "message", "icon")

    def __init__(
        self,
        rule_id: str,
        name: str,
        description: str,
        status: PolicyResult,
        message: Optional[str] = None,
        icon: str = "fa-shield-halved",
    ) -> None:
        self.rule_id     = rule_id
        self.name        = name
        self.description = description
        self.status      = status
        self.message     = message
        self.icon        = icon


class PolicyCheckResult:
    __slots__ = ("overall", "rules", "blocked_by")

    def __init__(
        self,
        overall: PolicyResult,
        rules: List[PolicyRuleResult],
        blocked_by: Optional[str] = None,
    ) -> None:
        self.overall    = overall
        self.rules      = rules
        self.blocked_by = blocked_by


class PolicyEngine:
    """
    Evaluates a proposed action against organisational policy rules.
    Rules are evaluated in order; first BLOCK verdict stops further checks.

    Rules implemented
    -----------------
    P-01  Protected Resource Guard
    P-02  Restricted Operation Guard
    P-03  Admin-Only Operation Guard
    P-04  Business Hours Guard
    P-05  Bulk Delete Confirmation Guard
    P-06  Regulatory Data Guard
    P-07  High Risk Approval Guard
    """

    def evaluate(
        self,
        operation_type: str,
        target_table: Optional[str],
        target_resource: str,
        affected_records: int,
        regulatory_category: str,
        risk_score: float,
        requestor_role: str = "user",
        is_business_hours: Optional[bool] = None,
    ) -> PolicyCheckResult:
        results: List[PolicyRuleResult] = []

        # ── P-01: Protected resource guard ───────────────────
        p01 = self._check_protected_resource(target_table, target_resource, operation_type)
        results.append(p01)
        if p01.status == PolicyResult.BLOCK:
            engine_logger.warning("Policy BLOCK: protected resource", extra={"table": target_table})
            return PolicyCheckResult(PolicyResult.BLOCK, results, p01.rule_id)

        # ── P-02: Restricted operation guard ─────────────────
        p02 = self._check_restricted_operation(operation_type)
        results.append(p02)
        if p02.status == PolicyResult.BLOCK:
            engine_logger.warning("Policy BLOCK: restricted operation", extra={"op": operation_type})
            return PolicyCheckResult(PolicyResult.BLOCK, results, p02.rule_id)

        # ── P-03: Admin-only operation guard ──────────────────
        p03 = self._check_admin_only(operation_type, requestor_role)
        results.append(p03)
        if p03.status == PolicyResult.BLOCK:
            return PolicyCheckResult(PolicyResult.BLOCK, results, p03.rule_id)

        # ── P-04: Business hours guard ────────────────────────
        p04 = self._check_business_hours(
            operation_type, risk_score, is_business_hours
        )
        results.append(p04)

        # ── P-05: Bulk delete confirmation guard ─────────────
        p05 = self._check_bulk_delete(operation_type, affected_records)
        results.append(p05)

        # ── P-06: Regulatory data guard ───────────────────────
        p06 = self._check_regulatory(regulatory_category, operation_type)
        results.append(p06)

        # ── P-07: High risk manual approval guard ─────────────
        p07 = self._check_high_risk_approval(risk_score)
        results.append(p07)

        # ── Determine overall ─────────────────────────────────
        has_block = any(r.status == PolicyResult.BLOCK for r in results)
        has_warn  = any(r.status == PolicyResult.WARN  for r in results)

        if has_block:
            blocked = next(r for r in results if r.status == PolicyResult.BLOCK)
            overall = PolicyResult.BLOCK
            blocked_by = blocked.rule_id
        elif has_warn:
            overall = PolicyResult.WARN
            blocked_by = None
        else:
            overall = PolicyResult.PASS
            blocked_by = None

        engine_logger.debug(
            "Policy evaluation complete",
            extra={"overall": overall.value, "rules": len(results)},
        )
        return PolicyCheckResult(overall, results, blocked_by)

    # ── Rule implementations ──────────────────────────────────
    def _check_protected_resource(
        self,
        target_table: Optional[str],
        target_resource: str,
        operation_type: str,
    ) -> PolicyRuleResult:
        protected = settings.PROTECTED_TABLES
        write_ops = {"DELETE", "UPDATE", "BULK_UPDATE", "BULK_DELETE", "IMPORT"}
        is_write  = operation_type.upper() in write_ops
        table     = (target_table or "").lower().strip()

        if is_write and table in [t.lower() for t in protected]:
            return PolicyRuleResult(
                rule_id="P-01",
                name="Protected Resource Guard",
                description="Prevents write operations on protected system tables",
                status=PolicyResult.BLOCK,
                message=f"Table '{table}' is protected and cannot be modified",
                icon="fa-lock",
            )
        return PolicyRuleResult(
            rule_id="P-01",
            name="Protected Resource Guard",
            description="Prevents write operations on protected system tables",
            status=PolicyResult.PASS,
            icon="fa-lock",
        )

    def _check_restricted_operation(self, operation_type: str) -> PolicyRuleResult:
        restricted = settings.RESTRICTED_OPERATIONS
        if operation_type.upper() in restricted:
            return PolicyRuleResult(
                rule_id="P-02",
                name="Restricted Operation Guard",
                description="Blocks operations that are globally restricted",
                status=PolicyResult.BLOCK,
                message=f"Operation '{operation_type}' is globally restricted",
                icon="fa-ban",
            )
        return PolicyRuleResult(
            rule_id="P-02",
            name="Restricted Operation Guard",
            description="Blocks operations that are globally restricted",
            status=PolicyResult.PASS,
            icon="fa-ban",
        )

    def _check_admin_only(self, operation_type: str, requestor_role: str) -> PolicyRuleResult:
        admin_ops = {"IMPORT", "RESTORE", "BULK_DELETE"}
        admin_roles = {"admin", "superadmin"}
        if operation_type.upper() in admin_ops and requestor_role not in admin_roles:
            return PolicyRuleResult(
                rule_id="P-03",
                name="Admin-Only Operation Guard",
                description="Certain operations require administrator privileges",
                status=PolicyResult.BLOCK,
                message=f"Operation '{operation_type}' requires admin role",
                icon="fa-user-shield",
            )
        return PolicyRuleResult(
            rule_id="P-03",
            name="Admin-Only Operation Guard",
            description="Certain operations require administrator privileges",
            status=PolicyResult.PASS,
            icon="fa-user-shield",
        )

    def _check_business_hours(
        self, operation_type: str, risk_score: float, is_business_hours: Optional[bool]
    ) -> PolicyRuleResult:
        if is_business_hours is None:
            hour = datetime.now(timezone.utc).hour
            is_bh = settings.BUSINESS_HOURS_START <= hour < settings.BUSINESS_HOURS_END
        else:
            is_bh = is_business_hours

        high_risk_ops = {"BULK_DELETE", "DELETE", "IMPORT"}
        if not is_bh and operation_type.upper() in high_risk_ops and risk_score > 50:
            return PolicyRuleResult(
                rule_id="P-04",
                name="Business Hours Guard",
                description="High-risk operations outside business hours require manager approval",
                status=PolicyResult.WARN,
                message="High-risk operation requested outside business hours",
                icon="fa-clock",
            )
        return PolicyRuleResult(
            rule_id="P-04",
            name="Business Hours Guard",
            description="High-risk operations outside business hours require manager approval",
            status=PolicyResult.PASS,
            icon="fa-clock",
        )

    def _check_bulk_delete(self, operation_type: str, affected_records: int) -> PolicyRuleResult:
        if operation_type.upper() in {"BULK_DELETE", "DELETE"} and affected_records > 1000:
            return PolicyRuleResult(
                rule_id="P-05",
                name="Bulk Delete Guard",
                description="Bulk deletions affecting more than 1000 records require explicit confirmation",
                status=PolicyResult.WARN,
                message=f"Bulk delete affects {affected_records} records — manager approval required",
                icon="fa-trash",
            )
        return PolicyRuleResult(
            rule_id="P-05",
            name="Bulk Delete Guard",
            description="Bulk deletions affecting more than 1000 records require confirmation",
            status=PolicyResult.PASS,
            icon="fa-trash",
        )

    def _check_regulatory(self, regulatory_category: str, operation_type: str) -> PolicyRuleResult:
        regulated = {"GDPR", "HIPAA", "SOX", "PCI-DSS"}
        write_ops = {"DELETE", "UPDATE", "BULK_UPDATE", "BULK_DELETE", "EXPORT"}
        if regulatory_category.upper() in regulated and operation_type.upper() in write_ops:
            return PolicyRuleResult(
                rule_id="P-06",
                name="Regulatory Data Guard",
                description="Regulated data operations require compliance review",
                status=PolicyResult.WARN,
                message=f"{regulatory_category} regulated data — compliance review required",
                icon="fa-scale-balanced",
            )
        return PolicyRuleResult(
            rule_id="P-06",
            name="Regulatory Data Guard",
            description="Regulated data operations require compliance review",
            status=PolicyResult.PASS,
            icon="fa-scale-balanced",
        )

    def _check_high_risk_approval(self, risk_score: float) -> PolicyRuleResult:
        if risk_score > 75:
            return PolicyRuleResult(
                rule_id="P-07",
                name="High Risk Approval Guard",
                description="Actions with risk score above 75 require explicit human approval",
                status=PolicyResult.WARN,
                message=f"Risk score {risk_score:.0f} exceeds high-risk threshold",
                icon="fa-triangle-exclamation",
            )
        return PolicyRuleResult(
            rule_id="P-07",
            name="High Risk Approval Guard",
            description="Actions with risk score above 75 require explicit human approval",
            status=PolicyResult.PASS,
            icon="fa-triangle-exclamation",
        )


# ── Singleton ─────────────────────────────────────────────────
policy_engine = PolicyEngine()
