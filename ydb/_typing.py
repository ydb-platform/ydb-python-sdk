"""
Common type definitions for YDB Python SDK.

This module contains type aliases, protocols, and type variables
used across the SDK for proper typing support.
"""

from typing import (
    Any,
    Callable,
    Iterable,
    Protocol,
    Tuple,
    TypeVar,
    Union,
    TYPE_CHECKING,
)

import grpc

if TYPE_CHECKING:
    from .driver import Driver as _SyncDriver
    from .aio.driver import Driver as _AsyncDriver


# =============================================================================
# Driver Type Variables
# =============================================================================

# TypeVar constrained to sync or async driver - use in Generic classes
# Example: class BaseQuerySession(Generic[DriverT]): ...
DriverT = TypeVar("DriverT", "_SyncDriver", "_AsyncDriver")

# Union type for functions that accept either driver
SupportedDriverType = Union["_SyncDriver", "_AsyncDriver"]


# =============================================================================
# gRPC Stream Types
# =============================================================================

# gRPC streaming calls return an object that is both grpc.Call (with cancel())
# and an Iterator. Since grpc doesn't export a public type for this combination,
# we define a type that matches the actual runtime behavior.
# See: grpc._channel._MultiThreadedRendezvous which inherits from grpc.Call, grpc.Future
_StreamItemT = TypeVar("_StreamItemT", covariant=True)


class GrpcStreamCall(grpc.Call, Iterable[_StreamItemT]):
    """Type for gRPC streaming call response.

    gRPC streaming calls return _MultiThreadedRendezvous which is both
    a grpc.Call (with cancel()) and an Iterator. This class provides
    proper typing by inheriting from both.

    Usage:
        _stream: Optional[GrpcStreamCall[SessionState]] = None
    """

    pass


# =============================================================================
# RPC Call Signatures
# =============================================================================

# Type for wrap_result callback
WrapResultFunc = Callable[..., Any]

# Type for RPC call arguments tuple
WrapArgsType = Tuple[Any, ...]


# =============================================================================
# Lock Protocol
# =============================================================================


class LockProtocol(Protocol):
    """Protocol for lock objects - supports both threading.Lock and fake locks."""

    def __enter__(self) -> Any:
        ...

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        ...
