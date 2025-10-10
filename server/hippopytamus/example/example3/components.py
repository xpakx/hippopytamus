from hippopytamus.core.annotation import Controller, GetMapping
from hippopytamus.core.annotation import ResponseStatus


@Controller
class MyService:
    @GetMapping("/exception")
    def exception_request(self) -> str:
        raise NotFoundException()

    @GetMapping("/exception2")
    def exception2_request(self) -> str:
        raise NotFoundWithReasonException()


@ResponseStatus(code=404)
class NotFoundException(Exception):
    pass


@ResponseStatus(code=404, reason="Test Not Found")
class NotFoundWithReasonException(Exception):
    pass
