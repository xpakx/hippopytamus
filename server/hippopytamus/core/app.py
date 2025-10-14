import pkgutil
import inspect
import os
import importlib
from hippopytamus.server.nonblocking import SelectTCPServer
from hippopytamus.protocol.http import HttpProtocol10
from typing import List, Any
from types import ModuleType
from hippopytamus.core.container import HippoContainer
from hippopytamus.core.extractor import get_class_decorators
from hippopytamus.logger.logger import LoggerFactory
from hippopytamus.core.lazy_import_utils import module_is_loaded, module_exists
from dataclasses import dataclass


# TODO: this should be loaded form file/context
@dataclass
class ServerOptions:
    host: str = "127.0.0.1"
    port: int = 8000


class HippoApp:
    def __init__(
            self,
            module_name: str,
            opt: ServerOptions = ServerOptions()
            ) -> None:
        self.logger = LoggerFactory.get_logger()
        all_classes = self.get_module_classes(module_name)
        self.hippo_self_inspect()
        components = self.get_components(all_classes)
        self.logger.debug(components)
        self.container = HippoContainer()
        for cls in components:
            self.container.register(cls)
        exceptions = self.get_status_exceptions(all_classes)
        self.logger.debug(f"Loaded exceptions: {exceptions}")
        for cls in exceptions:
            self.container.exceptionManager.register_exception(cls)
        self.server = SelectTCPServer(
                HttpProtocol10(),
                self.container, host=opt.host, port=opt.port)

    def inspect_module(self, module: ModuleType) -> Any:
        return inspect.getmembers(module, inspect.isclass)

    def run(self) -> None:
        self.server.listen()

    def get_module_classes(self, package_name: str) -> List[Any]:
        # TODO not a package
        package = importlib.import_module(package_name)
        if not package or not package.__file__:
            raise Exception("Error")
        package_dir = os.path.dirname(package.__file__)
        if not package_dir:
            raise Exception("Error")

        all_classes = []

        for _, module_name, is_pkg in pkgutil.\
                walk_packages([package_dir], prefix=package_name + "."):
            try:
                # Dynamically import the module or package
                module = importlib.import_module(module_name)
                all_classes.extend(self.inspect_module(module))
            except ImportError as e:
                self.logger.warn(f"Failed to import module {module_name}: {e}")

        all_classes_set = {cls for cls in all_classes}
        all_classes = list(all_classes_set)
        return all_classes

    def get_components(self, all_classes: List[Any]) -> List[Any]:
        return [obj for name, obj in all_classes if
                'Component' in get_class_decorators(obj)]

    def get_status_exceptions(self, all_classes: List[Any]) -> List[Any]:
        return [
            obj for name, obj in all_classes
            if issubclass(obj, Exception)
            and obj is not Exception
            and 'ResponseStatusException' in get_class_decorators(obj)
        ]

    def check_module(self, name: str) -> None:
        if module_exists(name):
            self.logger.debug(f"{name} module exists")
        if module_is_loaded(name):
            self.logger.debug(f"{name} module is loaded")

    def hippo_self_inspect(self) -> None:
        self.check_module('core')
        self.check_module('example')
        self.check_module('data')
        self.check_module('security')
