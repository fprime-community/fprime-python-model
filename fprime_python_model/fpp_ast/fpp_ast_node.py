from dataclasses import dataclass, fields
from typing import Generic, TypeVar, ClassVar, TypeAlias

T = TypeVar("T")
AstId: TypeAlias = int


def _freeze(value):
    """Recursively convert lists (and list contents of tuples) to tuples"""
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(item) for item in value)
    return value


class FrozenAstData:
    """Mixin for frozen AST dataclasses that converts list-valued fields to tuples

    AST nodes are immutable value types: freezing them (and tuple-izing their sequence
    fields) makes them hashable as packets of values, so they may be stored in sets and
    used as dictionary keys with value semantics. Dataclasses inheriting this mixin must
    be declared with `@dataclass(frozen=True)`.
    """

    def __post_init__(self):
        for field in fields(self):
            object.__setattr__(self, field.name, _freeze(getattr(self, field.name)))


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
