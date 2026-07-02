"""Shared topic message payload codec used by the sync and async topic workloads.

The write timestamp travels inside the message so the reader (same process) can
compute end-to-end latency; writer_id + seqno let it validate per-producer
ordering and detect loss / duplicates.
"""


def encode_payload(writer_id: int, seqno: int, write_ts_ns: int, size: int) -> bytes:
    """`writer_id:seqno:write_ts_ns:` header, padded to `size` bytes."""
    header = f"{writer_id}:{seqno}:{write_ts_ns}:".encode("utf-8")
    if len(header) < size:
        header += b"x" * (size - len(header))
    return header


def decode_payload(data: bytes):
    """Return (writer_id, seqno, write_ts_ns) or None if not our payload."""
    try:
        parts = data.split(b":", 3)
        return int(parts[0]), int(parts[1]), int(parts[2])
    except (ValueError, IndexError):
        return None
