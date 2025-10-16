from typing import Type
from hippopytamus.data.repository import HippoRepository
from hippopytamus.logger.logger import LoggerFactory


class HippoRepositoryCreator:
    def __init__(self) -> None:
        self.logger = LoggerFactory.get_logger()
        self.logger.debug("HippoRepositoryCreator crated")

    # naive in-memory storage
    # TODO: parsing methods names
    # TODO: generating methods based on parsed method
    # TODO: arbitrary data backend
    def create_repo_impl(self, repo_cls: Type[HippoRepository]) -> None:
        self.logger.debug(f"Creating repository {repo_cls.__name__}")

        self.logger.debug("Patching constructor")
        original_init = getattr(repo_cls, "__init__", lambda self: None)

        def new_init(self, *args, **kwargs):  # type: ignore
            original_init(self, *args, **kwargs)
            self._store = {}
        repo_cls.__init__ = new_init  # type: ignore

        def save(self, entity):  # type: ignore
            self._store[getattr(entity, "id")] = entity
            return entity
        setattr(repo_cls, "save", save)

        def find_by_id(self, id):  # type: ignore
            return self._store.get(id)
        setattr(repo_cls, "find_by_id", find_by_id)

        def find_all(self):  # type: ignore
            return list(self._store.values())
        setattr(repo_cls, "find_all", find_all)

        def delete_by_id(self, id):  # type: ignore
            self._store.pop(id, None)
        setattr(repo_cls, "delete_by_id", delete_by_id)
