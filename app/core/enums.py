"""
enums.py — All application-wide enumerations.
"""
from enum import Enum


class DecisionType(str, Enum):
    AUTO       = "auto"
    CONFIRM    = "confirm"
    REVIEW     = "review"


class RiskLevel(str, Enum):
    LOW      = "low"
    MEDIUM   = "medium"
    HIGH     = "high"
    CRITICAL = "critical"


class ActionStatus(str, Enum):
    PENDING    = "pending"
    APPROVED   = "approved"
    REJECTED   = "rejected"
    MODIFIED   = "modified"
    EXECUTING  = "executing"
    COMPLETED  = "completed"
    FAILED     = "failed"
    ROLLED_BACK = "rolled_back"


class OperationType(str, Enum):
    READ         = "READ"
    CREATE       = "CREATE"
    UPDATE       = "UPDATE"
    DELETE       = "DELETE"
    BULK_UPDATE  = "BULK_UPDATE"
    BULK_DELETE  = "BULK_DELETE"
    EXPORT       = "EXPORT"
    IMPORT       = "IMPORT"
    ARCHIVE      = "ARCHIVE"
    RESTORE      = "RESTORE"


class ReversibilityType(str, Enum):
    REVERSIBLE   = "reversible"
    IRREVERSIBLE = "irreversible"


class DataScope(str, Enum):
    SINGLE    = "single_record"
    SMALL     = "small_batch"
    MEDIUM    = "medium_batch"
    LARGE     = "large_batch"
    ALL       = "all_records"


class RegulatoryCategory(str, Enum):
    NONE     = "none"
    GDPR     = "GDPR"
    HIPAA    = "HIPAA"
    SOX      = "SOX"
    PCI_DSS  = "PCI-DSS"
    ISO27001 = "ISO27001"


class ReviewPriority(str, Enum):
    LOW      = "low"
    MEDIUM   = "medium"
    HIGH     = "high"
    CRITICAL = "critical"


class PolicyResult(str, Enum):
    PASS    = "pass"
    WARN    = "warn"
    BLOCK   = "block"


class WorkflowStage(str, Enum):
    INTAKE    = "intake"
    RISK      = "risk"
    POLICY    = "policy"
    DECISION  = "decision"
    EXECUTION = "execution"
    AUDIT     = "audit"


class AuditLevel(str, Enum):
    MINIMAL  = "minimal"
    STANDARD = "standard"
    VERBOSE  = "verbose"


class Language(str, Enum):
    EN = "en"
    TA = "ta"
    HI = "hi"


class WSEventType(str, Enum):
    CONNECTED         = "connected"
    DISCONNECTED      = "disconnected"
    PING              = "ping"
    PONG              = "pong"
    DASHBOARD_UPDATE  = "dashboard_update"
    REVIEW_NEW        = "review_new"
    REVIEW_UPDATE     = "review_update"
    AUDIT_NEW         = "audit_new"
    NOTIFICATION      = "notification"
    ACTION_STATUS     = "action_status"
    EXECUTION_PROGRESS = "execution_progress"
    SYSTEM_HEALTH     = "system_health"
