from dataclasses import dataclass, field
from typing import Tuple, Set
from fprime_python_model.fpp_ast import fpp_ast
from fprime_python_model.fpp_ast.fpp_ast_node import AstNode
from fprime_python_model.semantics.component_instance import ComponentInstance
from fprime_python_model.fpp_ast.fpp_locations import Location
from fprime_python_model.semantics.port_instance import PortInstance
from fprime_python_model.semantics.name import (
    QualifiedName,
    UnqualifiedName,
    qualified_name_from_ident_list,
)


@dataclass
class PortInstanceIdentifier:
    component_instance: ComponentInstance
    port_instance: PortInstance

    def __str__(self):
        return str(self.get_qualified_name())

    def get_qualified_name(self) -> QualifiedName:
        component_name = self.component_instance.qualified_name
        ident_list = component_name.to_ident_list()
        return qualified_name_from_ident_list(
            ident_list + [self.port_instance.get_unqualified_name()]
        )

    def get_unqualified_name(self) -> QualifiedName:
        component_name = self.component_instance.get_unqualified_name()
        port_name = self.port_instance.get_unqualified_name()
        ident_list = [component_name, port_name]
        return qualified_name_from_ident_list(ident_list)

    def __hash__(self):
        return hash(str(self.get_qualified_name()))
