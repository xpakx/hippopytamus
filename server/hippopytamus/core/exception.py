from abc import ABC, abstractmethod


class HippoExceptionHandler(ABC):
    @abstractmethod
    def get_type(self) -> str:
        """Prepares the response to be sent back."""
        pass

    @abstractmethod
    def transform(self, exception: Exception) -> dict:
        """Prepares the response to be sent back."""
        pass


class HippoDefaultExceptionHandler(HippoExceptionHandler):
    def get_type(self) -> str:
        return ''

    def transform(self, exception: Exception) -> dict:
        return {
                'code': 500,
                'body': bytes(str(exception), "utf-8"),
                'headers': {
                    'Server': 'Hippopytamus',
                    'Content-Type': 'text/html'
                }
        }

# TODO: conctruct handlers based on @ExceptionHandler annotations
# TODO: @ControllerAdvice
