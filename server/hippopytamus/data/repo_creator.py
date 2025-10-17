from typing import Type, Callable
from hippopytamus.data.repository import HippoRepository
from hippopytamus.data.repo_parser import tokenize_method, TokenParser
from hippopytamus.data.repo_parser import RepoMethodDefinition
from hippopytamus.data.repo_predicate import RepoPredicate
from hippopytamus.logger.logger import LoggerFactory
import inspect


class HippoRepositoryCreator:
    def __init__(self) -> None:
        self.logger = LoggerFactory.get_logger()
        self.logger.debug("HippoRepositoryCreator crated")

    # naive in-memory storage
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

        for method_name, _ in inspect.getmembers(repo_cls, predicate=inspect.isfunction):
            if method_name.startswith("_"):
                continue
            self.logger.debug(f"Parsing repository method: {method_name}")
            parsed_func = self.parse_method(method_name)
            self.logger.debug(f"Patching repository method: {method_name}")
            setattr(repo_cls, method_name, parsed_func)

    def parse_method(self, method_name: str) -> Callable | None:
        tokens = tokenize_method(method_name)
        parser = TokenParser(tokens)
        parsed = parser.parse()
        return self.generate_method(parsed)

    def generate_method(self, definition: RepoMethodDefinition) -> Callable | None:
        if definition.action == "save":
            def save(self, entity):  # type: ignore
                self._store[getattr(entity, "id")] = entity
                return entity
            return save

        self.logger.debug(definition.fields)
        pred = RepoPredicate()
        pred.build_tree(definition.fields)

        # TODO: define associations btwn args/kwargs and fields
        # TODO: use return type for definiton.all if any

        def query(self, *args, **kwargs):  # type: ignore
            # TODO: multiple fields
            if len(args) > 0:
                pred.set_field("id", args[0])
            predicate = pred.make_predicate()

            all = list(self._store.values())
            if predicate is not None:
                candidates = [e for e in all if predicate(e)]
            else:
                candidates = all

            if len(candidates) == 0:
                return [] if definition.all else None
            if not definition.all and definition.action != "count":
                candidates = [candidates[0]]

            if definition.action == "find":
                if definition.all:
                    return candidates
                elif len(candidates) > 0:
                    return candidates[0]
                else:
                    return None
            if definition.action == "delete":
                for entity in candidates:
                    self._store.pop(entity.id)
                if definition.all:
                    return candidates
                elif len(candidates) > 0:
                    return candidates[0]
                else:
                    return None
            if definition.action == "count":
                return len(candidates)
        return query
