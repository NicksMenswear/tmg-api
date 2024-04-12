class ServiceError(Exception):
    def __init__(self, message, original_exception=None):
        super().__init__(message)

        self.message = message
        self.original_exception = original_exception


class NotFoundError(ServiceError):
    MESSAGE = "Not found"

    def __init__(self, message=MESSAGE, original_exception=None):
        super().__init__(message, original_exception)


class DuplicateError(ServiceError):
    MESSAGE = "Duplicate entry"

    def __init__(self, message=MESSAGE, original_exception=None):
        super().__init__(message, original_exception)
