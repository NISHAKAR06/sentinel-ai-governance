# app/models/__init__.py — import all models so Base.metadata is populated
from app.models.employee   import Employee        # noqa: F401
from app.models.knowledge  import KnowledgeBase   # noqa: F401
from app.models.document   import Document        # noqa: F401
from app.models.action     import Action          # noqa: F401
from app.models.review     import ReviewQueue     # noqa: F401
from app.models.audit      import AuditLog        # noqa: F401
from app.models.settings   import PlatformSettings # noqa: F401

__all__ = [
    "Employee", "KnowledgeBase", "Document",
    "Action", "ReviewQueue", "AuditLog", "PlatformSettings",
]
