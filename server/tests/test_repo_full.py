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


def test_repo_has_store(repo):
    assert hasattr(repo, "_store")


def test_repository_creator_basic_save(repo):
    entity = Entity(id=1, name="Alice")
    saved = repo.save(entity)
    assert saved is entity
    assert repo._store[1] == entity


def test_repository_creator_basic_find_by_id(repo):
    alice = Entity(id=1, name="Alice")
    repo._store = {1: alice}
    found = repo.find_by_id(1)
    assert found == alice


def test_repository_creator_basic_find_all(repo):
    alice = Entity(id=1, name="Alice")
    bob = Entity(id=2, name="Bob")
    joan = Entity(id=3, name="Joan")
    repo._store = {
            1: alice,
            2: bob,
            3: joan,
    }
    all_entities = repo.find_all()
    assert len(all_entities) == 3
    assert alice in all_entities
    assert bob in all_entities
    assert joan in all_entities


def test_repository_creator_basic_delete_by_id(repo):
    alice = Entity(id=1, name="Alice")
    repo._store = {1: alice}
    repo.delete_by_id(1)
    assert repo.find_by_id(1) is None
    assert repo.find_all() == []
