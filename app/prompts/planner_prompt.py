"""
planner_prompt.py — Prompt for execution plan generation (kept for direct LLM calls if needed).
"""
from app.prompts.governance_prompt import PLANNER_PROMPT  # re-export

__all__ = ["PLANNER_PROMPT"]
