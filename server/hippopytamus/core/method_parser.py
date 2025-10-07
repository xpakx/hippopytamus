from typing import List
from typing import Dict, Any, Type, Optional
from hippopytamus.core.extractor import get_type_name
from dataclasses import dataclass, field


@dataclass
class RouteData:
    component: str = "unknown"
    methodName: str = "unknown"
    method: Any = None
    bodyParam: Optional[int] = None
    bodyParamType: Optional[Type] = None
    paramLen: int = 0
    pathVariables: List = field(default_factory=list)
    requestParams: List = field(default_factory=list)
    headers: List = field(default_factory=list)


@dataclass
class MethodData:
    component: str = "unknown"
    methodName: str = "unknown"
    method: Any = None
    bodyParam: Optional[int] = None
    bodyParamType: Optional[Type] = None
    paramLen: int = 0
    pathVariables: List = field(default_factory=list)
    requestParams: List = field(default_factory=list)
    headers: List = field(default_factory=list)

    def to_route(self) -> RouteData:
        return RouteData(
                component=self.component,
                methodName=self.methodName,
                method=self.method,
                bodyParam=self.bodyParam,
                bodyParamType=self.bodyParamType,
                paramLen=self.paramLen,
                pathVariables=self.pathVariables,
                requestParams=self.requestParams,
                headers=self.headers,
        )


class HippoMethodProcessor:
    def process_method(self, signature: List, method_data: MethodData) -> None:
        for param_num, param in enumerate(signature):
            if not param:
                # TODO: these are not type annotated
                # might be nice to add "Unknown" or "Any"
                # in get_class_data and guess their
                # type and function depending on the context
                continue
            for dec in param.get('annotations', []):
                self.process_param_decorator(
                        dec,
                        param,
                        param_num,
                        method_data
                )

    def process_param_decorator(
            self,
            dec: Dict,
            param: Dict,
            param_num: int,
            method_data: MethodData
    ) -> None:
        method_name = method_data.methodName
        if dec.get('__decorator__') == "RequestBody":
            print(f"Found @RequestBody for {method_name} at {param_num}")
            method_data.bodyParam = param_num
            method_data.bodyParamType = param.get('class')
        elif dec.get('__decorator__') == "PathVariable":
            print("Found @PathVariable for", method_name, "at", param_num)
            path_name = dec.get('name')
            if not path_name:
                path_name = param.get('name')
            method_data.pathVariables.append({
                    "name": path_name,
                    "param": param_num,
                    "defaultValue": dec.get('defaultValue'),
                    "required": dec.get('required'),
                    "type": param.get('class')
            })
        elif dec.get('__decorator__') == "RequestHeader":
            print("Found @RequestHeader for", method_name, "at", param_num)
            header_name = dec.get('name')
            if not header_name:
                header_name = param.get('name')
            method_data.headers.append({
                    "name": header_name,
                    "param": param_num,
                    "required": dec.get('required'),
                    "type": param.get('class')
            })
        elif dec.get('__decorator__') == "RequestParam":
            print("Found @RequestParam for", method_name, "at", param_num)
            rparam_name = dec.get('name')
            if not rparam_name:
                rparam_name = param.get('name')
            method_data.requestParams.append({
                    "name": rparam_name,
                    "param": param_num,
                    "defaultValue": dec.get('defaultValue'),
                    "required": dec.get('required'),
                    "type": param.get('class')
            })
        else:
            print("Param", param_num, "in", method_name, "is not annotated")

    def process_constructor(
            self,
            signature: List,
            class_dependencies: List
    ) -> None:
        for param_num, param in enumerate(signature):
            if not param:
                continue
            param_name = param.get('class')
            if not param_name:
                continue  # TODO: guess type
            dep_name = ""
            if type(param_name) is str:
                # MAYBE: this should be improved to make it possible
                # to prepend module names
                dep_name = param_name
            else:
                dep_name = get_type_name(param_name)
            value = False
            for annot in param.get('annotations'):
                if annot['__decorator__'] == 'Value':
                    value = True
                    dep_name = annot['value']
                    break
            class_dependencies.append({
                    "name": dep_name,
                    "type": "Component" if not value else "Value",
                    "param": param_num,
            })
