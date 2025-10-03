from abc import ABC, abstractmethod
from typing import Dict, Optional


class HippoExceptionHandler(ABC):
    @abstractmethod
    def get_type(self) -> Optional[str]:
        """Return a unique string identifying the exception
        type handled, or None if this is the default handler."""
        pass

    @abstractmethod
    def transform(self, exception: Exception) -> dict:
        """Prepares the response to be sent back."""
        pass


class HippoDefaultExceptionHandler(HippoExceptionHandler):
    def get_type(self) -> Optional[str]:
        return None

    def transform(self, exception: Exception) -> dict:
        return {
                'code': 500,
                'body': bytes(str(exception), "utf-8"),
                'headers': {
                    'Server': 'Hippopytamus',
                    'Content-Type': 'text/html'
                }
        }


class HippoExceptionManager:
    def __init__(self) -> None:
        self.defaultExceptionHandler: HippoExceptionHandler = HippoDefaultExceptionHandler()
        self.perTypeExceptionHandlers: Dict[str, HippoExceptionHandler] = {}
        # TODO: per controller handler map

    def register_exception_handler(self, handler: HippoExceptionHandler) -> None:
        if handler.get_type() is None:
            self.defaultExceptionHandler = handler
            return
        self.perTypeExceptionHandlers[handler.get_type()] = handler

    def get_exception_handler(self, name: str) -> HippoExceptionHandler:
        return self.perTypeExceptionHandlers.get(
                name,
                self.defaultExceptionHandler
        )

# TODO: conctruct handlers based on @ExceptionHandler annotations
# TODO: @ControllerAdvice
