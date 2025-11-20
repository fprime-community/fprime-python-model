from fprime_python_model.fpp_ast.fpp_locations import Location
from fprime_python_model.fpp_ast import fpp_ast
from fprime_python_model.fpp_ast.fpp_ast_node import AstNode, AstId
from fprime_python_model.semantics.symbol import InterfaceSymbol
from fprime_python_model.semantics.name import UnqualifiedName
from fprime_python_model.semantics.port_instance import (
    PortInstance,
    SpecialPortInstance,
)
from dataclasses import dataclass, field
from typing import Dict, Tuple


@dataclass
class Interface:
    a_node: fpp_ast.Annotated[AstNode[fpp_ast.DefInterface]]
    import_map: Dict[InterfaceSymbol, Tuple[AstId, Location]] = field(
        default_factory=dict
    )
    port_map: Dict[UnqualifiedName, PortInstance] = field(default_factory=dict)
    special_port_map: Dict[fpp_ast.SpecialKind, SpecialPortInstance] = field(
        default_factory=dict
    )
