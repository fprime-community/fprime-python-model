from typing import TypeAlias, List
from dataclasses import dataclass
from fprime_python_model.fpp_ast import fpp_ast
from fprime_python_model.utils.error import InternalError

UnqualifiedName: TypeAlias = str


@dataclass
class QualifiedName:
    qualifier: List[UnqualifiedName]
    base: UnqualifiedName

    def __str__(self):
        return ".".join(self.qualifier + [self.base])

    def __hash__(self):
        return hash(self.__str__())

    def to_ident_list(self) -> List[UnqualifiedName]:
        return self.qualifier + [self.base]


def qualified_name_from_ident_list(il: List[fpp_ast.Ident]) -> QualifiedName:
    if not il:
        raise InternalError("empty identifier list")

    return QualifiedName(il[:-1], il[-1])
