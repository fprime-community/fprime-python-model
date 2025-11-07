from dataclasses import dataclass, field
from typing import Tuple, Set
from fprime_python_model.fpp_ast import fpp_ast
from fprime_python_model.fpp_ast.fpp_ast_node import AstNode
from fprime_python_model.semantics.component_instance import ComponentInstance
from fprime_python_model.fpp_ast.fpp_locations import Location


@dataclass
class ConnectionPattern:
    a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecConnectionGraph]]
    ast: fpp_ast.Pattern
    source: Tuple[ComponentInstance, Location]
    targets: Set[Tuple[ComponentInstance, Location]]
