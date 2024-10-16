import pkgutil
import inspect
import os
import importlib
from hippopytamus.main import Servlet, TCPServer, HttpProtocol10
from typing import get_type_hints
import functools


def Component(cls):
    if not hasattr(cls, "__hippo_decorators"):
        cls.__hippo_decorators = []
    cls.__hippo_decorators.append("Component")
    return cls


def get_class_decorators(cls):
    if hasattr(cls, '__hippo_decorators'):
        return cls.__hippo_decorators
    return []


def get_class_data(cls):
    print(f"Class name: {cls.__name__}")
    all_methods = inspect.getmembers(cls, predicate=lambda x: callable(x))
    methods = []
    for name, method in all_methods:
        if name != "__init__" and name.startswith('__'):
            continue
        print(f"Method name: {name}")

        sig = inspect.signature(method)
        print(f"Arguments: {sig}")

        type_hints = get_type_hints(method)
        print(f"Type hints: {type_hints}")

        decorators = []
        met = method
        while hasattr(met, "__wrapped__"):
            if hasattr(met, "__hippo_decorator"):
                decorators.append(met.__hippo_decorator)
            met = met.__wrapped__

        if decorators:
            print(f"Decorators: {decorators}")
            methods.append(method)  # TODO include metadata
        elif name == "__init__":
            methods.append(method)  # TODO include metadata
        else:
            print("No decorator detected")
    return methods


class HippoContainer(Servlet):
    components = []

    def register(self, cls: classmethod):
        # TODO dependency injection
        # TODO shouldn't be registered right now
        component = cls()
        methods = get_class_data(cls)

        self.components.append(component)

    def process_request(self, request: dict) -> dict:
        # TODO routing
        return self.components[0].process_request(request)


def GetMapping(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    wrapper.__hippo_decorator = "GetMapping"
    return wrapper


def PostMapping(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    wrapper.__hippo_decorator = "PostMapping"
    return wrapper


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
