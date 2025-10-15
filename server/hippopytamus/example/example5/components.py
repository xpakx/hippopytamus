from hippopytamus.core.annotation import (
        Controller, GetMapping, PostMapping,
        RequestBody, RequestParam, Repository
)
from hippopytamus.data.repository import HippoRepository
from dataclasses import dataclass


@dataclass
class User:
    id: int
    name: str
    password: str


@dataclass
class UserDto:
    name: str
    password: str


@Repository
class UserRepository(HippoRepository[User, int]):
    pass


@Controller
class MyService:
    def __init__(self, repo: UserRepository):
        self.repo = repo
        self._next_id = 1

    @PostMapping("/create")
    def create(self, user: RequestBody(UserDto, required=True)) -> int:
        user_to_save = User(
                id=self._next_id,
                name=user.name,
                password=user.password,
        )
        self._next_id += 1
        saved = self.repo.save(user_to_save)
        return saved.id

    @GetMapping("/read")
    def read(self, id: RequestParam(int, required=True)) -> str:
        user = self.repo.find_by_id(id)
        return user.name if user else ""

    @GetMapping("/readAll")
    def read_all(self) -> list[str]:
        users = self.repo.find_all()
        return [user.name for user in users]
