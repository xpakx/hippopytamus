from hippopytamus.core.annotation import GetMapping, RequestBody, RequestParam
from hippopytamus.core.annotation import Controller
from typing import Dict, Tuple, Optional
import os


@Controller
class MyService:
    def __init__(self):
        print("Hello from service!")

    @GetMapping("/hello")
    def process_request(self, name: RequestParam(str, "name", defaultValue="world")) -> Dict:
        text = f"<html><head></head><body><h1>Hello {name} from service!</h1></body></html>"
        return text

    @GetMapping("/")
    def home(self, request: RequestBody(Dict)) -> Dict:
        body, err = self.body_from_file("index.html")
        if err:
            body, _ = self.body_from_file("404.html")
            return {"code": 404, "body": body}
        return body

    def body_from_file(self, url: str) -> Tuple[Optional[bytes], Optional[str]]:
        if os.path.exists(url):
            with open(url, 'rb') as f:
                body = f.read()
            return body, None
        return None, "No such file"
