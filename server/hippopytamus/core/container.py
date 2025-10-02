from hippopytamus.protocol.interface import Servlet, Response, Request
from typing import List, Tuple, get_origin, Union
from typing import Dict, Any, cast, Type, Optional
from hippopytamus.core.extractor import get_class_data, get_class_argdecorators
from urllib.parse import urlparse, parse_qs
import json
import re


class HippoContainer(Servlet):
    components: Dict[str, Any] = {}
    getRoutes: Dict[str, Any] = {}
    postRoutes: Dict[str, Any] = {}
    putRoutes: Dict[str, Any] = {}
    deleteRoutes: Dict[str, Any] = {}

    def register(self, cls: Type) -> None:
        component_name = cls.__name__
        metadata = get_class_data(cls)
        class_decorators = get_class_argdecorators(cls)
        url_prepend = None
        for dec in class_decorators:
            if dec['__decorator__'] == "RequestMapping":
                paths = dec['path']
                if len(paths) > 0:
                    url_prepend = paths[0]  # TODO: multiple paths?
        class_dependencies = []

        for method in metadata:
            method_name = method.get('name', 'unknown')
            print(len(method.get('signature', [])), 'params in', method_name)
            signature = method.get('signature', [])
            params_len = len(signature)

            method_data = {
                    "component": component_name,
                    "methodName": method_name,
                    "method": method['method_handle'],
                    "bodyParam": None,
                    "bodyParamType": None,
                    "paramLen": params_len,
                    "pathVariables": [],
                    "requestParams": [],
                    "headers": [],
            }

            if method_name == "__init__":
                for param_num, param in enumerate(signature):
                    if not param:
                        continue
                    param_name = param.get('class')
                    if not param_name:
                        continue  # TODO: guess type
                    dep_name = ""
                    if type(param_name) is str:
                        dep_name = param_name
                    else:
                        dep_name = param_name.__name__
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
            else:
                self.process_method(signature, method_data)

            for annotation in method['decorators']:
                if annotation['__decorator__'] == "RequestMapping":
                    self.register_route(annotation, method_data, url_prepend)

        print(class_dependencies)
        # TODO: maybe create components with routes earlier
        self.components[component_name] = {
                "component": None,
                "class": cls,
                "dependencies": class_dependencies,
        }

    def register_route(
            self,
            annotation: Dict,
            method_data: Dict,
            url_prepend: Optional[str]
    ) -> None:
        mapping_meth = annotation.get('method', 'GET')
        for meth in mapping_meth:
            routes = self.getRoutes
            if meth == 'POST':
                routes = self.postRoutes
            if meth == 'PUT':
                routes = self.putRoutes
            if meth == 'DELETE':
                routes = self.deleteRoutes
            for path in annotation['path']:
                p = f"{url_prepend}{path}" if url_prepend else path
                routes[p] = method_data

    def process_method(self, signature: List, method_data: Dict) -> None:
        method_name = method_data['methodName']

        for param_num, param in enumerate(signature):
            if not param:
                # TODO: these are not type annotated
                # might be nice to add "Unknown" or "Any"
                # in get_class_data and guess their
                # type and function depending on the context
                continue
            for dec in param.get('annotations', []):
                if dec.get('__decorator__') == "RequestBody":
                    print("Found @RequestBody for", method_name, "at", param_num)
                    method_data['bodyParam'] = param_num
                    method_data['bodyParamType'] = param.get('class')
                elif dec.get('__decorator__') == "PathVariable":
                    print("Found @PathVariable for", method_name, "at", param_num)
                    path_name = dec.get('name')
                    if not path_name:
                        path_name = param.get('name')
                    method_data['pathVariables'].append({
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
                    method_data['headers'].append({
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
                    method_data['requestParams'].append({
                            "name": rparam_name,
                            "param": param_num,
                            "defaultValue": dec.get('defaultValue'),
                            "required": dec.get('required'),
                            "type": param.get('class')
                    })
                else:
                    print("Param", param_num, "in", method_name, "is not annotated")

    def process_request(self, request: Request) -> Response:
        if not isinstance(request, dict):
            raise Exception("Error")
        # TODO path variables
        # TODO tree-based routing
        # TODO extracting and transforming body, path variables, query params
        uri = request['uri']
        parsed = urlparse(uri)
        query_params = parse_qs(parsed.query)
        uri = parsed.path

        mapping_meth = request.get('method', 'GET')
        routes = self.getRoutes
        if mapping_meth == 'POST':
            routes = self.postRoutes
        if mapping_meth == 'PUT':
            routes = self.putRoutes
        if mapping_meth == 'DELETE':
            routes = self.deleteRoutes

        route = routes.get(uri)
        pathvars: Dict[str, Any] = {}
        print(route)
        if not route:
            route, pathvars = self.try_find_varroute(routes, uri)
            print(route, pathvars)

        if not route:
            return {
                    "code": 404,
                    "body": b"<html><head></head><body><h1>Not found</h1></body></html>",
                    "headers": {
                        "Server": "Hippopytamus",
                        "Content-Type": "text/html"
                    }
            }
        if route:
            params: List[Any] = [None] * route['paramLen']

            requestBody = request.get('body')
            bodyParamType = route.get('bodyParamType')
            if requestBody is not None and bodyParamType is not None and bodyParamType is not str:
                if bodyParamType in [dict, Dict] or get_origin(bodyParamType) is dict:
                    try:
                        requestBody = json.loads(requestBody)
                    except Exception:
                        print("Malformed json")
            if route['bodyParam'] is not None:
                params[route['bodyParam']] = requestBody

            for rparam in route['requestParams']:
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

            for pathvar in route['pathVariables']:
                value = pathvars.get(pathvar['name'])
                if value is not None and type(value) is not pathvar['type']:
                    # TODO: other primitive types (?)
                    if pathvar['type'] is int:
                        value = int(value)
                if value is None and pathvar['defaultValue'] is not None:
                    value = pathvar['defaultValue']
                params[pathvar['param']] = value

            for headervar in route['headers']:
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

            try:
                component_name = cast(str, route.get('component'))
                component = self.getComponent(component_name)
                resp = route['method'](component, *params)
                return self.transform_response(resp)
            except Exception as e:
                print("Error in handler: ", repr(e))
                # TODO: exception handlers
                return {'code': 500, 'body': None}

        return {}

    def getComponent(self, name: str) -> Any:
        component = self.components.get(name)
        if not component:
            return None
        if not component['component']:
            deps = component['dependencies']
            params: List[Any] = [None] * len(deps)
            # TODO: detect cycles
            for param in deps:
                if (param['type'] == 'Component'):
                    params[param['param']] = self.getComponent(param['name'])
                elif param['type'] == 'Value':
                    params[param['param']] = eval(param['name'])  # TODO
            component['component'] = component['class'](*params)

        return component['component']

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

    # TODO: this is rather primitive temporary solution
    def try_find_varroute(self, routes: Dict[str, Any], uri: str) -> Tuple[Optional[Dict], Dict]:
        for key in routes:
            value = routes[key]
            if '{' not in key:
                continue
            pattern = re.sub(r"{(\w+)}", r"(?P<\1>[^/]+)", key)
            pattern = f"^{pattern}$"
            route_regex = re.compile(pattern)

            match = route_regex.match(uri)
            if match:
                path_vars = match.groupdict()
                print(path_vars)
                return value, path_vars
        return None, {}
