import inspect
import datetime
from typing import Type, Any, Union, Optional
from typing import Callable, Dict
import functools
from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class LogObject:
    timestamp: datetime.datetime = field(default_factory=datetime.datetime.now)
    log_level: str = "DEBUG"
    class_source: Optional[str] = None
    method_source: Optional[str] = None
    line_source: Optional[int] = None
    text: str = ""
    text_args: Dict = field(default_factory=dict)
    context: Dict = field(default_factory=dict)


class LogPrinter(ABC):
    @abstractmethod
    def print(self, obj: LogObject) -> None:
        """Prints log"""
        pass


def with_frame(fn: Callable) -> Callable:
    @functools.wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        self_param = args[0]
        if self_param.disabled:
            return
        frame = inspect.currentframe()
        if not frame:
            return
        frame = frame.f_back
        if not frame:
            return
        try:
            for_method = frame.f_code.co_name
            for_line = frame.f_lineno
            return fn(
                    *args,
                    for_method=for_method,
                    for_line=for_line,
                    **kwargs
            )
        finally:
            del frame
    return wrapper


def with_caller(fn: Callable) -> Callable:
    @functools.wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        sig = inspect.signature(fn)
        bound = sig.bind(*args, **kwargs)
        bound.apply_defaults()
        for_cls = bound.arguments['for_cls']
        self_name = bound.arguments['self_name']

        if for_cls:
            return fn(*args, **kwargs)
        else:
            frame = inspect.currentframe()
            if not frame:
                return
            frame = frame.f_back
            if not frame:
                return
            try:
                locals_ = frame.f_locals
                caller_self = locals_.get(self_name, None)
                caller_class = None
                if caller_self is not None:
                    caller_class = caller_self.__class__
                return fn(*args, for_cls=caller_class, **kwargs)
            finally:
                del frame
    return wrapper


class Logger:
    @with_caller
    def __init__(
        self,
        printer: LogPrinter,
        *,
        self_name: str = "self",
        for_cls: Optional[Union[Type, str]] = None,
        disabled: bool = False,
    ) -> None:
        if for_cls is not None:
            if isinstance(for_cls, str):
                self.caller = for_cls
            else:
                self.caller = f"{for_cls.__module__}.{for_cls.__name__}"
        else:
            self.caller = "<unknown>"
        self.disabled = disabled
        self.printer = printer

    def _log(
        self,
        level: str,
        text: str,
        args: Any,
        for_method: Optional[str],
        for_line: Optional[int],
        **context: Any
    ) -> None:
        logObj = LogObject(
                timestamp=datetime.datetime.now(),
                log_level=level,
                class_source=self.caller,
                method_source=for_method,
                line_source=for_line,
                text=text,
                text_args=args,
                context=context,
        )
        self.printer.print(logObj)

    @with_frame
    def log(
            self,
            text: str,
            *args: Any,
            for_method: Optional[str] = None,
            for_line: Optional[int] = None,
            **context: Any
    ) -> None:
        self._log("LOG", text, args, for_method, for_line, **context)

    @with_frame
    def debug(
            self,
            text: str,
            *args: Any,
            for_method: Optional[str] = None,
            for_line: Optional[int] = None,
            **context: Any
    ) -> None:
        self._log("DEBUG", text, args, for_method, for_line, **context)

    @with_frame
    def info(
            self,
            text: str,
            *args: Any,
            for_method: Optional[str] = None,
            for_line: Optional[int] = None,
            **context: Any
    ) -> None:
        self._log("INFO", text, args, for_method, for_line, **context)

    @with_frame
    def warn(
            self,
            text: str,
            *args: Any,
            for_method: Optional[str] = None,
            for_line: Optional[int] = None,
            **context: Any
    ) -> None:
        self._log("WARN", text, args, for_method, for_line, **context)

    @with_frame
    def error(
            self,
            text: str,
            *args: Any,
            for_method: Optional[str] = None,
            for_line: Optional[int] = None,
            **context: Any
    ) -> None:
        self._log("ERROR", text, args, for_method, for_line, **context)


class LoggerFactory:
    _loggers: dict[str, Logger] = {}
    _disabled: bool = False
    _printer: Optional[LogPrinter] = None

    @classmethod
    @with_caller
    def get_logger(
            cls,
            *,
            self_name: str = "self",
            for_cls: Optional[Union[Type, str]] = None
    ) -> Logger:
        caller_class = for_cls
        if caller_class is None:
            # TODO: unknown sources
            raise Exception("Couldn't determine caller class")
        name = ""
        if isinstance(caller_class, str):
            name = caller_class
        else:
            name = f"{caller_class.__module__}.{caller_class.__name__}"
        if name not in cls._loggers:
            cls._loggers[name] = Logger(
                    cls.get_printer(),
                    self_name=self_name,
                    for_cls=caller_class,
                    disabled=cls._disabled
            )
        return cls._loggers[name]

    @classmethod
    def disable_all(cls) -> None:
        cls._disabled = True
        for logger in cls._loggers.values():
            logger.disabled = True

    @classmethod
    def enable_all(cls) -> None:
        cls._disabled = False
        for logger in cls._loggers.values():
            logger.disabled = False

    @classmethod
    def disable_for(cls, class_type: Type[Any]) -> None:
        name = f"{class_type.__module__}.{class_type.__name__}"
        logger = cls._loggers.get(name)
        if logger:
            logger.disabled = True

    @classmethod
    def enable_for(cls, class_type: Type[Any]) -> None:
        name = f"{class_type.__module__}.{class_type.__name__}"
        logger = cls._loggers.get(name)
        if logger:
            logger.disabled = False

    @classmethod
    def get_printer(cls) -> LogPrinter:
        if cls._printer is None:
            cls._printer = BasicConsolePrinter()
        return cls._printer


# TODO: more args for print methods
class BasicConsolePrinter(LogPrinter):
    COLORS = {
        "LOG": "\033[94m",
        "INFO": "\033[92m",
        "WARN": "\033[93m",
        "ERROR": "\033[91m",
        "DEBUG": "\033[96m",
        "RESET": "\033[0m",
        "CLASS": "\033[95m",
        "METHOD": "\033[96m",
        "LINE": "\033[90m"
    }

    def _format_level(self, level: str) -> str:
        tag = f"[{level}]"
        pad = 7 - len(tag)
        tag += " " * pad
        return f"{self.COLORS[level]}{tag}{self.COLORS['RESET']}"

    def print(self, obj: LogObject) -> None:
        timestamp = obj.timestamp.strftime("%H:%M:%S")
        ctx_str = ""
        if obj.context is not None and len(obj.context) > 0:
            ctx_str = " (" + ", ".join(f"{k}={v!r}" for k, v in obj.context.items()) + ")"
        print(
            f"{self._format_level(obj.log_level)} "
            f"{timestamp} "
            f"{self.COLORS['CLASS']}{obj.class_source}{self.COLORS['RESET']}."
            f"{self.COLORS['METHOD']}{obj.method_source}{self.COLORS['RESET']}"
            f"{self.COLORS['LINE']}:{obj.line_source}{self.COLORS['RESET']} - "
            f"{obj.text}{ctx_str}"
        )
