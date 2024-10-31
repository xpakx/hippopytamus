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
            for annotation in method['decorators']:
                if annotation['__decorator__'] == "RequestMapping":
                    # TODO http methods
                    # TODO append class-defined path
                    for path in annotation['path']:
                        self.routes[path] = {
                                "component": component,
                                "method": method['method_handle']
                        }

        self.components.append(component)

    def process_request(self, request: Request) -> Response:
        if not isinstance(request, dict):
            raise Exception("Error")
        # TODO path variables
        # TODO tree-based routing
        # TODO transforming body, path variables, query params
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
            return cast(Dict, route['method'](route['component'], request))
        return {}
