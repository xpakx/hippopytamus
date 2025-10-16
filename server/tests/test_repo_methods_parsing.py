import pytest
from hippopytamus.data.repo_creator import tokenize_method, Token


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
