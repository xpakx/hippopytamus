from hippopytamus.core.annotation import Component, Controller, GetMapping
from hippopytamus.core.annotation import ExceptionHandler
from typing import Dict


# TODO: cycle detection
@Component
class A:
    # TODO: string type hints ????
    def __init__(self, b: "B"):
        self.b = b


@Component
class B:
    def __init__(self, a: A):
        self.a = a


@Controller
class MyService:
    def __init__(self, b: B):
        pass

    @ExceptionHandler(RecursionError)
    def handle_recursion(self, err: RecursionError) -> Dict:
        return {"code": 500, "body": b'Test error'}

    @GetMapping("/hello")
    def process_request(self) -> Dict:
        text = f"<html><head></head><body><h1>Hello from service!</h1></body></html>"
        return text
