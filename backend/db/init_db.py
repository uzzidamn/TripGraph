from backend.db.models import Base
from backend.db.session import engine


def create_tables() -> None:
    """Create all tables if they don't exist. Safe to call on every startup."""
    Base.metadata.create_all(bind=engine)
