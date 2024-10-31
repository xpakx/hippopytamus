from hippopytamus.core.annotation import GetMapping, RequestBody
from hippopytamus.core.annotation import Controller
from typing import Dict, Tuple, Optional
import os


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

    @GetMapping("/")
    def home(self, request: RequestBody(Dict)) -> Dict:
        body, err = self.body_from_file("index.html")
        if err:
            body, _ = self.body_from_file("404.html")
            return {"code": 404, "body": body}
        return {
                "code": 200,
                "body": body,
                "headers": {
                    "Server": "Hippopytamus",
                    "Content-Type": "text/html"
                }
        }

    def body_from_file(self, url: str) -> Tuple[Optional[bytes], Optional[str]]:
        if os.path.exists(url):
            with open(url, 'rb') as f:
                body = f.read()
            return body, None
        return None, "No such file"
