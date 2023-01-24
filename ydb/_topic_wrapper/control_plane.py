from dataclasses import dataclass
from typing import Union, List


@dataclass
class CreateTopicRequest:
    path: str
    consumers: Union[List["Consumer"], None] = None


@dataclass
class Consumer:
    name: str
