from fprime_python_model.fpp_ast import fpp_ast
from fprime_python_model.fpp_ast.fpp_ast_node import AstNode
from dataclasses import dataclass, field
from typing import Optional, Dict, TypeVar


@dataclass
class ComponentInstance:
    """An FPP component instance"""

    a_node: fpp_ast.Annotated[AstNode[fpp_ast.DefComponentInstance]]
    qualified_name: Optional[fpp_ast.Qualified]  # temp optional for testing
    component: None  # should be Component
    base_id: int
    max_id: int
    file: Optional[str]
    queue_size: Optional[int]
    stack_size: Optional[int]
    priority: Optional[int]
    cpu: Optional[int]
    init_specifier_map: Dict[int, None] = field(
        default_factory=dict
    )  # should be from int to init specifier

    def __str__(self) -> str:
        return str(self.qualified_name)

    def get_unqualified_name(self) -> fpp_ast.Ident:
        return self.a_node[1].data.name
