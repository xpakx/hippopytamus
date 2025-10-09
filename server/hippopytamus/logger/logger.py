import inspect
import datetime
from typing import Type, Any, Union, Optional
from typing import Callable, Dict, TextIO, Self
import functools
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import sys


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
    _factory: Optional["LoggerFactory"] = None

    def __init__(self) -> None:
        self.loggers: dict[str, Logger] = {}
        self.disabled: bool = False
        self.printer: Optional[LogPrinter] = None
        self.whitelist: set[str] = set()
        self.blacklist: set[str] = set()

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
        factory = cls.get_factory()
        disabled = factory.disabled
        if name in factory.blacklist:
            disabled = True
        if name in factory.whitelist:
            disabled = False
        if name not in factory.loggers:
            factory.loggers[name] = Logger(
                    factory._get_printer(),
                    self_name=self_name,
                    for_cls=caller_class,
                    disabled=disabled
            )
        return factory.loggers[name]

    @classmethod
    def get_factory(cls) -> "LoggerFactory":
        if cls._factory:
            return cls._factory
        factory = LoggerFactory()
        cls._factory = factory
        return factory

    def disable_all(self) -> None:
        self.disabled = True
        for logger in self.loggers.values():
            logger.disabled = True

    def enable_all(self) -> None:
        self.disabled = False
        for logger in self.loggers.values():
            logger.disabled = False

    def disable_for(self, class_type: Type[Any]) -> None:
        name = f"{class_type.__module__}.{class_type.__name__}"
        logger = self.loggers.get(name)
        if logger:
            logger.disabled = True
        self.blacklist.add(name)
        if name in self.whitelist:
            self.whitelist.remove(name)

    def enable_for(self, class_type: Type[Any]) -> None:
        name = f"{class_type.__module__}.{class_type.__name__}"
        logger = self.loggers.get(name)
        if logger:
            logger.disabled = False
        self.whitelist.add(name)
        if name in self.blacklist:
            self.blacklist.remove(name)

    def _get_printer(self) -> LogPrinter:
        if self.printer is None:
            self.printer = BasicConsolePrinter()
        return self.printer

    def get_printer(self) -> LogPrinter | None:
        return self.printer

    def set_printer(self, printer: LogPrinter) -> None:
        self.printer = printer


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

    def __init__(self, stream: TextIO = sys.stdout) -> None:
        self.stream = stream
        self.enable_colors = stream.isatty()

    def _format_level(self, level: str) -> str:
        tag = f"[{level}]"
        pad = 7 - len(tag)
        tag += " " * pad
        if self.enable_colors:
            return f"{self.COLORS[level]}{tag}{self.COLORS['RESET']}"
        else:
            return tag

    def _format_class(self, class_name: str | None) -> str:
        if class_name is None:
            class_name = "<unknown>"
        if not self.enable_colors:
            return class_name
        return f"{self.COLORS['CLASS']}{class_name}{self.COLORS['RESET']}"

    def _format_method(self, method_name: str | None) -> str:
        if method_name is None:
            method_name = "<unknown>"
        if not self.enable_colors:
            return method_name
        return f"{self.COLORS['METHOD']}{method_name}{self.COLORS['RESET']}"

    def _format_line(self, lineno: int | None) -> str:
        if lineno is None:
            return ""
        if not self.enable_colors:
            return f":{lineno}"
        return f"{self.COLORS['LINE']}:{lineno}{self.COLORS['RESET']}"

    def print(self, obj: LogObject) -> None:
        timestamp = obj.timestamp.strftime("%H:%M:%S")
        ctx_str = ""
        if obj.context is not None and len(obj.context) > 0:
            ctx_str = " (" + ", ".join(f"{k}={v!r}" for k, v in obj.context.items()) + ")"

        level = self._format_level(obj.log_level)
        cls = self._format_class(obj.class_source)
        method = self._format_method(obj.method_source)
        line = self._format_line(obj.line_source)

        print(
            f"{level} {timestamp} {cls}.{method}{line} - {obj.text}{ctx_str}",
            file=self.stream
        )
