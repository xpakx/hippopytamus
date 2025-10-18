from hippopytamus.data.repo_parser import (
       tokenize_method, Token, TokenParser,
       MethodParseError, update_with_type_hints
)
from typing import List, Optional


def test_basic_find():
    tokens = tokenize_method("find_by_name")
    assert tokens == [Token.FIND, Token.BY, (Token.FIELD, "name")]


def test_delete_by_field():
    tokens = tokenize_method("delete_by_id")
    assert tokens == [Token.DELETE, Token.BY, (Token.FIELD, "id")]


def test_find_distinct_and_field():
    tokens = tokenize_method("find_distinct_by_name")
    assert tokens == [Token.FIND, Token.DISTINCT, Token.BY, (Token.FIELD, "name")]


def test_multiple_fields_and_connector():
    tokens = tokenize_method("find_by_name_and_age")
    assert tokens == [
        Token.FIND, Token.BY,
        (Token.FIELD, "name"), Token.AND, (Token.FIELD, "age")
    ]


def test_fields_with_or_connector():
    tokens = tokenize_method("find_by_name_or_email")
    assert tokens == [
        Token.FIND, Token.BY,
        (Token.FIELD, "name"), Token.OR, (Token.FIELD, "email")
    ]


def test_field_with_multiple_underscores():
    tokens = tokenize_method("find_by_created_at_and_updated_at")
    assert tokens == [
        Token.FIND, Token.BY,
        (Token.FIELD, "created_at"), Token.AND, (Token.FIELD, "updated_at")
    ]


def test_parse_tokens():
    tokens = tokenize_method("find_distinct_by_name_and_age")
    parser = TokenParser(tokens)
    parsed = parser.parse()
    assert parsed.action == 'find'
    assert parsed.distinct is True
    assert parsed.fields == [('name', 'and'), ('age', '')]


def test_parser_throw_error_for_bad_tokens():
    bad_tokens = tokenize_method("username_and_by_find_age")
    bad_parser = TokenParser(bad_tokens)
    thrown = False
    try:
        bad_parser.parse()
    except MethodParseError:
        thrown = True
    assert thrown


def test_parse_save():
    tokens = tokenize_method("save")
    parser = TokenParser(tokens)
    parsed = parser.parse()
    assert parsed.action == 'save'
    assert parsed.distinct is False
    assert parsed.all is False
    assert parsed.fields == []


def test_parse_find_by_id():
    tokens = tokenize_method("find_by_id")
    parser = TokenParser(tokens)
    parsed = parser.parse()
    assert parsed.action == 'find'
    assert parsed.distinct is False
    assert parsed.all is False
    assert parsed.fields == [('id', '')]


def test_parse_delete_by_id():
    tokens = tokenize_method("delete_by_id")
    parser = TokenParser(tokens)
    parsed = parser.parse()
    assert parsed.action == 'delete'
    assert parsed.distinct is False
    assert parsed.all is False
    assert parsed.fields == [('id', '')]


def test_parse_find_all():
    tokens = tokenize_method("find_all")
    parser = TokenParser(tokens)
    parsed = parser.parse()
    assert parsed.action == 'find'
    assert parsed.distinct is False
    assert parsed.all is True
    assert parsed.fields == []


def test_update_with_type_hints_sets_all_list():
    def find_by_name(name: str) -> List[int]:
        pass
    tokens = tokenize_method(find_by_name.__name__)
    parser = TokenParser(tokens)
    parsed = parser.parse()
    update_with_type_hints(find_by_name, parsed)
    assert parsed.all is True


def test_update_with_type_hints_sets_all_optional():
    def find_by_name(name: str) -> Optional[List[int]]:
        pass
    tokens = tokenize_method(find_by_name.__name__)
    parser = TokenParser(tokens)
    parsed = parser.parse()
    update_with_type_hints(find_by_name, parsed)
    assert parsed.all is True


def test_update_with_type_hints_sets_all_optional_new():
    def find_by_name() -> List[int] | None:
        pass
    tokens = tokenize_method(find_by_name.__name__)
    parser = TokenParser(tokens)
    parsed = parser.parse()
    update_with_type_hints(find_by_name, parsed)
    assert parsed.all is True


def test_update_with_type_hints_sets_all_false():
    def find_all_by_name() -> int:
        pass
    tokens = tokenize_method(find_all_by_name.__name__)
    parser = TokenParser(tokens)
    parsed = parser.parse()
    update_with_type_hints(find_all_by_name, parsed)
    assert parsed.all is False
