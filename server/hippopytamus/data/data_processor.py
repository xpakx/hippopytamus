from hippopytamus.core.container import ComponentProcessor, ComponentData
from hippopytamus.data.repository import HippoRepository
from hippopytamus.data.repo_creator import HippoRepositoryCreator
from hippopytamus.logger.logger import LoggerFactory


class RepoProcessor(ComponentProcessor):
    def __init__(self) -> None:
        self.repo_creator = HippoRepositoryCreator()
        self.logger = LoggerFactory.get_logger()

    def should_process(self, component: ComponentData) -> bool:
        return issubclass(component.componentClass, HippoRepository)

    def process(self, component: ComponentData) -> None:
        self.logger.debug(f"Processing component {component.component.__name__}")
        repo_cls = component.componentClass
        component.componentClass = self.repo_creator.create_repo_impl(repo_cls)
