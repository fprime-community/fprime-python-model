from typing import TypeAlias
from dataclasses import dataclass
from fprime_python_model.fpp_ast import fpp_ast
from fprime_python_model.fpp_ast.fpp_ast_node import AstNode
from fprime_python_model.semantics.types_values import Type

RecordId: TypeAlias = int


@dataclass
class Record:
    a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecRecord]]
    record_type: Type
    is_array: bool

    def get_name(self) -> fpp_ast.Ident:
        return self.a_node[1].data.name

    # TODO get loc
