from typing import Optional, TypeAlias
from dataclasses import dataclass
from fprime_python_model.fpp_ast import fpp_ast
from fprime_python_model.fpp_ast.fpp_ast_node import AstNode

ContainerId: TypeAlias = int


@dataclass
class Container:
    a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecContainer]]
    default_priority: Optional[int]

    def get_name(self) -> fpp_ast.Ident:
        return self.a_node[1].data.name

    def get_node(self) -> AstNode:
        return self.a_node[1]
