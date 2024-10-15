import sys
import inspect
from main import Servlet, TCPServer, HttpProtocol10


def Component(cls):
    if not hasattr(cls, "__hippo_decorators"):
        cls.__hippo_decorators = []
    cls.__hippo_decorators.append("Component")
    return cls


def get_class_decorators(cls):
    if hasattr(cls, '__hippo_decorators'):
        return cls.__hippo_decorators
    return []


class HippoContainer(Servlet):
    components = []

    def register(self, cls: classmethod):
        component = cls()
        self.components.append(component)

    def process_request(self, request: dict) -> dict:
        return self.components[0].process_request(request)


class HippoApp:
    def __init__(self, module_name: str):
        classes = self.get_module_classes(module_name)
        print(classes)
        self.container = HippoContainer()
        for cls in classes:
            print(cls)
            self.container.register(cls)
        self.server = TCPServer(HttpProtocol10(), self.container)

    def get_module_classes(self, module_name: str):
        module = sys.modules[module_name]
        all_classes = self.inspect_module(module)
        classes = [obj for name, obj in all_classes if 'Component' in get_class_decorators(obj)]
        return classes

    def inspect_module(self, module):
        return inspect.getmembers(module, inspect.isclass)

    def run(self):
        self.server.listen()


@Component
class MyService:
    def __init__(self):
        print("Hello from service!")

    def process_request(self, request: dict) -> dict:
        return {
                "code": 200,
                "body": b"<html><head></head><body><h1>Hello from service!</h1></body></html>",
                "headers": {
                    "Server": "Hippopytamus",
                    "Content-Type": "text/html"
                }
        }


if __name__ == "__main__":
    app = HippoApp(__name__)
    app.run()
