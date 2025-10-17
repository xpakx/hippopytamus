import pytest
from dataclasses import dataclass
from hippopytamus.data.repository import HippoRepository
from hippopytamus.data.repo_creator import HippoRepositoryCreator


@dataclass
class Entity:
    id: int
    name: str


@pytest.fixture
def repo():
    creator = HippoRepositoryCreator()

    class TestRepository(HippoRepository):
        pass
    creator.create_repo_impl(TestRepository)
    return TestRepository()


@dataclass
class EntityComplex:
    id: int
    name: str
    posts: int


@pytest.fixture
def repo_complex():
    creator = HippoRepositoryCreator()

    class TestRepository(HippoRepository):
        def find_all_by_name_and_posts(name: str, posts: int) -> list[EntityComplex]:
            pass

        def find_all_by_name_or_posts(name: str, posts: int) -> list[EntityComplex]:
            pass
    creator.create_repo_impl(TestRepository)
    return TestRepository()


def populate_store(repo: HippoRepository, *entities):
    for e in entities:
        repo._store[e.id] = e


def test_repo_has_store(repo):
    assert hasattr(repo, "_store")


def test_repository_creator_basic_save(repo):
    entity = Entity(id=1, name="Alice")

    saved = repo.save(entity)

    assert saved is entity
    assert repo._store[1] == entity


def test_repository_creator_basic_find_by_id(repo):
    alice = Entity(id=1, name="Alice")
    populate_store(repo, alice)

    found = repo.find_by_id(1)

    assert found == alice


def test_repository_creator_basic_find_all(repo):
    alice = Entity(id=1, name="Alice")
    bob = Entity(id=2, name="Bob")
    joan = Entity(id=3, name="Joan")
    populate_store(repo, alice, bob, joan)

    all_entities = repo.find_all()

    assert len(all_entities) == 3
    assert alice in all_entities
    assert bob in all_entities
    assert joan in all_entities


def test_repository_creator_basic_delete_by_id(repo):
    alice = Entity(id=1, name="Alice")
    populate_store(repo, alice)

    repo.delete_by_id(1)

    assert repo.find_by_id(1) is None
    assert repo.find_all() == []


@pytest.mark.skip(reason="Not implemented yet")
def test_repository_creator_find_with_and(repo_complex):
    alice = EntityComplex(id=1, name="Alice", posts=10)
    alice2 = EntityComplex(id=2, name="Alice", posts=8)
    bob = EntityComplex(id=3, name="Bob", posts=10)
    alice3 = EntityComplex(id=4, name="Alice", posts=10)
    populate_store(repo_complex, alice, alice2, bob, alice3)

    all_entities = repo_complex.find_all_by_name_and_posts("Alice", 10)

    assert len(all_entities) == 2
    assert alice in all_entities
    assert alice3 in all_entities
    assert alice2 not in all_entities
    assert bob not in all_entities


@pytest.mark.skip(reason="Not implemented yet")
def test_find_with_three_fields_and_or(repo_complex):
    alice = EntityComplex(id=1, name="Alice", posts=10)
    alice2 = EntityComplex(id=2, name="Alice", posts=8)
    bob = EntityComplex(id=3, name="Bob", posts=10)
    charlie = EntityComplex(id=4, name="Charlie", posts=5)
    populate_store(repo_complex, alice, alice2, bob, charlie)

    result = repo_complex.find_all_by_name_or_posts("Alice", 10)

    assert len(result) == 3
    assert alice in result
    assert alice2 in result
    assert bob in result
    assert charlie not in result
