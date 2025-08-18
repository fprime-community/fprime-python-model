from dataclasses import dataclass
from typing import Generic, TypeVar, ClassVar, TypeAlias

T = TypeVar('T')
AstId: TypeAlias = int

@dataclass(frozen=True)
class AstNode(Generic[T]):
    data: T
    _id: AstId

    # The next identifier
    # Class variable shared amongst all instances of the class
    _next_id: ClassVar[AstId] = 0

    @classmethod
    def get_id(cls) -> AstId:
        id0 = cls._next_id
        cls._next_id = id0 + 1
        return id0

    @classmethod
    def create(cls, data: T) -> 'AstNode[T]':
        return cls(data, cls.get_id())
    
    @classmethod
    def create_with_id(cls, data: T, id: AstId) -> 'AstNode[T]':
        return cls(data, id)
