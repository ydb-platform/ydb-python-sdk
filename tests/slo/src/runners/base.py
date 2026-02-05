import logging
from abc import ABC, abstractmethod
from typing import Optional

import ydb


class BaseRunner(ABC):
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__module__)
        self.driver: Optional[ydb.Driver] = None

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

    async def run_async(self, args):
        raise NotImplementedError(f"Async mode not supported for {self.prefix}")

    @abstractmethod
    def cleanup(self, args):
        pass
