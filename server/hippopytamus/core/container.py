from hippopytamus.protocol.interface import Servlet, Response, Request
from typing import List
from typing import Dict, Any, cast, Type
from hippopytamus.core.extractor import get_class_data


class HippoContainer(Servlet):
    components: List[Any] = []
    routes: Dict[str, Any] = {}

    def register(self, cls: Type) -> None:
        # TODO dependency injection
        # TODO shouldn't be created right now
        component = cls()
        metadata = get_class_data(cls)
        for method in metadata:
            method_name = method.get('name', 'unknown')
            print(len(method.get('signature', [])), 'params in', method_name)

            param_num = 0
            request_param_num = None
            signature = method.get('signature', [])
            for param_num, param in enumerate(signature):
                for dec in param.get('annotations', []):
                    if dec.get('__decorator__') == "RequestBody":
                        print("Found @RequestBody for", method_name, "at", param_num)
                        request_param_num = param_num
                    else:
                        print("Param", param_num, "in", method_name, "is not annotated")

            for annotation in method['decorators']:
                if annotation['__decorator__'] == "RequestMapping":
                    # TODO http methods
                    # TODO append class-defined path
                    for path in annotation['path']:
                        self.routes[path] = {
                                "component": component,
                                "method": method['method_handle'],
                                "bodyParam": request_param_num
                        }

        self.components.append(component)

    def process_request(self, request: Request) -> Response:
        if not isinstance(request, dict):
            raise Exception("Error")
        # TODO path variables
        # TODO tree-based routing
        # TODO extracting and transforming body, path variables, query params
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
            if route['bodyParam'] is not None:
                # TODO: diff bodyParam positions
                return cast(Dict, route['method'](route['component'], request))
            else:
                return cast(Dict, route['method'](route['component']))
        return {}
