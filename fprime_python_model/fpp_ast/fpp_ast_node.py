from dataclasses import dataclass
from typing import Generic, TypeVar, ClassVar, TypeAlias

T = TypeVar("T")
AstId: TypeAlias = int


@dataclass(frozen=True)
class AstNode(Generic[T]):
    """
    An AST node with an identifier

    :param T: The type of the FPP AST node represented by this instance.
    """

    data: T
    _id: AstId

    # The next identifier
    # Class variable shared amongst all instances of the class
    _next_id: ClassVar[AstId] = 0

    def get_id(self) -> AstId:
        """
        Returns the identifier associated with this AST node.

        :returns: The unique identifier of the AST node.
        :rtype: AstId
        """
        return self._id

    @classmethod
    def create_with_id(cls, data: T, id: AstId) -> "AstNode[T]":
        """
        Creates an AST node with an existing identifier

        :param data: AST node data
        :type data: T
        :param id: AST node identifier
        :type id: AstId
        :returns: The AST node that was created
        :rtype: AstNode[T]
        """
        return cls(data, id)
