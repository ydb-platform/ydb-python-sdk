import ydb
import logging
from abc import ABC, abstractmethod


class BaseRunner(ABC):
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__module__)
        self.driver = None

    @property
    @abstractmethod
    def prefix(self) -> str:
        pass

    def set_driver(self, driver: ydb.Driver):
        self.driver = driver

    @abstractmethod
    def create(self, args):
        pass

    @abstractmethod
    def run(self, args):
        pass

    @abstractmethod
    def cleanup(self, args):
        pass
