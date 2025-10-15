from typing import TypeVar, Generic, List, Optional
from hippopytamus.logger.logger import LoggerFactory

T = TypeVar("T")
ID = TypeVar("ID")


class HippoRepository(Generic[T, ID]):
    def __init__(self) -> None:
        self.logger = LoggerFactory.get_logger()
        self.logger.info("Repo created")

    def save(self, entity: T) -> T:
        raise NotImplementedError

    def find_by_id(self, id: ID) -> Optional[T]:
        raise NotImplementedError

    def find_all(self) -> List[T]:
        raise NotImplementedError

    def delete_by_id(self, id: ID) -> None:
        raise NotImplementedError
