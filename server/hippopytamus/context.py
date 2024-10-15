import pkgutil
import inspect
import os
import importlib
from hippopytamus.main import Servlet, TCPServer, HttpProtocol10


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
        # TODO dependency injection
        # TODO shouldn't be registered right now
        component = cls()
        self.components.append(component)

    def process_request(self, request: dict) -> dict:
        # TODO routing
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

    def inspect_module(self, module):
        return inspect.getmembers(module, inspect.isclass)

    def run(self):
        self.server.listen()

    def get_module_classes(self, package_name: str):
        # TODO not a package
        package = importlib.import_module(package_name)
        package_dir = os.path.dirname(package.__file__)

        all_classes = []

        for _, module_name, is_pkg in pkgutil.\
                walk_packages([package_dir], prefix=package_name + "."):
            try:
                # Dynamically import the module or package
                module = importlib.import_module(module_name)
                all_classes.extend(self.inspect_module(module))
            except ImportError as e:
                print(f"Failed to import module {module_name}: {e}")

        classes = [obj for name, obj in all_classes if
                   'Component' in get_class_decorators(obj)]
        return classes
