from typing import Optional, TypeAlias
from dataclasses import dataclass
from fprime_python_model.fpp_ast import fpp_ast
from fprime_python_model.fpp_ast.fpp_ast_node import AstNode
from fprime_python_model.semantics.format import Format

EventId: TypeAlias = int


@dataclass
class Event:
    """
    An FPP event

    :param a_node: Annotated event AST node
    :type a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecEvent]]
    :param format: Event format
    :type format: Format
    :param throttle: Event throttle
    :type throttle: Optional[int]
    """

    a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecEvent]]
    format: Format
    throttle: Optional[int]

    def get_name(self) -> fpp_ast.Ident:
        """
        Gets the name of the event

        :return: Name of the event
        :rtype: fpp_ast.Ident
        """
        return self.a_node[1].data.name

    def get_node(self) -> AstNode[fpp_ast.SpecEvent]:
        """
        Gets the AST node of the event

        :return: AST node of the event
        :rtype: AstNode[fpp_ast.SpecEvent]
        """
        return self.a_node[1]
