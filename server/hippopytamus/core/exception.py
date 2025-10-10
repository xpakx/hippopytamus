from abc import ABC, abstractmethod
from typing import Dict, Optional, Any, cast, Type
from hippopytamus.core.extractor import (
        get_class_argdecorators, get_type_name
)
from hippopytamus.logger.logger import LoggerFactory
import inspect


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
        self.logger = LoggerFactory.get_logger()

    def register_exception_handler(self, handler: HippoExceptionHandler) -> None:
        handler_type = handler.get_type()
        if handler_type is None:
            self.defaultExceptionHandler = handler
            return
        self.perTypeExceptionHandlers[handler_type] = handler

    def get_exception_handler(self, name: str) -> HippoExceptionHandler:
        return self.perTypeExceptionHandlers.get(
                name,
                self.defaultExceptionHandler
        )

    def create_handler(self, annotation: Dict, method: Any, component: Any) -> None:
        self.logger.debug(f"Creating handler for {annotation}")
        exception_type = annotation.get('type', None)
        type_str = get_type_name(exception_type) if exception_type is not None else None

        self.logger.debug(f"Method to create handler {method}")
        method_handler = method.get('method_handle')
        if method_handler is None:
            return

        handler_sig = inspect.signature(method_handler)
        handler_params = handler_sig.parameters
        handler_param_count = len(handler_params)

        status_data = None
        status_code = None
        status_body = None
        for dec in method['decorators']:
            dec_name = dec.get('__decorator__')
            if dec_name == "ResponseStatus":
                status_data = dec
                break
        if status_data is not None:
            status_code = status_data.get('code', 500)
            status_body = bytes(status_data.get('reason', ''), "utf-8")

        class MethodHandler(HippoExceptionHandler):
            def __init__(self) -> None:
                self.component = None
                self.code = status_code
                self.body = status_body
                self.params = handler_param_count

            def get_type(self) -> Optional[str]:
                return type_str

            def transform(self, exception: Exception) -> Dict:
                transformed = None
                # TODO: improve that once potential params are determined
                if self.params == 1:
                    transformed = method_handler(self.component)
                else:
                    transformed = method_handler(self.component, exception)
                if transformed is None:
                    transformed = {}
                if self.code is not None:
                    transformed['code'] = self.code
                if self.body is not None:
                    transformed['body'] = self.body
                return cast(Dict, transformed)

            def get_component(self) -> Optional[str]:
                return cast(str, component.__name__)

            def set_component(self, comp: Any) -> None:
                self.component = comp
        self.register_exception_handler(MethodHandler())

    def register_exception(self, cls: Type[Exception]) -> None:
        exc_name = get_type_name(cls)
        class_decorators = get_class_argdecorators(cls)
        status_data = None
        for dec in class_decorators:
            dec_name = dec.get('__decorator__')
            if dec_name == "ResponseStatus":
                status_data = dec
                break
        if status_data is None:
            return
        self.logger.debug(exc_name)
        self.logger.debug(status_data)
        code = status_data.get('code', 500)
        body = bytes(status_data.get('reason', ''), "utf-8")

        class MethodHandler(HippoExceptionHandler):
            def __init__(self) -> None:
                self.component = None

            def get_type(self) -> Optional[str]:
                return exc_name

            def transform(self, exception: Exception) -> Dict:
                return {
                        "code": code,
                        "body": body,
                }

            def get_component(self) -> Optional[str]:
                return None

            def set_component(self, comp: Any) -> None:
                pass
        self.register_exception_handler(MethodHandler())

# TODO: @ControllerAdvice
