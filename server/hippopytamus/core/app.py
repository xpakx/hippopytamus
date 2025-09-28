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
        classes = self.get_module_classes(module_name)
        print(classes)
        self.container = HippoContainer()
        for cls in classes:
            self.container.register(cls)
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
                print(f"Failed to import module {module_name}: {e}")

        classes = [obj for name, obj in all_classes if
                   'Component' in get_class_decorators(obj)]
        return classes
