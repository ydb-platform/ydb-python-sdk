# -*- coding: utf-8 -*-
import dataclasses
import logging
import random
import string
from datetime import datetime
from threading import Lock

logger = logging.getLogger(__name__)


MAX_UINT64 = 2**64 - 1


def generate_random_string(min_len, max_len):
    strlen = random.randint(min_len, max_len)
    return "".join(random.choices(string.ascii_lowercase, k=strlen))


@dataclasses.dataclass
class Row:
    object_id: int
    payload_str: str
    payload_double: float
    payload_timestamp: datetime


@dataclasses.dataclass
class RowGenerator:
    id_counter: int = 0
    lock = Lock()

    def get(self):
        with self.lock:
            self.id_counter += 1
            if self.id_counter >= MAX_UINT64:
                self.id_counter = 0
                logger.warning("RowGenerator: maxint reached")

        return Row(
            object_id=self.id_counter,
            payload_str=generate_random_string(20, 40),
            payload_double=random.random(),
            payload_timestamp=datetime.now(),
        )


def batch_generator(args, start_id=0):
    row_generator = RowGenerator(start_id)
    remain = args.initial_data_count

    while True:
        size = min(remain, args.batch_size)
        if size < 1:
            return
        yield [row_generator.get() for _ in range(size)]
        remain -= size
