from typing import List, Optional
from typing import Dict, Any, cast, Type
from typing import Protocol, Union, Annotated
from typing import Callable, _SpecialForm
from typing import TypeVar
import functools


T = TypeVar("T")


class HippoDecoratorClass(Protocol):
    __hippo_decorators: List[str]


def Component(cls: Type) -> HippoDecoratorClass:
    if not hasattr(cls, "__hippo_decorators"):
        cls.__hippo_decorators = []
    cls.__hippo_decorators.append("Component")
    return cast(HippoDecoratorClass, cls)


Controller = Component
Service = Component
Repository = Component


class HippoDecoratorFunc(Protocol):
    __hippo_decorator: Dict[str, Any]
    def __call__(self, *args: Any, **kwargs: Any) -> Any: ...


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
        def wrapper(*args, **kwargs):  # type: ignore
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
                   produces: strList = [], value: strList = []
                   ) -> Callable:
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
               value: strList = []) -> Callable:
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
                value: strList = []) -> Callable:
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


type HippoArgDecorator = Annotated[_SpecialForm, Any]


def RequestParam(cls: T, name: str = "", defaultValue: Any = None,
                 required: bool = False) -> HippoArgDecorator:
    metadata = {
            "__decorator__": "RequestParam",
            "name": name,
            "defaultValue": defaultValue,
            "required": required
    }
    return Annotated[cls, AnnotationMetadata(metadata)]


def RequestBody(cls: T, required: bool = False) -> HippoArgDecorator:
    metadata = {
            "__decorator__": "RequestBody",
            "required": required
    }
    return Annotated[cls, AnnotationMetadata(metadata)]


def PathVariable(cls: T, name: Optional[str] = None, required: bool = False) -> HippoArgDecorator:
    metadata = {
            "__decorator__": "PathVariable",
            "name": name,
            "required": required
    }
    return Annotated[cls, AnnotationMetadata(metadata)]
