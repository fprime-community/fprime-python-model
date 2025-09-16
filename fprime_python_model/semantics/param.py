from typing import Optional, TypeAlias
from dataclasses import dataclass
from fprime_python_model.fpp_ast import fpp_ast
from fprime_python_model.fpp_ast.fpp_ast_node import AstNode
from fprime_python_model.semantics.types_values import Type, Value

ParamId: TypeAlias = int


@dataclass
class Param:
    a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecParam]]
    param_type: Type
    default: Optional[Value]
    set_opcode: int
    save_opcode: int
    is_external: bool

    def get_name(self) -> fpp_ast.Ident:
        return self.a_node[1].data.name

    # TODO get loc
