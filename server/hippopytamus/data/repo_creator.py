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


class Node:
    def __init__(self, field_name=None, left=None, right=None, op=None):
        self.field_name = field_name
        self.left = left
        self.right = right
        self.op = op
        self.value = None


class RepoPredicate:
    def __init__(self) -> None:
        self.head = None
        self.nodes_by_field = {}

    def set_field(self, fld, value) -> None:
        to_set = self.nodes_by_field.get(fld, [])
        for node in to_set:
            node.value = value

    def build_tree(self, fields):
        stack = []
        and_group = []

        for fld, op in fields:
            node = Node(field_name=fld)
            self.nodes_by_field.setdefault(fld, []).append(node)
            and_group.append(node)

            if op == 'or' or op == '':
                if len(and_group) == 1:
                    stack.append(and_group[0])
                else:
                    temp = and_group[0]
                    for n in and_group[1:]:
                        temp = Node(left=temp, right=n, op='and')
                    stack.append(temp)
                and_group = []

        node = stack.pop(0) if stack else None
        while stack:
            node = Node(left=node, right=stack.pop(0), op='or')

        self.head = node

    def print(self, node=None, indent=0):
        if node is None:
            node = self.head
        if node is None:
            return
        prefix = "  " * indent
        if node.field_name:
            print(f"{prefix}{node.field_name} = {node.value}")
        else:
            print(f"{prefix}{node.op.upper()}")
            if node.left:
                self.print(node.left, indent + 1)
            if node.right:
                self.print(node.right, indent + 1)

    def make_predicate(self, node=None):
        if node is None:
            node = self.head
        if node is None:
            return
        if node.field_name:
            return lambda entity: getattr(entity, node.field_name) == node.value
        elif node.op == 'and':
            left_pred = self.make_predicate(node.left)
            right_pred = self.make_predicate(node.right)
            return lambda entity: left_pred(entity) and right_pred(entity)
        elif node.op == 'or':
            left_pred = self.make_predicate(node.left)
            right_pred = self.make_predicate(node.right)
            return lambda entity: left_pred(entity) or right_pred(entity)


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

        print(definition.fields)
        pred = RepoPredicate()
        pred.build_tree(definition.fields)
        pred.print()

        # TODO: define associations btwn args/kwargs and fields
        # TODO: use return type for definiton.all if any

        def query(self, *args, **kwargs):
            # TODO: multiple fields
            if len(args) > 0:
                pred.set_field("id", args[0])
            predicate = pred.make_predicate()

            all = list(self._store.values())
            if predicate:
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
