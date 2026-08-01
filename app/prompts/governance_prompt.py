"""
governance_prompt.py — Prompt template for structured action extraction.
"""

GOVERNANCE_EXTRACTION_PROMPT = """
Extract a structured governance action from the following request.

Department: {department}
Request: "{natural_language}"

Return ONLY a JSON object with this exact schema:
{{
  "intent":              "one-sentence description of what the user wants to do",
  "operation_type":      "READ|CREATE|UPDATE|DELETE|BULK_UPDATE|BULK_DELETE|EXPORT|IMPORT|ARCHIVE|RESTORE",
  "target_resource":     "human-readable resource name (e.g. 'employees table', 'S3 bucket', 'audit logs')",
  "target_table":        "database table name if applicable, else null",
  "affected_records":    0,
  "reversibility":       "reversible|irreversible",
  "data_scope":          "single_record|small_batch|medium_batch|large_batch|all_records",
  "regulatory_category": "none|GDPR|HIPAA|SOX|PCI-DSS|ISO27001",
  "confidence":          0.85,
  "department":          "{department}",
  "action_json": {{
    "operation":  "SQL or API operation",
    "table":      "target table name or null",
    "filters":    {{}},
    "parameters": {{}},
    "limit":      null
  }},
  "parameters": {{}}
}}
""".strip()


PLANNER_PROMPT = """
Given the following action details, generate a step-by-step execution plan.

Action: {intent}
Operation: {operation_type}
Target: {target_resource}
Affected records: {affected_records}

Return a JSON array of execution steps, each with:
- step (int)
- description (string)
- operation (string)
- target (string)
- estimated_records (int)
- reversible (bool)
""".strip()
