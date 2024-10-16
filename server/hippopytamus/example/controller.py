from hippopytamus.context import Component, GetMapping


@Component
class MyService:
    def __init__(self):
        print("Hello from service!")

    @GetMapping("/hello")
    def process_request(self, request: dict) -> dict:
        return {
                "code": 200,
                "body": b"<html><head></head><body><h1>Hello from service!</h1></body></html>",
                "headers": {
                    "Server": "Hippopytamus",
                    "Content-Type": "text/html"
                }
        }
