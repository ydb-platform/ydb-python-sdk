from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)


class BaseWorkload(ABC):
    def __init__(self, driver, args):
        self.driver = driver
        self.args = args
        self.logger = logger

    @abstractmethod
    def create(self):
        pass

    @abstractmethod
    def run_slo(self, metrics):
        pass

    @abstractmethod
    def cleanup(self):
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        pass
