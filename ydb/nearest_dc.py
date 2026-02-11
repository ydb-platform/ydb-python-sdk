# -*- coding: utf-8 -*-
import atexit
import concurrent.futures
import socket
import sys
import threading
import logging
import random
import time
from typing import Dict, List, Optional

from . import resolver


logger = logging.getLogger(__name__)

# Module-level thread pool for TCP race (reused across discovery cycles)
_TCP_RACE_MAX_WORKERS = 30
_TCP_RACE_EXECUTOR: Optional[concurrent.futures.ThreadPoolExecutor] = None
_EXECUTOR_LOCK = threading.Lock()
_ATEXIT_REGISTERED = False


def _get_executor() -> concurrent.futures.ThreadPoolExecutor:
    """
    Lazily create and return the thread pool executor.

    The executor is created on first use to avoid import-time side effects.
    The atexit hook is registered only when the executor is actually created.
    """
    global _TCP_RACE_EXECUTOR, _ATEXIT_REGISTERED

    if _TCP_RACE_EXECUTOR is None:
        with _EXECUTOR_LOCK:
            if _TCP_RACE_EXECUTOR is None:
                _TCP_RACE_EXECUTOR = concurrent.futures.ThreadPoolExecutor(
                    max_workers=_TCP_RACE_MAX_WORKERS,
                    thread_name_prefix="ydb-tcp-race",
                )

                if not _ATEXIT_REGISTERED:
                    atexit.register(_shutdown_executor)
                    _ATEXIT_REGISTERED = True

    return _TCP_RACE_EXECUTOR


def _shutdown_executor():
    """Shutdown the executor if it was created."""
    if _TCP_RACE_EXECUTOR is not None:
        if sys.version_info >= (3, 9):
            _TCP_RACE_EXECUTOR.shutdown(wait=False, cancel_futures=True)
        else:
            _TCP_RACE_EXECUTOR.shutdown(wait=False)


def _check_fastest_endpoint(
    endpoints: List[resolver.EndpointInfo], timeout: float = 5.0
) -> Optional[resolver.EndpointInfo]:
    """
    Perform TCP race using a bounded thread pool and return the fastest endpoint.

    Uses a module-level ThreadPoolExecutor to avoid creating new threads on every
    discovery cycle. Returns immediately when the first endpoint connects successfully.

    If there are more endpoints than the thread pool size, takes one random endpoint
    per location to ensure fair representation of all locations in the race. If there
    are still too many locations, randomly samples them to stay within the limit.

    :param endpoints: List of resolver.EndpointInfo objects
    :param timeout: Maximum time to wait for any connection (seconds)
    :return: Fastest endpoint that connected successfully, or None if all failed
    """
    if not endpoints:
        return None

    if len(endpoints) > _TCP_RACE_MAX_WORKERS:
        endpoints_by_location = _split_endpoints_by_location(endpoints)
        endpoints = [random.choice(location_eps) for location_eps in endpoints_by_location.values()]

        if len(endpoints) > _TCP_RACE_MAX_WORKERS:
            endpoints = random.sample(endpoints, _TCP_RACE_MAX_WORKERS)

    stop_event = threading.Event()
    winner_lock = threading.Lock()
    deadline = time.monotonic() + timeout

    def try_connect(endpoint: resolver.EndpointInfo) -> Optional[resolver.EndpointInfo]:
        """Try to connect to endpoint and return it if successful."""
        remaining = deadline - time.monotonic()
        if remaining <= 0 or stop_event.is_set():
            return None

        if endpoint.ipv6_addrs:
            target_host = endpoint.ipv6_addrs[0]
        elif endpoint.ipv4_addrs:
            target_host = endpoint.ipv4_addrs[0]
        else:
            target_host = endpoint.address

        try:
            sock = socket.create_connection((target_host, endpoint.port), timeout=remaining)
            try:
                with winner_lock:
                    if stop_event.is_set():
                        return None
                    stop_event.set()
                    return endpoint
            finally:
                sock.close()
        except (OSError, socket.timeout):
            # Ignore expected connection errors; endpoints that fail simply lose the TCP race.
            return None
        except Exception as e:
            logger.debug("Unexpected error connecting to %s: %s", endpoint.endpoint, e)
            return None

    executor = _get_executor()
    futures: List[concurrent.futures.Future] = [executor.submit(try_connect, ep) for ep in endpoints]

    try:
        for fut in concurrent.futures.as_completed(futures, timeout=timeout):
            result = fut.result()
            if result is not None:
                return result
    except concurrent.futures.TimeoutError:
        # Overall timeout expired
        pass
    finally:
        for f in futures:
            f.cancel()

    return None


def _split_endpoints_by_location(endpoints: List[resolver.EndpointInfo]) -> Dict[str, List[resolver.EndpointInfo]]:
    """
    Group endpoints by their location.

    :param endpoints: List of resolver.EndpointInfo objects
    :return: Dictionary mapping location -> list of resolver.EndpointInfo
    """
    result: Dict[str, List[resolver.EndpointInfo]] = {}
    for endpoint in endpoints:
        location = endpoint.location
        if location not in result:
            result[location] = []
        result[location].append(endpoint)
    return result


def _get_random_endpoints(endpoints: List[resolver.EndpointInfo], count: int) -> List[resolver.EndpointInfo]:
    """
    Get random sample of endpoints.

    :param endpoints: List of resolver.EndpointInfo objects
    :param count: Maximum number of endpoints to return
    :return: Random sample of resolver.EndpointInfo
    """
    if len(endpoints) <= count:
        return endpoints
    return random.sample(endpoints, count)


def detect_local_dc(
    endpoints: List[resolver.EndpointInfo], max_per_location: int = 3, timeout: float = 5.0
) -> Optional[str]:
    """
    Detect nearest datacenter by performing TCP race between endpoints.

    This function groups endpoints by location, selects random samples from each location,
    and performs parallel TCP connections to find the fastest one. The location of the
    fastest endpoint is considered the nearest datacenter.

    Algorithm:
    1. Group endpoints by location
    2. If only one location exists, return it immediately
    3. Select up to max_per_location random endpoints from each location
    4. Perform TCP race: connect to all selected endpoints simultaneously
    5. Return the location of the first endpoint that connects successfully
    6. If all connections fail, return None

    :param endpoints: List of resolver.EndpointInfo objects from discovery
    :param max_per_location: Maximum number of endpoints to test per location (default: 3, must be >= 1)
    :param timeout: TCP connection timeout in seconds (default: 5.0, must be > 0)
    :return: Location string of the nearest datacenter, or None if detection failed
    :raises ValueError: If endpoints list is empty, max_per_location < 1, or timeout <= 0
    """
    if not endpoints:
        raise ValueError("Empty endpoints list for local DC detection")
    if max_per_location < 1:
        raise ValueError(f"max_per_location must be >= 1, got {max_per_location}")
    if timeout <= 0:
        raise ValueError(f"timeout must be > 0, got {timeout}")

    endpoints_by_location = _split_endpoints_by_location(endpoints)

    logger.debug(
        "Detecting local DC from %d endpoints across %d locations",
        len(endpoints),
        len(endpoints_by_location),
    )

    if len(endpoints_by_location) == 1:
        location = list(endpoints_by_location.keys())[0]
        logger.debug("Only one location found: %s", location)
        return location

    endpoints_to_test = []
    for location, location_endpoints in endpoints_by_location.items():
        sample = _get_random_endpoints(location_endpoints, max_per_location)
        endpoints_to_test.extend(sample)
        logger.debug(
            "Selected %d/%d endpoints from location '%s' for testing",
            len(sample),
            len(location_endpoints),
            location,
        )

    fastest_endpoint = _check_fastest_endpoint(endpoints_to_test, timeout=timeout)

    if fastest_endpoint is None:
        logger.debug("Failed to detect local DC via TCP race: no endpoint connected in time")
        return None

    detected_location = fastest_endpoint.location
    logger.debug("Detected local DC: %s", detected_location)

    return detected_location
