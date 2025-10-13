from hippopytamus.protocol.interface import Servlet, Response, Request
from typing import List, get_origin, Union
from typing import Dict, Any, cast, Type, Optional
from hippopytamus.core.extractor import get_class_methods, get_class_argdecorators
from hippopytamus.core.extractor import get_type_name, get_class_decorators
from hippopytamus.core.exception import HippoExceptionManager
from urllib.parse import urlparse, parse_qs
import json
from hippopytamus.core.method_parser import RouteData, MethodData, DependencyData
from hippopytamus.core.method_parser import HippoMethodProcessor
from hippopytamus.core.router import HippoRouter
from hippopytamus.logger.logger import LoggerFactory
from hippopytamus.core.filter import HippoFilter
from dataclasses import dataclass, field


@dataclass
class ClassData:
    name: str = ""
    advice: bool = False
    filter: bool = False
    dependencies: List[DependencyData] = field(default_factory=list)
    methods: List[Any] = field(default_factory=list)
    markers: List[str] = field(default_factory=list)
    decorators: List[Dict[str, Any]] = field(default_factory=list)
    url_prepend: str | None = None


class HippoClassProcessor:
    def __init__(self) -> None:
        pass

    def parse_class(self, cls: Type) -> ClassData:
        class_data = ClassData()
        class_data.name = get_type_name(cls)
        class_data.methods = get_class_methods(cls)  # TODO: separate constructor
        class_data.decorators = get_class_argdecorators(cls)
        class_data.markers = get_class_decorators(cls)
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
