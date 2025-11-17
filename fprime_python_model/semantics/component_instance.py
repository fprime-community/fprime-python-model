from fprime_python_model.fpp_ast import fpp_ast
from fprime_python_model.fpp_ast.fpp_ast_node import AstNode
from fprime_python_model.semantics.name import QualifiedName
from fprime_python_model.semantics.component import Component
from fprime_python_model.semantics.init_specifier import InitSpecifier
from dataclasses import dataclass, field
from typing import Optional, Dict


@dataclass
class ComponentInstance:
    """
    An FPP component instance

    :param a_node: Annotated component instance AST node
    :type a_node: fpp_ast.Annotated[AstNode[fpp_ast.DefComponentInstance]]
    :param qualified_name: Qualified name of the component instance
    :type qualified_name: QualifiedName
    :param component: Component associated with the component instance
    :type component: Component
    :param base_id: Base ID of the component instance
    :type base_id: int
    :param max_id: Maximum ID of the component instance
    :type max_id: int
    :param file: File that provides the implementation associated with the component instance
    :type file: Optional[str]
    :param queue_size: Queue size
    :type queue_size: Optional[int]
    :param stack_size: Stack size in bytes
    :type stack_size: Optional[int]
    :param priority: Thread priority
    :type priority: Optional[int]
    :param cpu: CPU affinity
    :type cpu: Optional[int]
    :param init_specifier_map: A map from phase to init specifier
    :type init_specifier_map: Dict[int, InitSpecifier]
    """

    a_node: fpp_ast.Annotated[AstNode[fpp_ast.DefComponentInstance]]
    qualified_name: QualifiedName
    component: Component
    base_id: int
    max_id: int
    file: Optional[str]
    queue_size: Optional[int]
    stack_size: Optional[int]
    priority: Optional[int]
    cpu: Optional[int]
    init_specifier_map: Dict[int, InitSpecifier] = field(default_factory=dict)

    def __str__(self) -> str:
        """
        Gets the string representation of the component instance qualified name

        :return: Component instance qualified name string
        :rtype: str
        """
        return str(self.qualified_name)

    def get_unqualified_name(self) -> fpp_ast.Ident:
        """
        Gets the unqualified name of the component instance

        :return: Unqualified name of the component instance
        :rtype: fpp_ast.Ident
        """
        return self.a_node[1].data.name

    def __hash__(self):
        """
        Gets the hash value of the component instance qualified name

        :return: Hash of component instance qualified name
        :rtype: int
        """
        return hash(self.qualified_name)
