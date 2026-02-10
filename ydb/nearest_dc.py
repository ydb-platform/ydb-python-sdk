# -*- coding: utf-8 -*-
import socket
import threading
import logging
import random
import time
from typing import Any, Dict, List, Optional

from . import resolver


logger = logging.getLogger(__name__)


def _check_fastest_endpoint(
    endpoints: List[resolver.EndpointInfo], timeout: float = 5.0
) -> Optional[resolver.EndpointInfo]:
    """
    Perform TCP race: connect to all endpoints simultaneously and return the fastest one.

    This function starts TCP connections to all provided endpoints in parallel
    and returns the first one that successfully connects. Other connection attempts
    will continue until their socket timeout expires (they cannot be interrupted).

    :param endpoints: List of resolver.EndpointInfo objects
    :param timeout: Maximum time to wait for any connection (seconds)
    :return: Fastest endpoint that connected successfully, or None if all failed
    """
    if not endpoints:
        return None

    result: Dict[str, Any] = {"endpoint": None, "lock": threading.Lock()}
    stop_event = threading.Event()
    deadline = time.monotonic() + timeout

    def try_connect(endpoint: resolver.EndpointInfo):
        """Try to connect to endpoint and report if successful."""
        remaining = deadline - time.monotonic()
        if remaining <= 0 or stop_event.is_set():
            return

        try:
            sock = socket.create_connection((endpoint.address, endpoint.port), timeout=remaining)

            try:
                with result["lock"]:
                    if result["endpoint"] is None:
                        result["endpoint"] = endpoint
                        stop_event.set()
                        logger.debug("TCP race winner: %s (location: %s)", endpoint.endpoint, endpoint.location)
            finally:
                sock.close()

        except (OSError, socket.timeout):
            # Ignore expected connection errors; endpoints that fail simply lose the TCP race.
            pass
        except Exception as e:
            logger.debug("Unexpected error connecting to %s: %s", endpoint.endpoint, e)

    threads: List[threading.Thread] = []
    for ep in endpoints:
        thread = threading.Thread(target=try_connect, args=(ep,), daemon=True)
        thread.start()
        threads.append(thread)

    stop_event.wait(timeout=max(0.0, deadline - time.monotonic()))

    return result["endpoint"]


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

    endpoints_copy = list(endpoints)
    random.shuffle(endpoints_copy)
    return endpoints_copy[:count]


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
    :param max_per_location: Maximum number of endpoints to test per location (default: 3)
    :param timeout: TCP connection timeout in seconds (default: 5.0)
    :return: Location string of the nearest datacenter, or None if detection failed
    :raises ValueError: If endpoints list is empty
    """
    if not endpoints:
        raise ValueError("Empty endpoints list for local DC detection")

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
