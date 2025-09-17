from typing import Optional, TypeAlias
from dataclasses import dataclass
from fprime_python_model.fpp_ast import fpp_ast
from fprime_python_model.fpp_ast.fpp_ast_node import AstNode
from fprime_python_model.semantics.format import Format

EventId: TypeAlias = int


@dataclass
class Event:
    a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecEvent]]
    format: Format
    throttle: Optional[int]

    def get_name(self) -> fpp_ast.Ident:
        return self.a_node[1].data.name

    def get_node(self) -> AstNode:
        return self.a_node[1]
