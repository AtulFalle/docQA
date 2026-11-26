"""Database layer: declarative base, models and session helpers."""

from docqa_core.db.base import Base, TimestampMixin
from docqa_core.db.models import *  # noqa: F403  # re-export every model and value set
from docqa_core.db.models import __all__ as _models_all
from docqa_core.db.session import make_engine, make_sessionmaker, set_tenant_context

__all__ = [  # noqa: PLE0604  # extends the model package's own __all__
    *_models_all,
    "Base",
    "TimestampMixin",
    "make_engine",
    "make_sessionmaker",
    "set_tenant_context",
]
