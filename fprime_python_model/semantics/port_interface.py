from dataclasses import dataclass, field
from typing import Dict
from fprime_python_model.semantics.name import UnqualifiedName
from fprime_python_model.semantics.port_instance import PortInstance
from fprime_python_model.fpp_ast import fpp_ast
from fprime_python_model.fpp_ast.fpp_ast_node import AstNode


# An FPP Port Interface (set of port instances)
@dataclass
class PortInterface:
    # The type of interface instance this port interface represents
    instance_type: str
    # The map from port names to port instances
    port_map: Dict[UnqualifiedName, PortInstance] = field(default_factory=dict)
    # The map from special port kinds to special port instances
    special_port_map: Dict[fpp_ast.SpecialKind, fpp_ast.SpecialPortInstance] = field(
        default_factory=dict
    )

    def get_port_instance(
        self, name: AstNode[fpp_ast.Ident], interface_name: str
    ) -> PortInstance:
        return self.port_map[name.data]
