from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import UnmappedClassError
from sqlalchemy.orm.util import class_mapper

from app.adapters.orm import start_mappers, metadata
from app.domain.model import Account
from app.core.config import get_database_url
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class Database:
    def __init__(self, database_url: str | None = None):
        self.database_url = database_url or get_database_url()
        self.engine = None
        self.session_factory = None

    def init(self):
        """Initializes the database connection and mappers."""
        if self.engine:
            return

        logger.info("Initializing database with URL: %s", self.database_url)
        self.engine = create_engine(self.database_url)
        self.session_factory = sessionmaker(bind=self.engine)

        self._ensure_mappers_started()

        # Create tables (temporary solution until migrations are added)
        metadata.create_all(self.engine)

    def _ensure_mappers_started(self) -> None:
        """Initialize ORM mappers if they are not already configured."""
        try:
            class_mapper(Account)
        except UnmappedClassError:
            logger.info("Starting ORM mappers")
            start_mappers()

    def get_session(self):
        if not self.session_factory:
            raise RuntimeError("Database not initialized. Call init() first.")
        return self.session_factory()

    def dispose(self):
        if self.engine:
            self.engine.dispose()
            self.engine = None
            self.session_factory = None
            logger.info("Database connection disposed")
