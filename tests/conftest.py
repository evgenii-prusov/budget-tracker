import pytest
from decimal import Decimal
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from budget_tracker.db import metadata
from budget_tracker.db import start_mappers
from budget_tracker.db import mapper_registry
from budget_tracker.model import Account
from budget_tracker.model import Entry
from budget_tracker.api import app
from budget_tracker.api import get_db_session

# Shared date constants
JAN_01 = date.fromisoformat("2025-01-01")
JAN_02 = date.fromisoformat("2025-01-02")
JAN_03 = date.fromisoformat("2025-01-03")


@pytest.fixture
def session():
    """Create an in-memory SQLite database session for testing."""
    # Create in-memory SQLite database
    from sqlalchemy.pool import StaticPool

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Create all tables from metadata
    metadata.create_all(engine)

    # Set up ORM mappers
    mapper_registry.dispose()
    start_mappers()

    # Create session
    Session = sessionmaker(bind=engine)
    session = Session()

    yield session

    # Cleanup
    session.close()
    engine.dispose()
    mapper_registry.dispose()


@pytest.fixture
def acc_eur() -> Account:
    return Account("a1", "EUR_1", "EUR", Decimal(35))


@pytest.fixture
def acc_rub() -> Account:
    return Account("a2", "RUB_1", "RUB", Decimal(0))


@pytest.fixture
def override_db_session(session):
    """Fixture to override the FastAPI dependency with test session."""

    def override_get_db_session():
        yield session

    app.dependency_overrides[get_db_session] = override_get_db_session
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def make_entry():
    """Factory fixture for creating Entry objects with customizable data.

    Usage:
        def test_something(make_entry):
            entry = make_entry(id="tx-1", amount=Decimal(100))
    """

    def _make_entry(
        id: str = "tx-1",
        account_id: str = "a-1",
        amount: Decimal = Decimal(0),
        date: date = JAN_01,
        category: str = "test",
        category_type: str = "EXPENSE",
    ) -> Entry:
        return Entry(id, account_id, amount, date, category, category_type)

    return _make_entry
