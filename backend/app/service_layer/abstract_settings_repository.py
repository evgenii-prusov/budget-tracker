import abc

from app.domain.model import Settings


class AbstractSettingsRepository(abc.ABC):
    @abc.abstractmethod
    def get(self) -> Settings | None:
        raise NotImplementedError()

    @abc.abstractmethod
    def save(self, settings: Settings) -> None:
        raise NotImplementedError()
