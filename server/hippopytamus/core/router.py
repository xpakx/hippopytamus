from typing import Tuple
from typing import Dict, Any, Optional
import re
from hippopytamus.core.method_parser import RouteData
from hippopytamus.logger.logger import LoggerFactory


class HippoRouter:
    def __init__(self) -> None:
        self.getRoutes: Dict[str, RouteData] = {}
        self.postRoutes: Dict[str, RouteData] = {}
        self.putRoutes: Dict[str, RouteData] = {}
        self.deleteRoutes: Dict[str, RouteData] = {}
        self.logger = LoggerFactory.get_logger()

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

    def get_route(
            self,
            uri: str,
            request: Dict
    ) -> Tuple[Optional[RouteData], Dict[str, Any]]:
        mapping_meth = request.get('method', 'GET')
        routes = self.routes_by_method(mapping_meth)
        route = routes.get(uri)
        self.logger.debug(route)
        pathvars: Dict[str, Any] = {}
        if not route:
            route, pathvars = self.try_find_varroute(routes, uri)
            self.logger.debug(f"{route} {pathvars}")
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
                self.logger.debug(path_vars)
                return value, path_vars
        return None, {}
