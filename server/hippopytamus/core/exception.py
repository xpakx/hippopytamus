from abc import ABC, abstractmethod
from typing import Dict, Optional, Any


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

    @abstractmethod
    def get_component(self) -> Optional[str]:
        """Return component name if needed for construction"""
        pass

    @abstractmethod
    def set_component(self, component: Any) -> None:
        """Set constructed component"""
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

    def get_component(self) -> Optional[str]:
        return None

    def set_component(self, component: Any) -> None:
        pass


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

    def create_handler(self, annotation: Dict, method: Any, component: Any) -> None:
        print("Creating handler for", annotation)
        exception_type = annotation.get('type', None)
        type_str = exception_type.__name__ if exception_type is not None else None

        print("Method to create handler", method)
        method_handler = method.get('method_handle')
        if method_handler is None:
            return

        class MethodHandler(HippoExceptionHandler):
            def __init__(self):
                self.component = None

            def get_type(self):
                return type_str

            def transform(self, exception: Exception):
                return method_handler(self.component, exception)

            def get_component(self) -> Optional[str]:
                return component.__name__

            def set_component(self, comp: Any) -> None:
                self.component = comp
        self.register_exception_handler(MethodHandler())


# TODO: @ControllerAdvice
