"""
constants.py — Application-wide constants.
"""

# ── Risk score weights ────────────────────────────────────────
RISK_WEIGHT_REVERSIBILITY    = 0.30
RISK_WEIGHT_DATA_SCOPE       = 0.25
RISK_WEIGHT_REGULATORY       = 0.25
RISK_WEIGHT_LLM_CONFIDENCE   = 0.20

# ── Reversibility scores ──────────────────────────────────────
REVERSIBILITY_SCORE = {
    "reversible":   0,
    "irreversible": 60,
}

# ── Data scope scores ─────────────────────────────────────────
DATA_SCOPE_SCORE = {
    "single_record": 5,
    "small_batch":   20,
    "medium_batch":  40,
    "large_batch":   65,
    "all_records":   90,
}

# ── Regulatory category scores ────────────────────────────────
REGULATORY_SCORE = {
    "none":     0,
    "GDPR":    70,
    "HIPAA":   85,
    "SOX":     75,
    "PCI-DSS": 80,
    "ISO27001": 50,
}

# ── Operation type base risk ──────────────────────────────────
OPERATION_BASE_RISK = {
    "READ":        5,
    "CREATE":     20,
    "UPDATE":     35,
    "DELETE":     70,
    "BULK_UPDATE": 55,
    "BULK_DELETE": 85,
    "EXPORT":     30,
    "IMPORT":     40,
    "ARCHIVE":    25,
    "RESTORE":    20,
}

# ── Protected tables (policy) ─────────────────────────────────
PROTECTED_TABLES = ["employees", "audit_logs", "settings"]
RESTRICTED_OPERATIONS = ["DELETE", "TRUNCATE", "DROP", "BULK_DELETE"]
ADMIN_ONLY_OPERATIONS = ["IMPORT", "RESTORE"]

# ── Business hours ────────────────────────────────────────────
BUSINESS_HOURS_START = 9    # 09:00
BUSINESS_HOURS_END   = 18   # 18:00

# ── Pagination ────────────────────────────────────────────────
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE     = 200

# ── Audit retention ───────────────────────────────────────────
DEFAULT_AUDIT_RETENTION_DAYS = 90

# ── Learning service ──────────────────────────────────────────
LEARNING_APPROVAL_THRESHOLD   = 0.8   # 80% approval → reduce risk
LEARNING_REJECTION_THRESHOLD  = 0.3   # 30% approval → increase risk
MAX_RISK_ADJUSTMENT           = 20    # max points adjusted per cycle

# ── Token ─────────────────────────────────────────────────────
TOKEN_HEADER = "Authorization"
TOKEN_PREFIX = "Bearer"

# ── App metadata ─────────────────────────────────────────────
APP_NAME    = "Sentinel AI"
APP_VERSION = "2.0.0"

# ── Risk level thresholds ─────────────────────────────────────
RISK_LOW_MAX      = 30
RISK_MEDIUM_MAX   = 60
RISK_HIGH_MAX     = 80
# above 80 → CRITICAL
