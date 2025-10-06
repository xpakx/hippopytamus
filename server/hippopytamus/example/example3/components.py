from hippopytamus.core.annotation import Controller, GetMapping
from hippopytamus.core.annotation import ResponseStatus


@Controller
class MyService:
    @GetMapping("/exception")
    def exception_request(self) -> str:
        raise NotFoundException()


@ResponseStatus(code=404)
class NotFoundException(Exception):
    pass
