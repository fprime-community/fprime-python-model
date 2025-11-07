from fprime_python_model.fpp_ast import fpp_ast
from fprime_python_model.fpp_ast.fpp_ast_node import AstNode
from dataclasses import dataclass


@dataclass
class InitSpecifier:
    a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecInit]]
    phase: int
