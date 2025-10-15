from typing import List, Optional
from typing import Dict, Any, cast, Type
from typing import Protocol, Union, Annotated
from typing import Callable, _SpecialForm
from typing import TypeVar
import inspect
import functools
from hippopytamus.core.filter import HippoFilter


T = TypeVar("T")


class HippoDecoratorClass(Protocol):
    __hippo_decorators: List[str]
    __hippo_argdecorators: List[Dict[str, Any]]


def hippo_ensure_meta_lists(cls: Type) -> None:
    if not hasattr(cls, "__hippo_decorators"):
        cls.__hippo_decorators = []
    if not hasattr(cls, "__hippo_argdecorators"):
        cls.__hippo_argdecorators = []


def Component(cls: Type) -> HippoDecoratorClass:
    hippo_ensure_meta_lists(cls)
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


def get_wrapper_for_annotation(
        name: str,
        applicable_to_class: bool,
        applicable_to_method: bool,
        decorators: List[str],
        argdecorator: Dict[str, Any] | None = None,
        req_sublass: Type | None = None
) -> Callable[[Callable], Union[HippoDecoratorFunc, HippoDecoratorClass]]:
    def decorator(func: Callable) -> Union[HippoDecoratorFunc, HippoDecoratorClass]:
        if inspect.isclass(func):
            if not applicable_to_class:
                raise Exception(f"@{name} cannot be applied to class")
            if req_sublass is not None and not issubclass(func, req_sublass):
                raise Exception(f"@{name} must implement {req_sublass.__name__} interface")

            hippo_ensure_meta_lists(func)
            for decorator in decorators:
                func.__hippo_decorators.append(decorator)

            if argdecorator is not None:
                func.__hippo_argdecorators.append(argdecorator)
            return cast(HippoDecoratorClass, func)
        else:
            if not applicable_to_method:
                raise Exception(f"@{name} cannot be applied to method")

            @functools.wraps(func)
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                return func(*args, **kwargs)
            hippo_wrapper = cast(HippoDecoratorFunc, wrapper)
            if argdecorator is not None:
                hippo_wrapper.__hippo_decorator = argdecorator
            return hippo_wrapper
    return decorator


# TODO: base type
# TODO: transformations
def hippo_make_decorator(
        name: str,
        argdec_name: str | None = None,
        class_ok: bool = True,
        method_ok: bool = True,
        markers: List[str] | None = None,
        defaults: Dict[str, Any] | None = None,
) -> Callable[..., Callable]:
    markers = markers or []
    defaults = defaults or {}
    argdec_name = argdec_name or name

    def decorator(*args: Any, **kwargs: Any) -> Callable:
        dec = {
                "__decorator__": argdec_name,
                **defaults
        }
        # trick to let use decorator with or without parentheses
        if len(args) == 1 and callable(args[0]):
            # used without parentheses, called by system,
            # first arg is actually a function
            func = args[0]
            wrapper = get_wrapper_for_annotation(
                    name,
                    class_ok,
                    method_ok,
                    markers,
                    dec
            )
            return wrapper(func)  # type: ignore
        dec = {
                "__decorator__": argdec_name,
                **defaults,
                **kwargs
        }
        # used directly by user with arguments
        return get_wrapper_for_annotation(
                    name,
                    class_ok,
                    method_ok,
                    markers,
                    dec
        )
    return decorator


def RequestMapping(path: strList = [], consumes: strList = [],
                   headers: strList = [], method: strList = [],
                   name: str = "", params: strList = [],
                   produces: strList = [], value: strList = []
                   ) -> Callable:
    decorator = hippo_make_decorator(
            "RequestMapping",
            markers=[],
            defaults={
                "path": [],
                "consumes": [],
                "headers": [],
                "method": [],
                "name": "",
                "params": [],
                "produces": [],
                "value": [],
            },
    )
    return decorator(
            path,
            path=getListForStrList(path),
            name=name,
            consumes=getListForStrList(consumes),
            headers=getListForStrList(headers),
            method=getListForStrList(method),
            params=getListForStrList(params),
            produces=getListForStrList(produces),
            value=getListForStrList(value),
    )


def GetMapping(path: strList = [], consumes: strList = [],
               headers: strList = [], name: str = "",
               params: strList = [], produces: strList = [],
               value: strList = []) -> Callable:
    if callable(path):
        func = path
        wrapper = GetMapping()
        return wrapper(func)
    else:
        return RequestMapping(path, consumes, headers, "GET",
                              name, params, produces, value)


def PostMapping(path: strList = [], consumes: strList = [],
                headers: strList = [], name: str = "",
                params: strList = [], produces: strList = [],
                value: strList = []) -> Callable:
    if callable(path):
        func = path
        wrapper = PostMapping()
        return wrapper(func)
    else:
        return RequestMapping(path, consumes, headers, "POST",
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


def RequestHeader(cls: T, name: Optional[str] = None, required: bool = False) -> HippoArgDecorator:
    metadata = {
            "__decorator__": "RequestHeader",
            "name": name,
            "required": required
    }
    return Annotated[cls, AnnotationMetadata(metadata)]


def Configuration(cls: Type) -> HippoDecoratorClass:
    hippo_ensure_meta_lists(cls)
    cls.__hippo_decorators.append("Configuration")
    return cast(HippoDecoratorClass, cls)


def Value(cls: T, value: str) -> HippoArgDecorator:
    metadata = {
            "__decorator__": "Value",
            "value": value
    }
    return Annotated[cls, AnnotationMetadata(metadata)]

# TODO: PropertySource


def ExceptionHandler(exc_type: Optional[type[Exception]] = None) -> Callable:
    if isinstance(exc_type, type) and issubclass(exc_type, Exception):
        dec = {
                "__decorator__": "ExceptionHandler",
                "type": exc_type,
        }
        markers: List[str] = []
        return get_wrapper_for_annotation("ExceptionHandler", False, True, markers,
                                          dec, req_sublass=HippoFilter)
    else:
        func = exc_type
        wrapper = ExceptionHandler()
        return wrapper(func)  # type: ignore


def ResponseStatus(code: int = 500, reason: str = "") -> Callable:
    decorator = hippo_make_decorator(
            "ResponseStatus",
            markers=["ResponseStatusException"],
            defaults={"code": 500, "reason": ""},
    )
    return decorator(code=code, reason=reason)


# TODO
def ControllerAdvice(cls: Type) -> Callable:
    decorator = hippo_make_decorator(
            "ControllerAdvice",
            markers=["ControllerAdvice", "Component"],
    )
    return decorator(cls)


def Filter(priority: int = 1) -> Callable:
    decorator = hippo_make_decorator(
            "Filter",
            markers=["Filter", "Component"],
            defaults={"priority": 1},
    )
    return decorator(priority, priority=priority)
