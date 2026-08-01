"""
logger.py — Structured JSON logging for Sentinel AI.
"""
import logging
import json
import sys
import traceback
from datetime import datetime, timezone
from typing import Any, Dict, Optional


class JSONFormatter(logging.Formatter):
    """Emit every log record as a single JSON line."""

    def format(self, record: logging.LogRecord) -> str:
        payload: Dict[str, Any] = {
            "ts":      datetime.now(timezone.utc).isoformat(),
            "level":   record.levelname,
            "logger":  record.name,
            "msg":     record.getMessage(),
            "module":  record.module,
            "func":    record.funcName,
            "line":    record.lineno,
        }

        # Extra fields injected by callers (e.g. log.info("…", extra={…}))
        for key, val in record.__dict__.items():
            if key not in {
                "msg", "args", "levelname", "levelno", "pathname", "filename",
                "module", "exc_info", "exc_text", "stack_info", "lineno",
                "funcName", "created", "msecs", "relativeCreated", "thread",
                "threadName", "processName", "process", "name", "message",
            }:
                payload[key] = val

        if record.exc_info:
            payload["exception"] = traceback.format_exception(*record.exc_info)

        return json.dumps(payload, default=str, ensure_ascii=False)


def get_logger(name: str, level: str = "INFO") -> logging.Logger:
    """Return a named logger with JSON formatting on stdout."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    logger.propagate = False
    return logger


# ── Module-level convenience loggers ─────────────────────────
app_logger      = get_logger("sentinel.app")
api_logger      = get_logger("sentinel.api")
agent_logger    = get_logger("sentinel.agent")
engine_logger   = get_logger("sentinel.engine")
service_logger  = get_logger("sentinel.service")
repo_logger     = get_logger("sentinel.repo")
ws_logger       = get_logger("sentinel.ws")
audit_logger    = get_logger("sentinel.audit")


# ── Request/Response helpers ──────────────────────────────────
def log_request(method: str, path: str, user_id: Optional[str] = None, **extra):
    api_logger.info(
        "HTTP request",
        extra={"method": method, "path": path, "user_id": user_id, **extra},
    )


def log_response(method: str, path: str, status_code: int, duration_ms: float, **extra):
    level = logging.WARNING if status_code >= 400 else logging.INFO
    api_logger.log(
        level,
        "HTTP response",
        extra={"method": method, "path": path, "status": status_code,
               "duration_ms": round(duration_ms, 2), **extra},
    )


def log_decision(action_id: str, decision: str, risk_score: float, **extra):
    agent_logger.info(
        "Governance decision",
        extra={"action_id": action_id, "decision": decision,
               "risk_score": risk_score, **extra},
    )


def log_execution(action_id: str, status: str, duration_ms: float = 0, **extra):
    service_logger.info(
        "Action execution",
        extra={"action_id": action_id, "status": status,
               "duration_ms": duration_ms, **extra},
    )
