"""
llm_service.py — Gemini LLM integration.
Calls Gemini API, extracts structured Action objects from natural language.
"""
from __future__ import annotations

import asyncio
import json
import re
from typing import Any, Dict, Optional

import google.generativeai as genai

from app.config import settings
from app.core.exceptions import LLMError, LLMTimeoutError, LLMParseError
from app.core.logger import service_logger
from app.prompts.system_prompt import SYSTEM_PROMPT
from app.prompts.governance_prompt import GOVERNANCE_EXTRACTION_PROMPT


class LLMService:
    """
    Wraps the Gemini generative model.
    Responsible for calling the API and parsing the JSON response.
    """

    def __init__(self) -> None:
        if settings.GEMINI_API_KEY:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self._model = genai.GenerativeModel(
                model_name=settings.GEMINI_MODEL,
                generation_config=genai.types.GenerationConfig(
                    temperature=settings.LLM_TEMPERATURE,
                    max_output_tokens=settings.LLM_MAX_TOKENS,
                    response_mime_type="application/json",
                ),
                system_instruction=SYSTEM_PROMPT,
            )
        else:
            self._model = None
            service_logger.warning("GEMINI_API_KEY not set — LLM calls will use mock fallback")

    async def extract_action(
        self,
        natural_language: str,
        conversation_id: Optional[str] = None,
        department: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Convert a natural language request into a structured Action dict.
        Falls back to a mock response when API key is absent (dev mode).
        """
        if self._model is None:
            return self._mock_extraction(natural_language)

        prompt = GOVERNANCE_EXTRACTION_PROMPT.format(
            natural_language=natural_language,
            department=department or "General",
        )

        try:
            response = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self._model.generate_content(prompt),
                ),
                timeout=settings.LLM_TIMEOUT,
            )
        except asyncio.TimeoutError:
            raise LLMTimeoutError(settings.LLM_TIMEOUT)
        except Exception as exc:
            raise LLMError(f"Gemini API error: {exc}") from exc

        raw_text = response.text.strip()
        return self._parse_json_response(raw_text, natural_language)

    async def generate_response(
        self,
        user_message: str,
        action_preview: Optional[Dict[str, Any]] = None,
        conversation_history: Optional[list] = None,
    ) -> str:
        """
        Generate a conversational response for the chat assistant.
        """
        if self._model is None:
            return self._mock_chat_response(user_message, action_preview)

        history_text = ""
        if conversation_history:
            history_text = "\n".join(
                f"{m['role'].capitalize()}: {m['content']}"
                for m in conversation_history[-6:]  # last 3 turns
            )

        ctx = ""
        if action_preview:
            ctx = f"\n\nGenerated Action:\n{json.dumps(action_preview, indent=2)}"

        prompt = (
            f"{history_text}\n\nUser: {user_message}{ctx}\n\n"
            "Provide a professional, concise response explaining what action has been "
            "extracted and what will happen next in the governance workflow. "
            "Do not use markdown. Keep it under 3 sentences."
        )

        try:
            response = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self._model.generate_content(prompt),
                ),
                timeout=settings.LLM_TIMEOUT,
            )
            return response.text.strip()
        except asyncio.TimeoutError:
            raise LLMTimeoutError(settings.LLM_TIMEOUT)
        except Exception as exc:
            raise LLMError(f"Chat generation failed: {exc}") from exc

    # ── JSON Parsing ──────────────────────────────────────────
    def _parse_json_response(self, raw: str, original: str) -> Dict[str, Any]:
        # Strip markdown code fences if present
        clean = re.sub(r"```(?:json)?", "", raw).strip().strip("`").strip()
        try:
            data = json.loads(clean)
            self._fill_defaults(data, original)
            return data
        except json.JSONDecodeError as exc:
            service_logger.error("LLM JSON parse failed", extra={"raw": raw[:300], "error": str(exc)})
            raise LLMParseError(raw)

    @staticmethod
    def _fill_defaults(data: Dict[str, Any], original: str) -> None:
        defaults = {
            "intent":              data.get("intent", original[:120]),
            "operation_type":      data.get("operation_type", "READ"),
            "target_resource":     data.get("target_resource", "unknown"),
            "target_table":        data.get("target_table"),
            "affected_records":    data.get("affected_records", 0),
            "action_json":         data.get("action_json", {"query": original}),
            "parameters":          data.get("parameters", {}),
            "reversibility":       data.get("reversibility", "reversible"),
            "data_scope":          data.get("data_scope", "single_record"),
            "regulatory_category": data.get("regulatory_category", "none"),
            "confidence":          float(data.get("confidence", 0.75)),
            "department":          data.get("department"),
        }
        data.update({k: v for k, v in defaults.items() if k not in data or data[k] is None})

    # ── Mock (dev without API key) ────────────────────────────
    @staticmethod
    def _mock_extraction(text: str) -> Dict[str, Any]:
        """Returns a sensible mock action when Gemini is not available."""
        return {
            "intent":              f"Process request: {text[:80]}",
            "operation_type":      "READ",
            "target_resource":     "employees table",
            "target_table":        "employees",
            "affected_records":    10,
            "reversibility":       "reversible",
            "data_scope":          "small_batch",
            "regulatory_category": "none",
            "confidence":          0.85,
            "department":          "Engineering",
            "action_json": {
                "operation": "SELECT",
                "table":     "employees",
                "filters":   {},
                "limit":     10,
                "natural_language": text,
            },
            "parameters": {},
        }

    @staticmethod
    def _mock_chat_response(message: str, action: Optional[Dict[str, Any]]) -> str:
        if action:
            return (
                f"I have analysed your request and generated a {action.get('operation_type', 'READ')} "
                f"action targeting {action.get('target_resource', 'the requested resource')}. "
                "The action will now proceed through the governance workflow for risk assessment."
            )
        return (
            "I have received your request and am processing it through the Sentinel AI "
            "governance pipeline. Please review the action details on the right."
        )


# ── Module-level singleton ────────────────────────────────────
llm_service = LLMService()
