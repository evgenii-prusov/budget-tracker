import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from budget_tracker.db import metadata, start_mappers, mapper_registry


@pytest.fixture
def session():
    """Create an in-memory SQLite database session for testing."""
    # Create in-memory SQLite database
    engine = create_engine("sqlite:///:memory:")

    # Create all tables from metadata
    metadata.create_all(engine)

    # Set up ORM mappers
    start_mappers()

    # Create session
    Session = sessionmaker(bind=engine)
    session = Session()

    yield session

    # Cleanup
    session.close()
    mapper_registry.dispose()
