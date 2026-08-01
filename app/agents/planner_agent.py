"""
planner_agent.py — Generates an ordered execution plan for the action.
Validates required fields and returns an ActionPlan attached to context.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.agents.base_agent import BaseAgent, AgentContext
from app.core.enums import OperationType, WorkflowStage
from app.core.exceptions import ValidationError


class PlannerAgent(BaseAgent):
    name = "PlannerAgent"

    # Step templates per operation type
    _STEP_TEMPLATES: Dict[str, List[Dict[str, Any]]] = {
        "READ": [
            {"step": 1, "description": "Validate read permissions",       "operation": "VALIDATE",  "reversible": True},
            {"step": 2, "description": "Execute query",                   "operation": "SELECT",    "reversible": True},
            {"step": 3, "description": "Format and return results",       "operation": "FORMAT",    "reversible": True},
        ],
        "CREATE": [
            {"step": 1, "description": "Validate input schema",           "operation": "VALIDATE",  "reversible": True},
            {"step": 2, "description": "Check for duplicates",            "operation": "CHECK",     "reversible": True},
            {"step": 3, "description": "Insert record(s)",                "operation": "INSERT",    "reversible": True},
            {"step": 4, "description": "Emit audit event",                "operation": "AUDIT",     "reversible": True},
        ],
        "UPDATE": [
            {"step": 1, "description": "Validate update scope",           "operation": "VALIDATE",  "reversible": True},
            {"step": 2, "description": "Snapshot current state (backup)", "operation": "SNAPSHOT",  "reversible": True},
            {"step": 3, "description": "Apply changes",                   "operation": "UPDATE",    "reversible": True},
            {"step": 4, "description": "Verify changes applied",          "operation": "VERIFY",    "reversible": True},
            {"step": 5, "description": "Emit audit event",                "operation": "AUDIT",     "reversible": True},
        ],
        "DELETE": [
            {"step": 1, "description": "Validate delete scope",           "operation": "VALIDATE",  "reversible": False},
            {"step": 2, "description": "Snapshot records before delete",  "operation": "SNAPSHOT",  "reversible": False},
            {"step": 3, "description": "Soft-delete or archive records",  "operation": "DELETE",    "reversible": False},
            {"step": 4, "description": "Cascade dependency checks",       "operation": "CASCADE",   "reversible": False},
            {"step": 5, "description": "Emit audit event",                "operation": "AUDIT",     "reversible": False},
        ],
        "BULK_UPDATE": [
            {"step": 1, "description": "Validate bulk scope",             "operation": "VALIDATE",  "reversible": True},
            {"step": 2, "description": "Snapshot affected records",       "operation": "SNAPSHOT",  "reversible": True},
            {"step": 3, "description": "Apply batch update in chunks",    "operation": "BULK",      "reversible": True},
            {"step": 4, "description": "Verify row count matches",        "operation": "VERIFY",    "reversible": True},
            {"step": 5, "description": "Emit audit event",                "operation": "AUDIT",     "reversible": True},
        ],
        "BULK_DELETE": [
            {"step": 1, "description": "Validate delete authorization",   "operation": "VALIDATE",  "reversible": False},
            {"step": 2, "description": "Export records to archive",       "operation": "ARCHIVE",   "reversible": False},
            {"step": 3, "description": "Execute batch deletion",          "operation": "BULK",      "reversible": False},
            {"step": 4, "description": "Verify record count",             "operation": "VERIFY",    "reversible": False},
            {"step": 5, "description": "Emit audit event",                "operation": "AUDIT",     "reversible": False},
        ],
        "EXPORT": [
            {"step": 1, "description": "Validate export permissions",     "operation": "VALIDATE",  "reversible": True},
            {"step": 2, "description": "Query and format data",           "operation": "SELECT",    "reversible": True},
            {"step": 3, "description": "Generate export file",            "operation": "EXPORT",    "reversible": True},
            {"step": 4, "description": "Emit audit event",                "operation": "AUDIT",     "reversible": True},
        ],
        "IMPORT": [
            {"step": 1, "description": "Validate import file schema",     "operation": "VALIDATE",  "reversible": True},
            {"step": 2, "description": "Dry-run import (staging)",        "operation": "STAGE",     "reversible": True},
            {"step": 3, "description": "Execute import transaction",      "operation": "INSERT",    "reversible": True},
            {"step": 4, "description": "Verify record counts",            "operation": "VERIFY",    "reversible": True},
            {"step": 5, "description": "Emit audit event",                "operation": "AUDIT",     "reversible": True},
        ],
        "ARCHIVE": [
            {"step": 1, "description": "Validate archive scope",          "operation": "VALIDATE",  "reversible": True},
            {"step": 2, "description": "Move records to archive table",   "operation": "ARCHIVE",   "reversible": True},
            {"step": 3, "description": "Verify archive integrity",        "operation": "VERIFY",    "reversible": True},
            {"step": 4, "description": "Emit audit event",                "operation": "AUDIT",     "reversible": True},
        ],
        "RESTORE": [
            {"step": 1, "description": "Validate restore authorization",  "operation": "VALIDATE",  "reversible": True},
            {"step": 2, "description": "Locate archive snapshot",         "operation": "LOCATE",    "reversible": True},
            {"step": 3, "description": "Restore records to live table",   "operation": "RESTORE",   "reversible": True},
            {"step": 4, "description": "Verify restored row count",       "operation": "VERIFY",    "reversible": True},
            {"step": 5, "description": "Emit audit event",                "operation": "AUDIT",     "reversible": True},
        ],
    }

    async def execute(self, context: AgentContext) -> AgentContext:
        self._log("Planning execution", action_id=context.action_id)
        context.workflow_stage = WorkflowStage.RISK.value

        action = context.action
        if action is None:
            raise ValidationError("No action found in context for planning")

        self._validate_action(action)

        operation = (action.operation_type or "READ").upper()
        template  = self._STEP_TEMPLATES.get(operation, self._STEP_TEMPLATES["READ"])

        plan: List[Dict[str, Any]] = []
        for step_tpl in template:
            plan.append({
                **step_tpl,
                "target":            action.target_resource,
                "estimated_records": action.affected_records,
                "status":            "pending",
            })

        context.execution_plan = plan
        self._log("Plan generated", steps=len(plan), operation=operation)
        return context

    def _validate_action(self, action: Any) -> None:
        required = ["intent", "operation_type", "target_resource"]
        for field_name in required:
            val = getattr(action, field_name, None)
            if not val:
                raise ValidationError(f"Missing required action field: {field_name}", field=field_name)
        # Validate operation type is known
        valid_ops = {op.value for op in OperationType}
        if action.operation_type.upper() not in valid_ops:
            raise ValidationError(
                f"Unknown operation type: {action.operation_type}",
                field="operation_type",
            )
