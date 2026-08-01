"""
seed.py — Robust seeder: 100+ records across all 6 tables.
Run: python -m app.database.init_db --seed
"""
from __future__ import annotations
import asyncio, random, uuid
from datetime import datetime, timedelta, timezone
from sqlalchemy import insert
from app.database.session import AsyncSessionLocal
from app.core.security import hash_password
from app.core.logger import get_logger
from app.models.employee import Employee
from app.models.action import Action
from app.models.audit import AuditLog
from app.models.review import ReviewQueue
from app.models.knowledge import KnowledgeBase
from app.models.document import Document
from app.models.settings import PlatformSettings

logger = get_logger("sentinel.seed")

# ─── Mock Data ─────────────────────────────────────────
FIRST_NAMES = ["Alice", "Bob", "Carol", "David", "Emma", "Frank", "Grace", "Henry", "Iris", "Jack",
               "Karen", "Leo", "Maya", "Nathan", "Olivia", "Peter", "Quinn", "Rachel", "Sam", "Tina"]
LAST_NAMES = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez",
              "Wilson", "Anderson", "Taylor", "Thomas", "Moore", "Jackson", "Martin", "Sanchez", "White", "Harris"]

DEPARTMENTS = ["Engineering", "Finance", "HR", "Legal", "Operations", "Sales", "Marketing", "Security", "Compliance", "Data Science"]
ROLES = ["admin", "reviewer", "analyst", "auditor", "stakeholder"]
DESIGNATIONS = ["Manager", "Senior Engineer", "Analyst", "Reviewer", "Director", "Specialist", "Coordinator", "Officer"]

ACTION_TYPES = [
    "Read Customer Profile", "Update Patient Record", "Export Financial Report",
    "Send Notification Email", "Delete Session Records", "Bulk Update User Flags",
    "Query Audit Database", "Modify Schema Column", "Archive Old Records",
    "Sync External API Data", "Generate Compliance PDF", "Revoke User Permissions",
    "Purge Log Files", "Update Risk Thresholds", "Read Config Settings",
    "Backup Database", "Create New User", "Disable API Key", "Change Access Level", "Audit Log Report",
]

OPERATIONS = ["READ", "WRITE", "DELETE", "UPDATE", "EXECUTE", "EXPORT", "IMPORT", "BULK_OP"]

REASONS = [
    "PII data modification requires review",
    "Bulk operation affecting >10k records",
    "Financial regulatory compliance required",
    "Irreversible action on production data",
    "Health data subject to HIPAA review",
    "Cross-border data transfer flagged",
    "Non-standard query pattern detected",
    "Potential data leak risk",
    "Compliance audit required",
    "Elevated permission usage",
]

MITIGATIONS = [
    "Limit batch size to ≤1,000 records",
    "Request additional sign-off from data owner",
    "Schedule during low-traffic window",
    "Create snapshot backup before execution",
    "Apply field-level encryption before export",
    "Enable audit logging for this operation",
    "Require 2-factor verification",
    "Add delay between operations",
    "Monitor for anomalies",
]

KB_CATEGORIES = ["Policy", "Procedure", "Technical", "Security", "Compliance", "Risk", "Best Practices", "Governance"]

KB_CONTENT = {
    "Policy": [
        "All data access must be logged and auditable. Retention is 7 years minimum.",
        "PII (Personally Identifiable Information) requires additional security controls.",
        "Financial records are subject to SOX compliance requirements.",
        "Sensitive healthcare data must comply with HIPAA regulations.",
        "Cross-border data transfers require legal review."
    ],
    "Procedure": [
        "To request data access, file a ticket via the governance portal.",
        "Data export requires approval from department head.",
        "Bulk operations must be scheduled with operations team.",
        "Schema changes require database team review.",
        "API keys are rotated quarterly for security."
    ],
    "Technical": [
        "Database connections use SSL/TLS encryption.",
        "All API calls are rate-limited to 1000 req/min.",
        "Backup retention is 30 days for development, 90 days for production.",
        "Indexes are optimized monthly by database team.",
        "Query timeouts are set to 5 minutes maximum."
    ],
    "Security": [
        "Role-based access control (RBAC) is enforced system-wide.",
        "MFA is required for administrative access.",
        "Passwords must be 12+ chars with special characters.",
        "Session tokens expire after 4 hours of inactivity.",
        "All authentication events are logged."
    ],
    "Compliance": [
        "Audit logs are immutable and cannot be modified.",
        "Access reviews are conducted quarterly.",
        "Incident response time SLA is 2 hours.",
        "Data retention policies must align with legal holds.",
        "Privacy impact assessments are required for new systems."
    ],
    "Risk": [
        "High-risk operations require multiple approvals.",
        "Risk scores are recalculated daily based on patterns.",
        "Unusual access patterns trigger automated alerts.",
        "Rollback procedures must be tested quarterly.",
        "Incident severity is classified using CVSS scoring."
    ],
    "Best Practices": [
        "Always run operations in staging before production.",
        "Document all manual changes with business justification.",
        "Use stored procedures instead of dynamic SQL.",
        "Implement circuit breakers for external API calls.",
        "Monitor error rates and set up alerting."
    ],
    "Governance": [
        "All system changes require change advisory board approval.",
        "AI decisions must be explainable and auditable.",
        "Graduated autonomy levels are based on risk assessment.",
        "Human oversight is required for critical operations.",
        "Annual governance reviews are mandatory."
    ]
}

DOC_TYPES = ["Policy", "Procedure", "Guideline", "Regulation", "Audit Report", "Risk Assessment", "Security Plan", "Training Manual"]

# ─── Seeder Functions ─────────────────────────────────────────

async def seed_employees(session):
    """Create 50+ realistic employees."""
    logger.info("Seeding employees…")
    employees = []
    
    # Shuffle to get unique combinations
    first_names_shuffled = FIRST_NAMES.copy()
    random.shuffle(first_names_shuffled)
    last_names_shuffled = LAST_NAMES.copy()
    random.shuffle(last_names_shuffled)
    
    # Create 50 employees with guaranteed unique usernames/emails
    for i in range(50):
        first = first_names_shuffled[i % len(first_names_shuffled)]
        last = last_names_shuffled[i % len(last_names_shuffled)]
        dept = random.choice(DEPARTMENTS)
        role = random.choice(ROLES)
        
        # Use index to ensure uniqueness
        username = f"{first.lower()}.{last.lower()}_{i}"
        email = f"{first.lower()}.{last.lower()}{i}@company.com"
        
        emp = Employee(
            employee_id=f"EMP{1000+i}",
            username=username,
            email=email,
            full_name=f"{first} {last}",
            hashed_password=hash_password("DemoPass123!"),
            role=role,
            department=dept,
            designation=random.choice(DESIGNATIONS),
            phone=f"+1-555-{random.randint(100,999)}-{random.randint(1000,9999)}",
            avatar_url=None,
            is_active=random.choice([True, True, True, False]),  # 75% active
            is_admin=role == "admin",
            language="en",
            timezone="UTC",
            last_login=datetime.now(timezone.utc) - timedelta(days=random.randint(0, 30)),
        )
        employees.append(emp)
    
    session.add_all(employees)
    await session.commit()
    logger.info(f"✓ Created {len(employees)} employees")
    return employees


async def seed_actions(session):
    """Create 100+ realistic actions."""
    logger.info("Seeding actions…")
    actions = []
    
    # Create 120 actions with varied statuses and risk scores
    statuses = ["pending", "pending_confirm", "pending_review", "executed", "rejected", "approved"]
    decisions = ["review", "autonomous", "confirmed", "rejected", "approved"]
    workflow_stages = ["intake", "risk_assessment", "policy_check", "execution", "completed"]
    
    for i in range(120):
        risk_score = random.randint(5, 98)
        status = random.choice(statuses)
        
        # Risk level based on risk score
        if risk_score < 30:
            risk_level = "low"
            decision = random.choice(["autonomous", "approved"])
        elif risk_score < 70:
            risk_level = "medium"
            decision = random.choice(["review", "confirmed"])
        else:
            risk_level = "high"
            decision = random.choice(["review", "rejected"])
        
        action = Action(
            conversation_id=f"CONV-{random.randint(1000, 9999)}",
            requested_by=f"user_{random.randint(1, 50)}",
            department=random.choice(DEPARTMENTS),
            natural_language=f"Request to {random.choice(ACTION_TYPES).lower()}",
            intent=f"Execute {random.choice(OPERATIONS)}",
            operation_type=random.choice(OPERATIONS),
            target_resource=f"/api/resource/{random.randint(1, 1000)}",
            target_table=random.choice(["users", "transactions", "audit_logs", "documents", "settings"]),
            affected_records=random.randint(1, 50000),
            action_json={
                "type": "database_operation",
                "resource": f"table_{random.randint(1,50)}",
                "details": random.choice(REASONS),
            },
            execution_plan=[
                {"step": 1, "description": "Validate request"},
                {"step": 2, "description": "Check permissions"},
                {"step": 3, "description": "Execute operation"},
            ],
            parameters={
                "batch_size": random.randint(100, 10000),
                "timeout": random.randint(30, 300),
                "retry_count": random.randint(1, 3),
            },
            risk_score=risk_score,
            risk_level=risk_level,
            risk_breakdown={
                "reversibility": random.randint(20, 100),
                "data_scope": random.randint(10, 100),
                "regulatory": random.randint(0, 100),
                "confidence": random.randint(40, 99),
            },
            reversibility=random.choice(["reversible", "irreversible", "partially_reversible"]),
            data_scope=random.choice(["single_record", "multiple_records", "table_wide", "cross_table"]),
            regulatory_category=random.choice(["hipaa", "gdpr", "sox", "pci", "none"]),
            policy_result=random.choice(["pass", "fail", "warning"]),
            policy_violations=[] if random.random() > 0.2 else [random.choice(REASONS)],
            decision=decision,
            confidence=random.randint(40, 99),
            workflow_stage=random.choice(workflow_stages),
            status=status,
            execution_result={"status": "success"} if status == "executed" else None,
            execution_logs=[
                {"timestamp": datetime.now(timezone.utc).isoformat(), "message": "Operation logged"}
            ],
            rollback_available=random.choice([True, True, False]),
            reviewed_by=f"reviewer_{random.randint(1, 20)}" if decision != "autonomous" else None,
            review_comment=random.choice(MITIGATIONS) if status == "pending_review" else None,
            created_at=datetime.now(timezone.utc) - timedelta(days=random.randint(0, 30)),
        )
        actions.append(action)
    
    session.add_all(actions)
    await session.commit()
    logger.info(f"✓ Created {len(actions)} actions")
    return actions


async def seed_audit_logs(session, actions):
    """Create 100+ audit log entries linked to actions."""
    logger.info("Seeding audit logs…")
    audit_logs = []
    
    outcomes = ["approved", "rejected", "executed", "pending", "rolled_back", "escalated"]
    event_types = ["action_review", "action_execution", "action_rejection", "manual_intervention", "policy_check", "risk_assessment"]
    
    for i in range(100):
        action = random.choice(actions)
        outcome = random.choice(outcomes)
        
        log = AuditLog(
            action_id=action.id,
            conversation_id=action.conversation_id,
            event_type=random.choice(event_types),
            action=action.operation_type,
            operation_type=action.operation_type,
            resource=action.target_resource,
            department=action.department,
            description=f"Audit entry for {action.operation_type}",
            actor=action.requested_by or f"user_{random.randint(1, 50)}",
            actor_role=random.choice(ROLES),
            reviewer=f"reviewer_{random.randint(1, 20)}" if outcome in ["approved", "rejected"] else None,
            risk_level=action.risk_level,
            risk_score=action.risk_score,
            risk_breakdown=action.risk_breakdown,
            decision=action.decision,
            outcome=outcome,
            rejection_reason=random.choice(REASONS) if outcome == "rejected" else None,
            execution_status="completed" if outcome in ["executed", "approved"] else "pending",
            execution_duration_ms=random.randint(100, 5000),
            rollback_executed=outcome == "rolled_back",
            metadata_={
                "source": "api",
                "method": random.choice(["POST", "PUT", "DELETE", "GET"]),
                "status_code": random.choice([200, 201, 400, 403, 500]),
            },
            ip_address=f"192.168.{random.randint(0, 255)}.{random.randint(1, 255)}",
            user_agent="Mozilla/5.0",
            timestamp=action.created_at + timedelta(hours=random.randint(0, 24)),
        )
        audit_logs.append(log)
    
    session.add_all(audit_logs)
    await session.commit()
    logger.info(f"✓ Created {len(audit_logs)} audit logs")
    return audit_logs


async def seed_review_queue(session, actions):
    """Create 30+ review queue items."""
    logger.info("Seeding review queue…")
    review_items = []
    
    priorities = ["low", "medium", "high", "critical"]
    statuses = ["pending", "in_progress", "approved", "rejected", "escalated"]
    
    # Get high-risk and medium-risk actions
    high_risk_actions = [a for a in actions if a.risk_level in ["medium", "high"]][:30]
    
    for action in high_risk_actions:
        status = random.choice(statuses)
        review = ReviewQueue(
            action_id=action.id,
            action_type=action.operation_type,
            action_description=action.natural_language,
            action_json=action.action_json,
            target_resource=action.target_resource,
            department=action.department,
            requested_by=action.requested_by,
            risk_level=action.risk_level,
            risk_score=action.risk_score,
            priority=random.choice(priorities),
            status=status,
            assigned_to=f"reviewer_{random.randint(1, 20)}" if status != "pending" else None,
            reviewer_comment=random.choice(MITIGATIONS) if status in ["approved", "rejected"] else None,
            reviewed_by=f"reviewer_{random.randint(1, 20)}" if status in ["approved", "rejected"] else None,
            reversibility=action.reversibility,
            affected_records=action.affected_records,
            confidence=action.confidence,
            intent=action.natural_language,
            risk_breakdown=action.risk_breakdown,
            created_at=action.created_at,
            updated_at=datetime.now(timezone.utc),
            reviewed_at=datetime.now(timezone.utc) if status in ["approved", "rejected"] else None,
            due_at=datetime.now(timezone.utc) + timedelta(days=random.randint(1, 7)),
        )
        review_items.append(review)
    
    session.add_all(review_items)
    await session.commit()
    logger.info(f"✓ Created {len(review_items)} review queue items")
    return review_items


async def seed_knowledge_base(session):
    """Create 80+ knowledge base entries."""
    logger.info("Seeding knowledge base…")
    kb_entries = []
    
    for category in KB_CATEGORIES:
        # Create 10 entries per category
        content_list = KB_CONTENT.get(category, ["Sample content"])
        
        for i in range(10):
            entry = KnowledgeBase(
                title=f"{category} - Article {i+1}",
                category=category,
                subcategory=random.choice(["Operational", "Technical", "Regulatory"]),
                content=random.choice(content_list),
                tags=[category.lower(), "production", "governance"],
                source="Internal Policy Database",
                author=f"admin_{random.randint(1, 5)}",
                is_active=True,
                version=random.randint(1, 5),
                relevance_score=random.uniform(0.6, 1.0),
            )
            kb_entries.append(entry)
    
    session.add_all(kb_entries)
    await session.commit()
    logger.info(f"✓ Created {len(kb_entries)} knowledge base entries")


async def seed_documents(session):
    """Create 50+ documents."""
    logger.info("Seeding documents…")
    documents = []
    
    for i in range(50):
        doc = Document(
            title=f"Document {i+1} - {random.choice(DOC_TYPES)}",
            doc_type=random.choice(DOC_TYPES),
            department=random.choice(DEPARTMENTS),
            description=f"Important document for {random.choice(DEPARTMENTS)} department",
            file_path=f"/documents/doc_{i+1}.pdf",
            file_size_bytes=random.randint(100000, 10000000),  # 100KB to 10MB
            mime_type="application/pdf",
            is_confidential=random.choice([False, False, False, True]),  # 25% confidential
            is_active=True,
            version=random.randint(1, 10),
            owner_id=f"user_{random.randint(1, 50)}",
            metadata_={
                "classification": random.choice(["public", "internal", "confidential"]),
                "compliance": random.choice(["hipaa", "gdpr", "sox", "none"]),
                "retention_years": random.randint(1, 10),
            },
            created_at=datetime.now(timezone.utc) - timedelta(days=random.randint(0, 365)),
            expires_at=datetime.now(timezone.utc) + timedelta(days=random.randint(30, 365)),
        )
        documents.append(doc)
    
    session.add_all(documents)
    await session.commit()
    logger.info(f"✓ Created {len(documents)} documents")


async def seed_settings(session):
    """Create platform-wide settings."""
    logger.info("Seeding settings…")
    
    settings_data = [
        {
            "key": "autonomous_threshold",
            "value": {"threshold": 30, "description": "Risk score below this is autonomous"},
            "category": "governance",
            "description": "Autonomous execution threshold",
        },
        {
            "key": "confirmation_threshold",
            "value": {"threshold": 70, "description": "Between autonomous and full review"},
            "category": "governance",
            "description": "Confirmation-required threshold",
        },
        {
            "key": "full_review_threshold",
            "value": {"threshold": 70, "description": "Risk score above this requires full review"},
            "category": "governance",
            "description": "Full review threshold",
        },
        {
            "key": "max_batch_size",
            "value": {"size": 10000, "unit": "records"},
            "category": "operations",
            "description": "Maximum batch operation size",
        },
        {
            "key": "audit_retention_days",
            "value": {"days": 2555, "years": 7},
            "category": "compliance",
            "description": "Audit log retention period",
        },
        {
            "key": "enable_adaptive_learning",
            "value": {"enabled": True, "learning_rate": 0.1},
            "category": "ai_governance",
            "description": "Enable adaptive risk scoring",
        },
        {
            "key": "enable_webhooks",
            "value": {"enabled": False, "retry_count": 3},
            "category": "integration",
            "description": "Enable webhook notifications",
        },
        {
            "key": "session_timeout_minutes",
            "value": {"timeout": 240, "grace_period": 30},
            "category": "security",
            "description": "User session timeout",
        },
        {
            "key": "mfa_required",
            "value": {"required_for_admins": True, "required_for_reviewers": False},
            "category": "security",
            "description": "MFA requirement policy",
        },
        {
            "key": "notification_email",
            "value": {"enabled": True, "send_summary": True, "summary_frequency": "daily"},
            "category": "notifications",
            "description": "Email notification settings",
        },
    ]
    
    settings_objs = []
    for s in settings_data:
        setting = PlatformSettings(
            key=s["key"],
            value=s["value"],
            category=s["category"],
            description=s["description"],
            is_secret=False,
            is_editable=True,
            updated_by="seed_script",
        )
        settings_objs.append(setting)
    
    session.add_all(settings_objs)
    await session.commit()
    logger.info(f"✓ Created {len(settings_objs)} settings")


async def run_seed():
    """Main seeding routine."""
    async with AsyncSessionLocal() as session:
        try:
            logger.info("=" * 60)
            logger.info("Starting comprehensive database seeding…")
            logger.info("=" * 60)
            
            # Create all records
            employees = await seed_employees(session)
            actions = await seed_actions(session)
            await seed_audit_logs(session, actions)
            await seed_review_queue(session, actions)
            await seed_knowledge_base(session)
            await seed_documents(session)
            await seed_settings(session)
            
            logger.info("=" * 60)
            logger.info("✓ Seeding completed successfully!")
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"✗ Seeding failed: {e}", exc_info=True)
            await session.rollback()
            raise

