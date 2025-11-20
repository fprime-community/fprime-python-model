from dataclasses import dataclass
from typing import Tuple, Set
from fprime_python_model.fpp_ast import fpp_ast
from fprime_python_model.fpp_ast.fpp_ast_node import AstNode
from fprime_python_model.semantics.component_instance import ComponentInstance
from fprime_python_model.fpp_ast.fpp_locations import Location


@dataclass
class ConnectionPattern:
    """
    An FPP connection pattern

    :param a_node: The annotated AST node specifying the pattern
    :type a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecConnectionPattern]]
    :param ast: The AST pattern
    :type ast: fpp_ast.Pattern
    :param source: The source component instance and location
    :type source: Tuple[ComponentInstance, Location]
    :param targets: The set of target component instances and locations
    :type targets: Set[Tuple[ComponentInstance, Location]]
    """

    a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecConnectionGraph]]
    ast: fpp_ast.Pattern
    source: Tuple[ComponentInstance, Location]
    targets: Set[Tuple[ComponentInstance, Location]]
