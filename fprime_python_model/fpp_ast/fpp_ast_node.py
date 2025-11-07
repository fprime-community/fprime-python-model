from dataclasses import dataclass
from typing import Generic, TypeVar, ClassVar, TypeAlias

T = TypeVar("T")
AstId: TypeAlias = int


@dataclass(frozen=True)
class AstNode(Generic[T]):
    """An AST node with an identifier

    Args:
        Generic (_type_): FPP AST node
    """
    data: T
    _id: AstId

    # The next identifier
    # Class variable shared amongst all instances of the class
    _next_id: ClassVar[AstId] = 0

    def get_id(self) -> AstId:
        """Get node identifier

        Returns:
            AstId: AST node identifier
        """
        return self._id

    @classmethod
    def create_with_id(cls, data: T, id: AstId) -> "AstNode[T]":
        """Creates an AST node with an existing identifier

        Args:
            data (T): AST node data
            id (AstId): AST node identifier

        Returns:
            AstNode[T]: Created AST node
        """
        return cls(data, id)
