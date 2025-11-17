from typing import Optional, TypeAlias
from dataclasses import dataclass
from fprime_python_model.fpp_ast import fpp_ast
from fprime_python_model.fpp_ast.fpp_ast_node import AstNode

ContainerId: TypeAlias = int


@dataclass
class Container:
    """
    An FPP container

    :param a_node: The annotated AST node of the container
    :type a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecContainer]]
    :param default_priority: The default priority of the container
    :type default_priority: Optional[int]
    """

    a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecContainer]]
    default_priority: Optional[int]

    def get_name(self) -> fpp_ast.Ident:
        """
        Gets the name of the container

        :return: Name of the container
        :rtype: fpp_ast.Ident
        """
        return self.a_node[1].data.name

    def get_node(self) -> AstNode[fpp_ast.SpecContainer]:
        """
        Gets the AST node of the container

        :return: AST node of the container
        :rtype: AstNode[fpp_ast.SpecContainer]
        """
        return self.a_node[1]
