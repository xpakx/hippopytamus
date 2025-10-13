from typing import List
from typing import Dict, Any, Type
from hippopytamus.core.extractor import get_class_methods, get_class_argdecorators
from hippopytamus.core.extractor import get_type_name, get_class_decorators
from hippopytamus.core.method_parser import DependencyData
from hippopytamus.logger.logger import LoggerFactory
from dataclasses import dataclass, field


@dataclass
class ClassData:
    name: str = ""
    advice: bool = False
    filter: bool = False
    dependencies: List[DependencyData] = field(default_factory=list)
    methods: List[Any] = field(default_factory=list)
    constructor: Any = None
    markers: List[str] = field(default_factory=list)
    decorators: List[Dict[str, Any]] = field(default_factory=list)
    url_prepend: str | None = None


class HippoClassProcessor:
    def __init__(self) -> None:
        self.logger = LoggerFactory.get_logger()

    def parse_class(self, cls: Type) -> ClassData:
        class_data = ClassData()
        class_data.name = get_type_name(cls)
        all_methods = get_class_methods(cls)
        class_data.decorators = get_class_argdecorators(cls)
        class_data.markers = get_class_decorators(cls)

        for method in all_methods:
            method_name = method.get('name', 'unknown')
            if method_name == "__init__":
                class_data.constructor = method
            else:
                class_data.methods.append(method)

        for dec in class_data.decorators:
            if dec['__decorator__'] == "RequestMapping":
                paths = dec['path']
                if len(paths) > 0:
                    class_data.url_prepend = paths[0]  # TODO: multiple paths?
        for marker in class_data.markers:
            if marker == "ControllerAdvice":
                class_data.advice = True
            if marker == "Filter":
                class_data.filter = True
        return class_data
