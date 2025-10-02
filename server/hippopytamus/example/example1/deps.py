from hippopytamus.core.annotation import (
    Controller, GetMapping, PathVariable,
    RequestMapping, RequestHeader, Component,
    Service, Value
)


@Component
class Config:
    def __init__(self, prefix: Value(str, '"Hello"')):
        self.prefix = prefix


@Service
class GreetingService:
    def __init__(self, config: Config):
        self.config = config

    def greet(self, name: str) -> str:
        return f"{self.config.prefix} {name}!"


@Controller
@RequestMapping("/api")
class UserController:
    def __init__(self, service: GreetingService):
        self.service = service

    @GetMapping("/test")
    def test(self) -> str:
        return "<h1>Dependency test</h1>"

    @GetMapping("/hello/{user_id}")
    def say_hello(
        self,
        user_id: PathVariable(int, "user_id"),
        request_id: RequestHeader(str, "X-Request-ID")
    ) -> dict:
        greeting = self.service.greet(f"User#{user_id}")
        return {
            "greeting": greeting,
            "request_id": request_id
        }
