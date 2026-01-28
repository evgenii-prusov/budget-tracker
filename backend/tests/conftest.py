import pytest
from decimal import Decimal
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.adapters.orm import metadata
from app.adapters.orm import start_mappers
from app.adapters.orm import mapper_registry
from app.domain.model import Account
from app.domain.model import Posting
from app.domain.model import PostingType
from app.main import app
from app.api.dependencies import get_db_session
from fastapi.testclient import TestClient
from tests.constants import JAN_01, JAN_02, JAN_03


@pytest.fixture
def client(session):
    """Test client with database session already configured."""

    def override_get_db_session():
        yield session

    app.dependency_overrides[get_db_session] = override_get_db_session
    yield TestClient(app)
    app.dependency_overrides.clear()


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
def make_posting():
    """Factory fixture for creating Posting objects with customizable data.

    Usage:
        def test_something(make_posting):
            posting = make_posting(id="p-1", amount=Decimal(100))
    """

    def _make_posting(
        id: str = "p-1",
        account_id: str = "a-1",
        amount: Decimal = Decimal(0),
        posting_date: date = JAN_01,
        category_id: str | None = "test",
        posting_type: PostingType = PostingType.EXPENSE,
    ) -> Posting:
        return Posting(id, account_id, amount, posting_date, category_id, posting_type)

    return _make_posting


@pytest.fixture
def posting_1() -> Posting:
    """Posting on Jan 01 for testing (taxi expense)."""
    return Posting("p-1", "a-1", Decimal(0), JAN_01, "taxi", PostingType.EXPENSE)


@pytest.fixture
def posting_2() -> Posting:
    """Posting on Jan 02 for testing (food expense)."""
    return Posting("p-2", "a-1", Decimal(3), JAN_02, "food", PostingType.EXPENSE)


@pytest.fixture
def posting_3() -> Posting:
    """Posting on Jan 03 for testing (taxi expense)."""
    return Posting("p-3", "a-2", Decimal(1), JAN_03, "taxi", PostingType.EXPENSE)


@pytest.fixture
def test_data(client):
    """Creates a test account and category via API and returns their IDs."""
    # Create account
    acc_response = client.post(
        "/accounts/",
        json={
            "name": "Test Posting Account",
            "currency": "EUR",
            "initial_balance": "100.00",
        },
    )
    assert acc_response.status_code == 201
    account_id = acc_response.json()["account_id"]

    # Create category
    cat_response = client.post("/categories/", json={"name": "Test Category"})
    assert cat_response.status_code == 201
    category_id = cat_response.json()["category_id"]

    return {"account_id": account_id, "category_id": category_id}
