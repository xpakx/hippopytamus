from typing import get_type_hints, List
from typing import Dict, Any, cast, Type
from typing import Annotated, get_origin, get_args
from typing import Optional
from inspect import Signature, Parameter
import inspect
from hippopytamus.core.annotation import HippoDecoratorClass
from hippopytamus.core.annotation import AnnotationMetadata


def get_class_decorators(cls: Type) -> List[str]:
    hippo_cls = cast(HippoDecoratorClass, cls)
    if hasattr(hippo_cls, '__hippo_decorators'):
        return hippo_cls.__hippo_decorators
    return []


def get_class_argdecorators(cls: Type) -> List[Dict[str, Any]]:
    hippo_cls = cast(HippoDecoratorClass, cls)
    if hasattr(hippo_cls, '__hippo_argdecorators'):
        return hippo_cls.__hippo_argdecorators
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
    print(f"class argdecorators: {get_class_argdecorators(cls)}")
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
