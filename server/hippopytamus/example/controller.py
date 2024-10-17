from hippopytamus.context import Controller, GetMapping, RequestBody
from typing import Dict


@Controller
class MyService:
    def __init__(self):
        print("Hello from service!")

    @GetMapping("/hello")
    def process_request(self, request: RequestBody(Dict)) -> Dict:
        return {
                "code": 200,
                "body": b"<html><head></head><body><h1>Hello from service!</h1></body></html>",
                "headers": {
                    "Server": "Hippopytamus",
                    "Content-Type": "text/html"
                }
        }
