import pkgutil
import inspect
import os
import importlib
from hippopytamus.protocol.interface import Servlet, Response, Request
from hippopytamus.server.nonblocking import SelectTCPServer
from hippopytamus.protocol.http import HttpProtocol10
from typing import get_type_hints, Union, List
from typing import Dict, Any, cast, Type, TypeVar
from typing import Annotated, get_origin, get_args
from typing import Protocol, Callable, Optional
from types import ModuleType
from inspect import Signature, Parameter
import functools

T = TypeVar("T")


def Component(cls: Type) -> Type:
    if not hasattr(cls, "__hippo_decorators"):
        cls.__hippo_decorators = []
    cls.__hippo_decorators.append("Component")
    return cls


Controller = Component
Service = Component
Repository = Component


class HippoDecoratorFunc(Protocol):
    __hippo_decorator: Dict[str, Any]
    def __call__(self, *args: Any, **kwargs: Any) -> Any: ...


def get_class_decorators(cls):
    if hasattr(cls, '__hippo_decorators'):
        return cls.__hippo_decorators
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


strList = Union[List[str], str]


def getListForStrList(arg: strList) -> List[str]:
    return arg if isinstance(arg, list) else [arg]


def get_request_wrapper(path: strList = [], consumes: strList = [],
                        headers: strList = [], method: strList = [],
                        name: str = "", params: strList = [],
                        produces: strList = [], value: strList = []
                        ) -> Callable[[Callable], HippoDecoratorFunc]:
    def decorator(func: Callable) -> HippoDecoratorFunc:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        hippo_wrapper = cast(HippoDecoratorFunc, wrapper)
        hippo_wrapper.__hippo_decorator = {
                "__decorator__": "RequestMapping",
                "path": getListForStrList(path),
                "name": name,
                "consumes": getListForStrList(consumes),
                "headers": getListForStrList(headers),
                "method": getListForStrList(method),
                "params": getListForStrList(params),
                "produces": getListForStrList(produces),
                "value": getListForStrList(value),
            }
        return hippo_wrapper
    return decorator


def RequestMapping(path: strList = [], consumes: strList = [],
                   headers: strList = [], method: strList = [],
                   name: str = "", params: strList = [],
                   produces: strList = [], value: strList = []):
    # trick to let use decorator with or without parentheses
    if callable(path):
        # used without parentheses, called by system,
        # path is actually a function
        func = path
        wrapper = get_request_wrapper()
        return wrapper(func)

    else:
        # used directly by user with arguments
        return get_request_wrapper(path, consumes, headers, method,
                                   name, params, produces, value)


def GetMapping(path: strList = [], consumes: strList = [],
               headers: strList = [], name: str = "",
               params: strList = [], produces: strList = [],
               value: strList = []):
    if callable(path):
        func = path
        wrapper = get_request_wrapper(method="GET")
        return wrapper(func)
    else:
        return get_request_wrapper(path, consumes, headers, "GET",
                                   name, params, produces, value)


def PostMapping(path: strList = [], consumes: strList = [],
                headers: strList = [], name: str = "",
                params: strList = [], produces: strList = [],
                value: strList = []):
    if callable(path):
        func = path
        wrapper = get_request_wrapper(method="POST")
        return wrapper(func)
    else:
        return get_request_wrapper(path, consumes, headers, "POST",
                                   name, params, produces, value)


class AnnotationMetadata:
    def __init__(self, metadata: Dict) -> None:
        self.metadata = metadata


def RequestParam(cls: T, name: str = "", defaultValue: Any = None,
                 required: bool = False):
    metadata = {
            "__decorator__": "RequestParam",
            "name": name,
            "defaultValue": defaultValue,
            "required": required
    }
    return Annotated[cls, AnnotationMetadata(metadata)]


def RequestBody(cls: T, required: bool = False):
    metadata = {
            "__decorator__": "RequestBody",
            "required": required
    }
    return Annotated[cls, AnnotationMetadata(metadata)]


def PathVariable(cls: T, name: str = "", required: bool = False):
    metadata = {
            "__decorator__": "PathVariable",
            "name": name,
            "required": required
    }
    return Annotated[cls, AnnotationMetadata(metadata)]


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
