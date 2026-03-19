from fprime_python_model.fpp_ast.fpp_locations import Location
from fprime_python_model.fpp_ast import fpp_ast
from fprime_python_model.fpp_ast.fpp_ast_node import AstNode, AstId
from fprime_python_model.semantics.symbol import InterfaceSymbol
from fprime_python_model.semantics.name import UnqualifiedName
from fprime_python_model.semantics.port_instance import (
    PortInstance,
    SpecialPortInstance,
)
from fprime_python_model.semantics.port_interface import PortInterface
from dataclasses import dataclass, field
from typing import Dict, Tuple


# An FPP interface
@dataclass
class Interface:
    # The AST node defining the interface
    a_node: fpp_ast.Annotated[AstNode[fpp_ast.DefInterface]]
    # The imported interfaces
    import_map: Dict[InterfaceSymbol, Tuple[AstId, Location]] = field(
        default_factory=dict
    )
    # The port interface of the component
    port_interface: PortInterface = field(
        default_factory=lambda: PortInterface("interface")
    )
