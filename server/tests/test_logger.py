import pytest
from typing import List
from hippopytamus.logger.logger import (
        LoggerFactory, LogPrinter, LogObject
)


class TestPrinter(LogPrinter):
    def post_init(self):
        self.logged: List[LogObject] = []

    def print(self, obj: LogObject) -> None:
        self.logged.append(obj)


class Dummy:
    def __init__(self, logger):
        self.logger = logger

    def action(self):
        self.logger.log("hello %s", "world")
        self.logger.debug("debug %d", 123)
        self.logger.info("info msg", extra="data")
        self.logger.warn("watch out!")
        self.logger.error("oops!", code=500)


class Dummy2:
    def __init__(self):
        self.logger = LoggerFactory.get_logger()

    def action(self):
        self.logger.debug("debug")


@pytest.fixture(autouse=True)
def test_printer():
    printer = TestPrinter()
    printer.post_init()
    LoggerFactory._printer = printer
    LoggerFactory._loggers.clear()
    LoggerFactory._disabled = False
    return printer


@pytest.fixture
def logger():
    return LoggerFactory.get_logger(for_cls=Dummy)


def test_logging_levels(test_printer, logger):
    obj = Dummy(logger)
    obj.action()

    logs = test_printer.logged
    assert len(logs) == 5

    assert logs[0].log_level == "LOG"
    assert logs[0].text == "hello %s"
    assert logs[0].text_args == ("world",)

    assert logs[1].log_level == "DEBUG"
    assert logs[1].text_args == (123,)

    assert logs[2].log_level == "INFO"
    assert logs[2].context["extra"] == "data"

    assert logs[4].log_level == "ERROR"
    assert logs[4].context["code"] == 500


def test_class_and_method_names(logger, test_printer):
    obj = Dummy(logger)
    obj.action()

    logs = test_printer.logged
    for log in logs:
        assert log.class_source.endswith("Dummy")
        assert log.method_source in ("action",)
        assert log.line_source is not None


def test_class_and_method_names_from_factory(test_printer):
    obj = Dummy2()
    obj.action()

    logs = test_printer.logged
    assert len(logs) == 1
    assert logs[0].class_source.endswith("Dummy2")
    assert logs[0].method_source in ("action",)
    assert logs[0].line_source is not None


def test_disable_enable_all(test_printer, logger):
    obj = Dummy(logger)

    LoggerFactory.disable_all()
    obj.action()
    assert len(test_printer.logged) == 0

    LoggerFactory.enable_all()
    obj.action()
    assert len(test_printer.logged) == 5


def test_disable_enable_for_class(test_printer, logger):
    obj = Dummy(logger)

    LoggerFactory.disable_for(Dummy)
    obj.action()
    assert len(test_printer.logged) == 0

    LoggerFactory.enable_for(Dummy)
    obj.action()
    assert len(test_printer.logged) == 5
