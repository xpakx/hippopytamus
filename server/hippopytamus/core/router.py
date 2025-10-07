from hippopytamus.protocol.interface import Request
from typing import Tuple
from typing import Dict, Any, Optional
import re
from hippopytamus.core.method_parser import RouteData


class HippoRouter:
    getRoutes: Dict[str, RouteData] = {}
    postRoutes: Dict[str, RouteData] = {}
    putRoutes: Dict[str, RouteData] = {}
    deleteRoutes: Dict[str, RouteData] = {}

    def routes_by_method(self, method: str) -> Dict[str, RouteData]:
        if method == 'POST':
            return self.postRoutes
        if method == 'PUT':
            return self.putRoutes
        if method == 'DELETE':
            return self.deleteRoutes
        return self.getRoutes

    def register_route(
            self,
            annotation: Dict,
            method_data: RouteData,
            url_prepend: Optional[str]
    ) -> None:
        mapping_meth = annotation.get('method', 'GET')
        for meth in mapping_meth:
            routes = self.routes_by_method(meth)
            for path in annotation['path']:
                p = f"{url_prepend}{path}" if url_prepend else path
                routes[p] = method_data

    def get_route(self, uri: str, request: Request) -> Optional[Tuple[RouteData, Dict[str, Any]]]:
        mapping_meth = request.get('method', 'GET')
        routes = self.routes_by_method(mapping_meth)
        route = routes.get(uri)
        print(route)
        pathvars: Dict[str, Any] = {}
        if not route:
            route, pathvars = self.try_find_varroute(routes, uri)
            print(route, pathvars)
        return route, pathvars

    # TODO: this is rather primitive temporary solution
    # TODO tree-based routing
    def try_find_varroute(
            self,
            routes: Dict[str, Any],
            uri: str
    ) -> Tuple[Optional[RouteData], Dict]:
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
