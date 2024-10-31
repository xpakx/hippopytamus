import pkgutil
import inspect
import os
import importlib
from hippopytamus.protocol.interface import Servlet, Response, Request
from hippopytamus.server.nonblocking import SelectTCPServer
from hippopytamus.protocol.http import HttpProtocol10
from typing import get_type_hints, List
from typing import Dict, Any, cast, Type
from typing import Annotated, get_origin, get_args
from typing import Optional
from types import ModuleType
from inspect import Signature, Parameter
from hippopytamus.core.annotation import HippoDecoratorClass
from hippopytamus.core.annotation import AnnotationMetadata


def get_class_decorators(cls: Type) -> List[str]:
    hippo_cls = cast(HippoDecoratorClass, cls)
    if hasattr(hippo_cls, '__hippo_decorators'):
        return hippo_cls.__hippo_decorators
    return []


def extract_underlying_type(name: str, param: Parameter) -> Optional[Dict[str, Any]]:
    cls = param.annotation
    if cls is inspect._empty:
        return None

    annotations = []
    while get_origin(cls) is Annotated:
        args = get_args(cls)
        cls = args[0]
        if isinstance(args[1], AnnotationMetadata):
            annotations.append(args[1].metadata)
    return {"name": name, "class": cls, "annotations": annotations}


def get_class_data(cls: Type) -> List[Any]:
    print(cls)
    print(f"Class name: {cls.__name__}")
    print(f"class decorators: {get_class_decorators(cls)}")
    all_methods = inspect.getmembers(cls, predicate=lambda x: callable(x))
    methods: List[Any] = []
    for name, method in all_methods:
        if name != "__init__" and name.startswith('__'):
            continue
        current_method: Dict[str, Any] = {}
        current_method['name'] = name
        current_method['method_handle'] = method

        sig: Signature = inspect.signature(method)
        signature = []
        for key, value in sig.parameters.items():
            if key == "self":
                continue
            extracted_signature = extract_underlying_type(key, value)
            signature.append(extracted_signature)
        current_method['signature'] = signature

        type_hints = get_type_hints(method)
        current_method['arguments'] = type_hints

        decorators = []
        met = method
        while hasattr(met, "__wrapped__"):
            if hasattr(met, "__hippo_decorator"):
                decorators.append(met.__hippo_decorator)
            met = met.__wrapped__

        if decorators:
            current_method['decorators'] = decorators
            methods.append(current_method)
        elif name == "__init__":
            current_method['decorators'] = []
            methods.append(current_method)
    print(methods)
    return methods


class HippoContainer(Servlet):
    components: List[Any] = []
    routes: Dict[str, Any] = {}

    def register(self, cls: Type) -> None:
        # TODO dependency injection
        # TODO shouldn't be created right now
        component = cls()
        metadata = get_class_data(cls)
        for method in metadata:
            for annotation in method['decorators']:
                if annotation['__decorator__'] == "RequestMapping":
                    # TODO http methods
                    # TODO append class-defined path
                    for path in annotation['path']:
                        self.routes[path] = {
                                "component": component,
                                "method": method['method_handle']
                        }

        self.components.append(component)

    def process_request(self, request: Request) -> Response:
        if not isinstance(request, dict):
            raise Exception("Error")
        # TODO path variables
        # TODO tree-based routing
        # TODO transforming body, path variables, query params
        # TODO transforming response
        uri = request['uri']
        if uri not in self.routes:
            return {
                    "code": 404,
                    "body": b"<html><head></head><body><h1>Nof found</h1></body></html>",
                    "headers": {
                        "Server": "Hippopytamus",
                        "Content-Type": "text/html"
                    }
            }
        route = self.routes[uri]
        if route:
            return cast(Dict, route['method'](route['component'], request))
        return {}


class HippoApp:
    def __init__(self, module_name: str) -> None:
        classes = self.get_module_classes(module_name)
        print(classes)
        self.container = HippoContainer()
        for cls in classes:
            self.container.register(cls)
        self.server = SelectTCPServer(HttpProtocol10(), self.container)

    def inspect_module(self, module: ModuleType) -> Any:
        return inspect.getmembers(module, inspect.isclass)

    def run(self) -> None:
        self.server.listen()

    def get_module_classes(self, package_name: str) -> List[Any]:
        # TODO not a package
        package = importlib.import_module(package_name)
        if not package or not package.__file__:
            raise Exception("Error")
        package_dir = os.path.dirname(package.__file__)
        if not package_dir:
            raise Exception("Error")

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
