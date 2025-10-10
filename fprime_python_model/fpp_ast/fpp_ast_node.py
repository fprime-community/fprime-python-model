from dataclasses import dataclass
from typing import Generic, TypeVar, ClassVar, TypeAlias

T = TypeVar("T")
AstId: TypeAlias = int


@dataclass(frozen=True)
class AstNode(Generic[T]):
    data: T
    _id: AstId

    # The next identifier
    # Class variable shared amongst all instances of the class
    _next_id: ClassVar[AstId] = 0

    def get_id(self) -> AstId:
        return self._id

    @classmethod
    def create_with_id(cls, data: T, id: AstId) -> "AstNode[T]":
        return cls(data, id)
