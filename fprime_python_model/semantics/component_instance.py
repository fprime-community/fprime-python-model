from fprime_python_model.fpp_ast import fpp_ast
from fprime_python_model.fpp_ast.fpp_ast_node import AstNode
from fprime_python_model.semantics.name import QualifiedName
from fprime_python_model.semantics.component import Component
from fprime_python_model.semantics.init_specifier import InitSpecifier
from dataclasses import dataclass, field
from typing import Optional, Dict, TypeVar


@dataclass
class ComponentInstance:
    """An FPP component instance"""

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
        return str(self.qualified_name)

    def get_unqualified_name(self) -> fpp_ast.Ident:
        return self.a_node[1].data.name

    def __hash__(self):
        return hash(self.qualified_name)
