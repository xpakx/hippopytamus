from hippopytamus.protocol.interface import Servlet, Response, Request
from typing import List, get_origin, Union
from typing import Dict, Any, cast, Type, Optional
from hippopytamus.core.extractor import get_type_name
from hippopytamus.core.exception import HippoExceptionManager
from hippopytamus.core.exception import HippoInternalForbiddenException
from hippopytamus.core.exception import HippoInternalNotFoundException
from urllib.parse import urlparse, parse_qs
import json
from hippopytamus.core.method_parser import RouteData, MethodData, DependencyData
from hippopytamus.core.method_parser import HippoMethodProcessor
from hippopytamus.core.class_parser import HippoClassProcessor
from hippopytamus.core.router import HippoRouter
from hippopytamus.logger.logger import LoggerFactory
from hippopytamus.core.filter import HippoFilter
from dataclasses import dataclass, field


@dataclass
class ComponentData:
    component: Optional[Any]
    componentClass: Type
    dependencies: List[DependencyData] = field(default_factory=list)


@dataclass
class FilterData:
    name: str
    priority: int


class HippoContainer(Servlet):
    def __init__(self) -> None:
        self.components: Dict[str, ComponentData] = {}
        self.exceptionManager = HippoExceptionManager()
        self.method_processor = HippoMethodProcessor()
        self.router = HippoRouter()
        self.logger = LoggerFactory.get_logger()
        self.filter_chain: List[FilterData] = []
        self.class_processor = HippoClassProcessor()

    def register(self, cls: Type) -> None:
        class_data = self.class_processor.parse_class(cls)
        if self.components.get(class_data.name) is not None:
            self.logger.warn(f"Component {class_data.name} already registered!")
            return

        self.method_processor.process_constructor(
                class_data.constructor.get('signature', []),
                class_data.dependencies
        )

        for method in class_data.methods:
            method_name = method.get('name', 'unknown')
            self.logger.debug(f"{len(method.get('signature', []))} params in {method_name}")
            signature = method.get('signature', [])
            params_len = len(signature)

            method_data = MethodData(
                    component=class_data.name,
                    methodName=method_name,
                    method=method['method_handle'],
                    paramLen=params_len,
            )

            self.method_processor.process_method(signature, method_data)

            self.logger.debug(f"Found decorators for method {method_name}", decorators=method['decorators'])
            for annotation in method['decorators']:
                if annotation['__decorator__'] == "RequestMapping":
                    self.router.register_route(
                            annotation,
                            method_data.to_route(),
                            class_data.url_prepend
                    )
                elif annotation['__decorator__'] == "ExceptionHandler":
                    self.logger.debug(f"Found @ExceptionHandler in {method_name}")
                    self.exceptionManager.create_handler(
                            cast(Dict, annotation),
                            method,
                            cls,
                            class_data.advice
                    )

        if class_data.filter:
            prior = class_data.filter_priority
            filter_priority = prior if prior is not None else 1
            filter_data = FilterData(
                    name=class_data.name,
                    priority=filter_priority,
            )
            inserted = False
            for i, existing in enumerate(self.filter_chain):
                if filter_data.priority < existing.priority:
                    self.filter_chain.insert(i, filter_data)
                    inserted = True
                    break
            if not inserted:
                self.filter_chain.append(filter_data)

        self.logger.debug(class_data.dependencies)

        self.components[class_data.name] = ComponentData(
                component=None,
                componentClass=cls,
                dependencies=class_data.dependencies,
        )

    def process_request(self, request: Request) -> Response:
        try:
            return self.do_process_request(request)
        except Exception as e:
            return self.process_exception(e, None)

    def do_process_request(self, request: Request) -> Response:
        if not isinstance(request, dict):
            raise Exception("Error")
        # TODO extracting and transforming body, path variables, query params
        uri = request['uri']
        parsed = urlparse(uri)
        query_params = parse_qs(parsed.query)
        uri = parsed.path
        route, pathvars = self.router.get_route(uri, request)
        self.logger.debug(f"PROCESSED: {pathvars}")

        request_context = {
                "path": uri,
                "params": query_params,
                "pathvars": pathvars,
        }
        filtered = self.filter_request(request, request_context)

        if filtered:
            raise HippoInternalForbiddenException()

        if not route:
            raise HippoInternalNotFoundException()

        params: List[Any] = [None] * route.paramLen
        self.set_body_param(params, request, route)
        self.set_request_params(params, query_params, route)
        self.set_path_variables(params, pathvars, route)
        self.set_header_params(params, request, route)

        try:
            component_name = route.component
            component = self.getComponent(component_name)
            resp = route.method(component, *params)
            return self.transform_response(resp)
        except Exception as e:
            return self.process_exception(e, component_name)

        return {}

    def set_body_param(self, params: List, request: Dict, route: RouteData) -> None:
        requestBody: Optional[str] = request.get('body')
        if requestBody is None:
            return
        bodyParamType = route.bodyParamType
        if self.needs_conversion(requestBody, bodyParamType):
            if self.is_dict(bodyParamType):
                try:
                    requestBody = json.loads(requestBody)
                except Exception:
                    self.logger.error("Malformed json")
        if route.bodyParam is not None:
            params[route.bodyParam] = requestBody

    def needs_conversion(self, obj: Any, obj_type: Any) -> bool:
        obj_exists = obj is not None
        obj_type_defined = obj_type is not None
        obj_type_needs_conversion = obj_type_defined and obj_type is not str
        return obj_exists and obj_type_needs_conversion

    def is_dict(self, paramType: Any) -> bool:
        return paramType in [dict, Dict] or get_origin(paramType) is dict

    def set_request_params(
            self,
            params: List,
            query_params: Dict,
            route: RouteData
    ) -> None:
        for rparam in route.requestParams:
            valueList = query_params.get(rparam['name'])
            value: Optional[Union[int, str]] = None
            if isinstance(valueList, list):
                value = valueList[0] if len(valueList) > 0 else None
            else:
                value = valueList
            if value is not None and type(value) is not rparam['type']:
                # TODO: other primitive types (?)
                if rparam['type'] is int:
                    value = int(value)
            if value is None and rparam['defaultValue'] is not None:
                value = rparam['defaultValue']
            params[rparam['param']] = value

    def set_path_variables(
            self,
            params: List,
            pathvars: Dict,
            route: RouteData
    ) -> None:
        for pathvar in route.pathVariables:
            value = pathvars.get(pathvar['name'])
            if value is not None and type(value) is not pathvar['type']:
                # TODO: other primitive types (?)
                if pathvar['type'] is int:
                    value = int(value)
            if value is None and pathvar['defaultValue'] is not None:
                value = pathvar['defaultValue']
            params[pathvar['param']] = value

    def set_header_params(
            self,
            params: List,
            request: Dict,
            route: RouteData
    ) -> None:
        for headervar in route.headers:
            value = None
            # TODO: do that more elegant
            for header in request['headers']:
                if header == headervar['name']:
                    value = request['headers'][header]
                    break
            if value is not None and type(value) is not headervar['type']:
                # TODO: other primitive types (?)
                if headervar['type'] is int:
                    value = int(value)
            params[headervar['param']] = value

    def getComponent(self, name: str) -> Any:
        component = self.components.get(name)
        if not component:
            return None
        if not component.component:
            deps = component.dependencies
            params: List[Any] = [None] * len(deps)
            for param in deps:
                if (param.dependencyType == 'Component'):
                    params[param.param] = self.getComponent(param.name)
                elif param.dependencyType == 'Value':
                    params[param.param] = eval(param.name)  # TODO
            component.component = component.componentClass(*params)

        return component.component

    def transform_response(self, resp: Response) -> Dict[str, Any]:
        # TODO add ResponseBody, and transform pydantic/pydantic-like types
        # jsonify dicts
        headers = {"Server": "Hippopytamus", "Content-Type": "text/html"}
        if not resp:
            return {"code": 200, "headers": headers}
        if (type(resp) is str):
            return {
                    "code": 200,
                    "body": bytes(resp, "utf-8"),
                    "headers": headers,
                    }
        if (type(resp) is bytes):
            return {
                    "code": 200,
                    "body": resp,
                    "headers": headers,
                    }
        if (type(resp) is dict) and 'code' not in resp:
            return {
                    "code": 200,
                    "body": bytes(json.dumps(resp), "utf-8"),
                    "headers": headers,
                    }
        return cast(Dict, resp)

    def process_exception(self, e: Union[Exception, str], cls: Optional[str]) -> Dict:
        self.logger.debug(f"Error in handler: {repr(e)}")
        ex_type = get_type_name(type(e)) if type(e) is not str else e
        self.logger.debug(f"Exception type: {ex_type}")
        handler = self.exceptionManager.get_exception_handler(ex_type, cls)
        if handler is None:
            return {"code": 500, "body": None}
        neededComponent = handler.get_component()
        if neededComponent is not None:
            try:
                handler.set_component(self.getComponent(neededComponent))
            except Exception:
                self.logger.error("Couldn't create component needed for exception handler")
        self.logger.debug(f"Handler: {handler}")
        # TODO: create dummy exception if needed
        transformed = handler.transform(e)  # type: ignore
        if type(transformed['body']) is str:
            transformed['body'] = bytes(transformed['body'], "utf-8")
        return transformed

    def filter_request(self, request: Request, context: Dict) -> bool:
        for filter_data in self.filter_chain:
            filter_name = filter_data.name
            filter = cast(HippoFilter, self.getComponent(filter_name))
            filtered = filter.filter(request, context)
            if filtered:
                return True
        return False
