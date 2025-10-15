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
    def create_repo_impl(self, repo_cls: Type[HippoRepository]) -> HippoRepository:
        store = {}

        self.logger.debug(f"Creating repository {repo_cls.__name__}")

        class Impl(repo_cls):
            def save(self, entity):
                store[getattr(entity, "id")] = entity
                return entity

            def find_by_id(self, id):
                return store.get(id)

            def find_all(self):
                return list(store.values())

            def delete_by_id(self, id):
                store.pop(id, None)

        return Impl()
