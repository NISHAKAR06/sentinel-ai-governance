"""
exceptions.py — Custom application exceptions with HTTP status codes.
"""
from fastapi import HTTPException, status


class SentinelBaseException(Exception):
    """Root exception for all Sentinel AI errors."""
    def __init__(self, message: str, code: str = "SENTINEL_ERROR"):
        self.message = message
        self.code = code
        super().__init__(message)


# ── Authentication & Authorisation ───────────────────────────
class AuthenticationError(SentinelBaseException):
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, "AUTH_ERROR")


class AuthorisationError(SentinelBaseException):
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(message, "AUTHZ_ERROR")


class TokenExpiredError(SentinelBaseException):
    def __init__(self):
        super().__init__("Token has expired", "TOKEN_EXPIRED")


# ── Validation ────────────────────────────────────────────────
class ValidationError(SentinelBaseException):
    def __init__(self, message: str, field: str = None):
        self.field = field
        super().__init__(message, "VALIDATION_ERROR")


# ── Database ──────────────────────────────────────────────────
class DatabaseError(SentinelBaseException):
    def __init__(self, message: str = "Database operation failed"):
        super().__init__(message, "DB_ERROR")


class RecordNotFoundError(SentinelBaseException):
    def __init__(self, resource: str, identifier: str):
        super().__init__(f"{resource} with id '{identifier}' not found", "NOT_FOUND")
        self.resource   = resource
        self.identifier = identifier


class DuplicateRecordError(SentinelBaseException):
    def __init__(self, resource: str, field: str):
        super().__init__(f"{resource} with that {field} already exists", "DUPLICATE")


class RollbackError(SentinelBaseException):
    def __init__(self, action_id: str, reason: str):
        super().__init__(
            f"Rollback failed for action {action_id}: {reason}",
            "ROLLBACK_ERROR"
        )
        self.action_id = action_id
        self.reason    = reason


# ── LLM / AI ──────────────────────────────────────────────────
class LLMError(SentinelBaseException):
    def __init__(self, message: str = "LLM API call failed"):
        super().__init__(message, "LLM_ERROR")


class LLMTimeoutError(SentinelBaseException):
    def __init__(self, timeout_seconds: int):
        super().__init__(
            f"LLM request timed out after {timeout_seconds}s",
            "LLM_TIMEOUT"
        )


class LLMParseError(SentinelBaseException):
    def __init__(self, raw_response: str):
        super().__init__(
            "Failed to parse structured action from LLM response",
            "LLM_PARSE_ERROR"
        )
        self.raw_response = raw_response


# ── Governance / Engines ──────────────────────────────────────
class PolicyBlockedError(SentinelBaseException):
    def __init__(self, rule: str, reason: str):
        super().__init__(f"Action blocked by policy '{rule}': {reason}", "POLICY_BLOCKED")
        self.rule   = rule
        self.reason = reason


class RiskCalculationError(SentinelBaseException):
    def __init__(self, message: str):
        super().__init__(message, "RISK_CALC_ERROR")


class InvalidDecisionError(SentinelBaseException):
    def __init__(self, decision: str):
        super().__init__(f"Invalid decision type: {decision}", "INVALID_DECISION")


# ── Execution ─────────────────────────────────────────────────
class ExecutionError(SentinelBaseException):
    def __init__(self, action_id: str, reason: str):
        super().__init__(f"Execution failed for action {action_id}: {reason}", "EXEC_ERROR")
        self.action_id = action_id
        self.reason    = reason


class ActionNotApprovedError(SentinelBaseException):
    def __init__(self, action_id: str, status: str):
        super().__init__(
            f"Action {action_id} cannot be executed — current status: {status}",
            "NOT_APPROVED"
        )


class ActionAlreadyExecutedError(SentinelBaseException):
    def __init__(self, action_id: str):
        super().__init__(f"Action {action_id} has already been executed", "ALREADY_EXECUTED")


# ── WebSocket ─────────────────────────────────────────────────
class WebSocketError(SentinelBaseException):
    def __init__(self, message: str):
        super().__init__(message, "WS_ERROR")


# ── HTTP exception factory ────────────────────────────────────
def to_http_exception(exc: SentinelBaseException) -> HTTPException:
    """Convert a domain exception to an HTTPException."""
    status_map = {
        "AUTH_ERROR":        status.HTTP_401_UNAUTHORIZED,
        "AUTHZ_ERROR":       status.HTTP_403_FORBIDDEN,
        "TOKEN_EXPIRED":     status.HTTP_401_UNAUTHORIZED,
        "NOT_FOUND":         status.HTTP_404_NOT_FOUND,
        "DUPLICATE":         status.HTTP_409_CONFLICT,
        "VALIDATION_ERROR":  status.HTTP_422_UNPROCESSABLE_ENTITY,
        "POLICY_BLOCKED":    status.HTTP_403_FORBIDDEN,
        "NOT_APPROVED":      status.HTTP_409_CONFLICT,
        "ALREADY_EXECUTED":  status.HTTP_409_CONFLICT,
        "LLM_TIMEOUT":       status.HTTP_504_GATEWAY_TIMEOUT,
    }
    http_status = status_map.get(exc.code, status.HTTP_500_INTERNAL_SERVER_ERROR)
    return HTTPException(
        status_code=http_status,
        detail={"code": exc.code, "message": exc.message},
    )
