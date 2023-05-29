# -*- coding: utf-8 -*-
import dataclasses
import logging
import random
import string
from datetime import datetime

logger = logging.getLogger(__name__)


MaxUi32 = 2**32 - 1


def hash_ui32(value):
    return abs(hash(str(value))) % MaxUi32


def generate_random_string(min_len, max_len):
    strlen = random.randint(min_len, max_len)
    return "".join(random.choices(string.ascii_lowercase, k=strlen))


@dataclasses.dataclass(slots=True)
class Row:
    object_id_key: int
    object_id: int
    payload_str: str
    payload_double: float
    payload_timestamp: datetime

    # First id in current shard
    def get_shard_id(self, partitions_count):
        shard_size = int((MaxUi32 + 1) / partitions_count)
        return self.object_id_key / shard_size


@dataclasses.dataclass
class RowGenerator:
    id_counter: int = 0

    def get(self):
        self.id_counter += 1
        if self.id_counter >= MaxUi32:
            self.id_counter = 0
            logger.warning("RowGenerator: maxint reached")

        return Row(
            object_id_key=hash_ui32(self.id_counter),
            object_id=self.id_counter,
            payload_str=generate_random_string(20, 40),
            payload_double=random.random(),
            payload_timestamp=datetime.now(),
        )


class PackGenerator:
    def __init__(self, args, start_id=0):
        self._row_generator = RowGenerator(start_id)

        self._remain = args.initial_data_count
        self._pack_size = args.pack_size
        self._partitions_count = args.partitions_count

        self._packs = {}

    def get_next_pack(self):
        while self._remain:
            new_record = self._row_generator.get()
            shard_id = new_record.get_shard_id(self._partitions_count)

            self._remain -= 1

            if shard_id in self._packs:
                existing_pack = self._packs[shard_id]
                existing_pack.append(new_record)
                if len(existing_pack) >= self._pack_size:
                    return self._packs.pop(shard_id)
            else:
                self._packs[shard_id] = [new_record]

        for shard_id, pack in self._packs.items():
            if pack:
                return self._packs.pop(shard_id)
