from hippopytamus.protocol.interface import Servlet, Response, Request
from typing import List
from typing import Dict, Any, cast, Type
from hippopytamus.core.extractor import get_class_data, get_class_argdecorators
from urllib.parse import urlparse, parse_qs


class HippoContainer(Servlet):
    components: List[Any] = []
    routes: Dict[str, Any] = {}

    def register(self, cls: Type) -> None:
        # TODO dependency injection
        # TODO shouldn't be created right now
        component = cls()
        metadata = get_class_data(cls)
        class_decorators = get_class_argdecorators(cls)
        url_prepend = None
        for dec in class_decorators:
            if dec['__decorator__'] == "RequestMapping":
                paths = dec['path']
                if len(paths) > 0:
                    url_prepend = paths[0]  # TODO: multiple paths?

        for method in metadata:
            method_name = method.get('name', 'unknown')
            print(len(method.get('signature', [])), 'params in', method_name)

            param_num = 0
            request_param_num = None
            signature = method.get('signature', [])
            params_len = len(signature)
            rparams = []
            pathvars = []
            for param_num, param in enumerate(signature):
                for dec in param.get('annotations', []):
                    if dec.get('__decorator__') == "RequestBody":
                        print("Found @RequestBody for", method_name, "at", param_num)
                        request_param_num = param_num
                    elif dec.get('__decorator__') == "PathVariable":
                        print("Found @PathVariable for", method_name, "at", param_num)
                        path_name = dec.get('name')
                        if not path_name:
                            path_name = param.get('name')
                        pathvars.append({
                                "name": path_name,
                                "param": param_num,
                                "defaultValue": dec.get('defaultValue'),
                                "required": dec.get('required')
                        })
                    elif dec.get('__decorator__') == "RequestHeader":
                        print("Found @RequestHeader for", method_name, "at", param_num)
                    elif dec.get('__decorator__') == "RequestParam":
                        print("Found @RequestParam for", method_name, "at", param_num)
                        rparam_name = dec.get('name')
                        if not rparam_name:
                            rparam_name = param.get('name')
                        rparams.append({
                                "name": rparam_name,
                                "param": param_num,
                                "defaultValue": dec.get('defaultValue'),
                                "required": dec.get('required')
                        })
                    else:
                        print("Param", param_num, "in", method_name, "is not annotated")

            for annotation in method['decorators']:
                if annotation['__decorator__'] == "RequestMapping":
                    # TODO http methods
                    for path in annotation['path']:
                        p = f"{url_prepend}{path}" if url_prepend else path
                        self.routes[p] = {
                                "component": component,
                                "method": method['method_handle'],
                                "bodyParam": request_param_num,
                                "paramLen": params_len,
                                "requestParams": rparams,
                                "pathVariables": pathvars,
                        }

        self.components.append(component)

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
            params: List[Any] = [None] * route['paramLen']
            if route['bodyParam'] is not None:
                params[route['bodyParam']] = request
            for rparam in route['requestParams']:
                valueList = query_params.get(rparam['name'])
                value = None
                if isinstance(valueList, list):
                    value = valueList[0] if len(valueList) > 0 else None
                else:
                    value = valueList
                if value is None and rparam['defaultValue'] is not None:
                    value = rparam['defaultValue']
                params[rparam['param']] = value
            resp = route['method'](route['component'], *params)
            return self.transform_response(resp)
        return {}

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
        return cast(Dict, resp)
