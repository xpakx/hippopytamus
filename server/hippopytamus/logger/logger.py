import inspect
import datetime
from typing import Type, Any
import functools


def with_frame(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        frame = inspect.currentframe().f_back
        try:
            return fn(*args, frame=frame, **kwargs)
        finally:
            del frame
    return wrapper


def with_caller(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        sig = inspect.signature(fn)
        bound = sig.bind(*args, **kwargs)
        bound.apply_defaults()
        for_cls = bound.arguments['for_cls']
        self_name = bound.arguments['self_name']

        if for_cls:
            return fn(*args, **kwargs)
        else:
            frame = inspect.currentframe().f_back
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

    @with_caller
    def __init__(
        self,
        *,
        self_name: str = "self",
        for_cls: type = None,
        disabled: bool = False
    ) -> None:
        if for_cls:
            self.caller = f"{for_cls.__module__}.{for_cls.__name__}"
        else:
            self.caller = "<unknown>"
        self.disabled = disabled

    def _format_level(self, level: str) -> str:
        tag = f"[{level}]"
        pad = 7 - len(tag)
        tag += " " * pad
        return f"{self.COLORS[level]}{tag}{self.COLORS['RESET']}"

    def _log(self, level: str, text: str, frame) -> None:
        caller_method = frame.f_code.co_name
        lineno = frame.f_lineno
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        print(
            f"{self._format_level(level)} "
            f"{timestamp} "
            f"{self.COLORS['CLASS']}{self.caller}{self.COLORS['RESET']}."
            f"{self.COLORS['METHOD']}{caller_method}{self.COLORS['RESET']}"
            f"{self.COLORS['LINE']}:{lineno}{self.COLORS['RESET']} - {text}"
        )

    @with_frame
    def log(self, text: str, frame=None) -> None:
        if self.disabled:
            return
        self._log("LOG", text, frame)

    @with_frame
    def debug(self, text: str, frame=None):
        if self.disabled:
            return
        self._log("DEBUG", text, frame)

    @with_frame
    def info(self, text: str, frame=None):
        if self.disabled:
            return
        self._log("INFO", text, frame)

    @with_frame
    def warn(self, text: str, frame=None):
        if self.disabled:
            return
        self._log("WARN", text, frame)

    @with_frame
    def error(self, text: str, frame=None):
        if self.disabled:
            return
        self._log("ERROR", text, frame)


class LoggerFactory:
    _loggers: dict[str, Logger] = {}
    _disabled: bool = False

    @classmethod
    @with_caller
    def get_logger(cls, *, self_name: str = "self", for_cls: type = None) -> Logger:
        caller_class = for_cls
        if caller_class is None:
            # TODO: unknown sources
            raise Exception("Couldn't determine caller class")
        name = f"{caller_class.__module__}.{caller_class.__name__}"
        if name not in cls._loggers:
            cls._loggers[name] = Logger(
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
