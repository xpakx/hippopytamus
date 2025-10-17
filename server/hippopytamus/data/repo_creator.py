from typing import Type, cast, Callable
from hippopytamus.data.repository import HippoRepository
from hippopytamus.logger.logger import LoggerFactory
from enum import Enum, auto
from dataclasses import dataclass, field
import inspect


@dataclass
class RepoMethodDefinition:
    action: str | None = None
    all: bool = False
    distinct: bool = False
    fields: list[tuple[str, str]] = field(default_factory=list)


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

        def query(self, *args, **kwargs):
            # TODO: multiple fields
            candidates = []
            if len(definition.fields) == 0:
                candidates = list(self._store.values())
            else:
                candidates.append(self._store.get(args[0]))

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


Tok = tuple[Token, str] | Token


def tokenize_method(name: str) -> list[Tok]:
    parts = name.split('_')
    tokens: list[Tok] = []
    i = 0

    curr_field: list[str] = []

    def append_field() -> None:
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


class MethodParseError(Exception):
    pass


class TokenParser:
    def __init__(self, tokens: list[Tok]) -> None:
        self.tokens = tokens
        self.pos = 0
        self.length = len(tokens)

    def current(self) -> Tok | None:
        return self.tokens[self.pos] if self.pos < self.length else None

    def consume(self, expected: Tok | None = None) -> Tok | None:
        cur = self.current()
        if expected:
            if isinstance(cur, tuple):
                raise MethodParseError(
                        f"Expected {expected}, got FIELD {cur[1]}"
                )
            if cur != expected:
                raise MethodParseError(f"Expected {expected}, got {cur}")
        self.pos += 1
        return cur

    def parse(self) -> RepoMethodDefinition:
        result = RepoMethodDefinition()

        cur = self.current()
        if cur not in (Token.FIND, Token.DELETE, Token.COUNT, Token.SAVE):
            raise MethodParseError(f"Method must start with action, got {cur}")
        cur = cast(Token, cur)
        result.action = cur.name.lower()
        self.consume()

        if self.current() == Token.ALL:
            result.all = True
            self.consume()

        if self.current() == Token.DISTINCT:
            result.distinct = True
            self.consume()

        if self.current() == Token.BY:
            self.consume()
            result.fields = self.parse_fields()
        elif self.current():
            raise MethodParseError("Fields must be preceded by 'by'")

        return result

    def parse_fields(self) -> list[tuple[str, str]]:
        fields = []
        while self.pos < self.length:
            cur = self.current()
            if isinstance(cur, tuple) and cur[0] == Token.FIELD:
                field_name = cur[1]
                self.consume()
                connector = ''
                if self.current() in (Token.AND, Token.OR):
                    consumed = cast(Token, self.consume())
                    connector = consumed.name.lower()
                fields.append((field_name, connector))
            else:
                raise MethodParseError(f"Unexpected token {cur} in fields")
        if len(fields) > 0:
            last = fields[len(fields) - 1]
            if last[1] != '':
                raise MethodParseError("Unfinished method")
        return fields
