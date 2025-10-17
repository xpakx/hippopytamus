from typing import cast
from enum import Enum, auto
from dataclasses import dataclass, field


@dataclass
class RepoMethodDefinition:
    action: str | None = None
    all: bool = False
    distinct: bool = False
    fields: list[tuple[str, str]] = field(default_factory=list)


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
