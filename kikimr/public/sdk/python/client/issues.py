# -*- coding: utf-8 -*-
from google.protobuf import text_format
import enum

from kikimr.public.api.protos import ydb_status_codes_pb2


_TRANSPORT_STATUSES_FIRST = 401000
_CLIENT_STATUSES_FIRST = 402000


@enum.unique
class StatusCode(enum.IntEnum):
    STATUS_CODE_UNSPECIFIED = ydb_status_codes_pb2.StatusIds.STATUS_CODE_UNSPECIFIED
    SUCCESS = ydb_status_codes_pb2.StatusIds.SUCCESS
    BAD_REQUEST = ydb_status_codes_pb2.StatusIds.BAD_REQUEST
    UNAUTHORIZED = ydb_status_codes_pb2.StatusIds.UNAUTHORIZED
    INTERNAL_ERROR = ydb_status_codes_pb2.StatusIds.INTERNAL_ERROR
    ABORTED = ydb_status_codes_pb2.StatusIds.ABORTED
    UNAVAILABLE = ydb_status_codes_pb2.StatusIds.UNAVAILABLE
    OVERLOADED = ydb_status_codes_pb2.StatusIds.OVERLOADED
    SCHEME_ERROR = ydb_status_codes_pb2.StatusIds.SCHEME_ERROR
    GENERIC_ERROR = ydb_status_codes_pb2.StatusIds.GENERIC_ERROR
    TIMEOUT = ydb_status_codes_pb2.StatusIds.TIMEOUT
    BAD_SESSION = ydb_status_codes_pb2.StatusIds.BAD_SESSION
    PRECONDITION_FAILED = ydb_status_codes_pb2.StatusIds.PRECONDITION_FAILED
    ALREADY_EXISTS = ydb_status_codes_pb2.StatusIds.ALREADY_EXISTS
    NOT_FOUND = ydb_status_codes_pb2.StatusIds.NOT_FOUND
    SESSION_EXPIRED = ydb_status_codes_pb2.StatusIds.SESSION_EXPIRED

    CONNECTION_LOST = _TRANSPORT_STATUSES_FIRST + 10
    CONNECTION_FAILURE = _TRANSPORT_STATUSES_FIRST + 20
    DEADLINE_EXCEEDED = _TRANSPORT_STATUSES_FIRST + 30
    CLIENT_INTERNAL_ERROR = _TRANSPORT_STATUSES_FIRST + 40
    UNIMPLEMENTED = _TRANSPORT_STATUSES_FIRST + 50

    UNAUTHENTICATED = _CLIENT_STATUSES_FIRST + 30


class Error(Exception):
    status = None

    def __init__(self, message, issues=None):
        super(Error, self).__init__(message)
        self.issues = issues
        self.message = message


class ConnectionError(Error):
    status = None


class ConnectionFailure(ConnectionError):
    status = StatusCode.CONNECTION_FAILURE


class ConnectionLost(ConnectionError):
    status = StatusCode.CONNECTION_LOST


class DeadlineExceed(ConnectionError):
    status = StatusCode.DEADLINE_EXCEEDED


class Unimplemented(ConnectionError):
    status = StatusCode.UNIMPLEMENTED


class Unauthenticated(Error):
    status = StatusCode.UNAUTHENTICATED


class BadRequest(Error):
    status = StatusCode.BAD_REQUEST


class Unauthorized(Error):
    status = StatusCode.UNAUTHORIZED


class InternalError(Error):
    status = StatusCode.INTERNAL_ERROR


class Aborted(Error):
    status = StatusCode.ABORTED


class Unavailable(Error):
    status = StatusCode.UNAVAILABLE


class Overloaded(Error):
    status = StatusCode.OVERLOADED


class SchemeError(Error):
    status = StatusCode.SCHEME_ERROR


class GenericError(Error):
    status = StatusCode.GENERIC_ERROR


class BadSession(Error):
    status = StatusCode.BAD_SESSION


class Timeout(Error):
    status = StatusCode.TIMEOUT


class PreconditionFailed(Error):
    status = StatusCode.PRECONDITION_FAILED


class NotFound(Error):
    status = StatusCode.NOT_FOUND


class AlreadyExists(Error):
    status = StatusCode.ALREADY_EXISTS


class SessionExpired(Error):
    status = StatusCode.SESSION_EXPIRED


def _format_issues(issues):
    if not issues:
        return ""
    return " ,".join(
        [text_format.MessageToString(issue, False, True) for issue in issues]
    )


_success_status_codes = {StatusCode.STATUS_CODE_UNSPECIFIED, StatusCode.SUCCESS}
_server_side_error_map = {
    StatusCode.BAD_REQUEST: BadRequest,
    StatusCode.UNAUTHORIZED: Unauthorized,
    StatusCode.INTERNAL_ERROR: InternalError,
    StatusCode.ABORTED: Aborted,
    StatusCode.UNAVAILABLE: Unavailable,
    StatusCode.OVERLOADED: Overloaded,
    StatusCode.SCHEME_ERROR: SchemeError,
    StatusCode.GENERIC_ERROR: GenericError,
    StatusCode.TIMEOUT: Timeout,
    StatusCode.BAD_SESSION: BadSession,
    StatusCode.PRECONDITION_FAILED: PreconditionFailed,
    StatusCode.ALREADY_EXISTS: AlreadyExists,
    StatusCode.NOT_FOUND: NotFound,
    StatusCode.SESSION_EXPIRED: SessionExpired,
}


def _process_response(response_proto):
    if response_proto.status not in _success_status_codes:
        exc_obj = _server_side_error_map.get(response_proto.status)
        raise exc_obj(
            _format_issues(response_proto.issues),
            response_proto.issues
        )
