import os

import pytest
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.adapters.orm import metadata
from app.adapters.orm import start_mappers
from app.adapters.orm import mapper_registry
from app.domain.model import Account
from app.domain.model import Posting
from app.domain.model import PostingType
from app.main import app
from app.api.dependencies import get_db_session
from fastapi.testclient import TestClient
from tests.constants import JAN_01, JAN_02, JAN_03, TEST_API_KEY


@pytest.fixture(scope="session", autouse=True)
def set_api_key():
    """Override API_KEY for the entire test session regardless of the outer environment."""
    original = os.environ.get("API_KEY")
    os.environ["API_KEY"] = TEST_API_KEY
    yield
    if original is None:
        os.environ.pop("API_KEY", None)
    else:
        os.environ["API_KEY"] = original


@pytest.fixture(scope="session")
def postgres_engine():
    """Spin up a throwaway Postgres container for the test session."""
    from testcontainers.postgres import PostgresContainer

    with PostgresContainer("postgres:17") as pg:
        engine = create_engine(pg.get_connection_url())
        metadata.create_all(engine)

        mapper_registry.dispose()
        start_mappers()

        yield engine


@pytest.fixture
def session(postgres_engine):
    """Postgres-backed session wrapped in a transaction that rolls back after each test.

    Uses the "join session to external transaction" pattern so that commits
    inside the application code are converted to savepoints, and the whole
    transaction is rolled back at cleanup.
    """
    connection = postgres_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(session):
    """Test client with database session and auth header configured."""

    def override_get_db_session():
        yield session

    app.dependency_overrides[get_db_session] = override_get_db_session
    yield TestClient(app, headers={"Authorization": f"Bearer {TEST_API_KEY}"})
    app.dependency_overrides.clear()


@pytest.fixture
def client_no_auth(session):
    """Test client with NO Authorization header — for testing 401 responses."""

    def override_get_db_session():
        yield session

    app.dependency_overrides[get_db_session] = override_get_db_session
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def acc_eur() -> Account:
    return Account("a1", "EUR_1", "EUR", Decimal(35))


@pytest.fixture
def acc_rub() -> Account:
    return Account("a2", "RUB_1", "RUB", Decimal(0))


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
    """Creates a test account and category hierarchy via API and returns their IDs.

    Creates a parent category and subcategory. The subcategory ID is returned
    as 'category_id' since postings must reference subcategories.
    """
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

    parent_response = client.post(
        "/categories/",
        json={"name": "Test Parent", "category_type": "EXPENSE"},
    )
    assert parent_response.status_code == 201
    parent_id = parent_response.json()["category_id"]

    # Also create an INCOME parent + subcategory for income posting tests
    income_parent_response = client.post(
        "/categories/",
        json={"name": "Income Parent", "category_type": "INCOME"},
    )
    assert income_parent_response.status_code == 201
    income_parent_id = income_parent_response.json()["category_id"]

    sub_response = client.post(
        "/categories/",
        json={
            "name": "Test Subcategory",
            "category_type": "EXPENSE",
            "parent_id": parent_id,
        },
    )
    assert sub_response.status_code == 201
    category_id = sub_response.json()["category_id"]

    income_sub_response = client.post(
        "/categories/",
        json={
            "name": "Income Subcategory",
            "category_type": "INCOME",
            "parent_id": income_parent_id,
        },
    )
    assert income_sub_response.status_code == 201
    income_category_id = income_sub_response.json()["category_id"]

    return {
        "account_id": account_id,
        "category_id": category_id,
        "parent_category_id": parent_id,
        "income_category_id": income_category_id,
        "income_parent_id": income_parent_id,
    }
