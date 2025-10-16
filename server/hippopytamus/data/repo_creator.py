from typing import Type
from hippopytamus.data.repository import HippoRepository
from hippopytamus.logger.logger import LoggerFactory
from enum import Enum, auto


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


class Token(Enum):
    FIND = auto()
    DELETE = auto()
    COUNT = auto()
    SAVE = auto()

    DISTINCT = auto()

    BY = auto()
    ALL = auto()

    AND = auto()
    OR = auto()
    FIELD = auto()


def tokenize_method(name: str):
    parts = name.split('_')
    tokens = []
    i = 0

    curr_field = []

    def append_field():
        if len(curr_field) > 0:
            tokens.append((Token.FIELD, "_".join(curr_field)))
            curr_field.clear()

    while i < len(parts):
        part = parts[i]
        if part == 'find':
            append_field()
            tokens.append(Token.FIND)
        elif part == 'delete':
            append_field()
            tokens.append(Token.DELETE)
        elif part == 'count':
            append_field()
            tokens.append(Token.COUNT)
        elif part == 'save':
            append_field()
            tokens.append(Token.SAVE)
        elif part == 'distinct':
            append_field()
            tokens.append(Token.DISTINCT)
        elif part == 'all':
            append_field()
            tokens.append(Token.ALL)
        elif part == 'by':
            append_field()
            tokens.append(Token.BY)
        elif part == 'and':
            append_field()
            tokens.append(Token.AND)
        elif part == 'or':
            append_field()
            tokens.append(Token.OR)
        else:
            curr_field.append(part)
        i += 1
    append_field()
    return tokens
