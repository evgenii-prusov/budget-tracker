from sqlalchemy.orm import Session

from app.domain.model import Settings
from app.service_layer.abstract_settings_repository import AbstractSettingsRepository


class SqlAlchemySettingsRepository(AbstractSettingsRepository):
    def __init__(self, session: Session):
        self.session = session

    def get(self) -> Settings | None:
        return self.session.get(Settings, Settings.SINGLETON_ID)

    def save(self, settings: Settings) -> None:
        self.session.merge(settings)
