
class Warning(Exception):
    pass


class Error(Exception):
    def __init__(self, message, issues=None, status=None):
        super(Error, self).__init__(message)
        self.issues = issues
        self.message = message
        self.status = status


class InterfaceError(Error):
    pass


class DatabaseError(Error):
    pass


class DataError(DatabaseError):
    pass


class OperationalError(DatabaseError):
    pass


class IntegrityError(DatabaseError):
    pass


class InternalError(DatabaseError):
    pass


class ProgrammingError(DatabaseError):
    pass


class NotSupportedError(DatabaseError):
    pass
