from hippopytamus.core.annotation import Controller, GetMapping
from hippopytamus.core.annotation import ResponseStatus, ExceptionHandler
from hippopytamus.core.annotation import ControllerAdvice


@ResponseStatus(code=404)
class NotFoundException(Exception):
    pass


@ResponseStatus(code=404, reason="Test Not Found")
class NotFoundWithReasonException(Exception):
    pass


class LocalException(Exception):
    pass


class LocalException2(Exception):
    pass


class GlobalException(Exception):
    pass


@Controller
class MyService:
    @GetMapping("/exception")
    def exception_request(self) -> str:
        raise NotFoundException()

    @GetMapping("/exception2")
    def exception2_request(self) -> str:
        raise NotFoundWithReasonException()

    @GetMapping("/exception3")
    def exception3_request(self) -> str:
        raise LocalException()

    @GetMapping("/exception4")
    def exception4_request(self) -> str:
        raise LocalException2("Error 4")

    @GetMapping("/exception5")
    def exception5_request(self) -> str:
        raise GlobalException()

    @ResponseStatus(code=400)
    @ExceptionHandler(LocalException)
    def controller_handler(self) -> dict:
        pass

    @ExceptionHandler(LocalException2)
    def controller_handler2(self, exc: LocalException2) -> dict:
        return {
                "code": 404,
                "body": str(exc),
        }


@Controller
class AnotherService:
    @GetMapping("/another_exception")
    def exception_request(self) -> str:
        raise LocalException()


@ControllerAdvice
class MyServiceAdvice:
    @ResponseStatus(code=400, reason="From Advice")
    @ExceptionHandler(GlobalException)
    def controller_handler(self) -> dict:
        pass
