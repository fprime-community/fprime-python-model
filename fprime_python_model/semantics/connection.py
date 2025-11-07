from dataclasses import dataclass, field
from typing import Tuple, Set, Optional
from fprime_python_model.fpp_ast import fpp_ast
from fprime_python_model.fpp_ast.fpp_ast_node import AstNode
from fprime_python_model.semantics.component_instance import ComponentInstance
from fprime_python_model.fpp_ast.fpp_locations import Location
from fprime_python_model.semantics.port_instance_identifier import (
    PortInstanceIdentifier,
)
from fprime_python_model.semantics.port_instance import PortInstance, Direction


@dataclass
class Endpoint:
    loc: Location
    port: PortInstanceIdentifier
    port_number: Optional[int] = None

    def __str__(self):
        if self.port_number is not None:
            return f"{str(self.port)}[{self.port_number}]"
        else:
            return f"{str(self.port)}"


@dataclass
class Connection:
    from_endpoint: Endpoint
    to_endpoint: Endpoint
    is_unmatched: bool = False

    def __str__(self):
        return f"{str(self.from_endpoint)} -> {str(self.to_endpoint)}"

    def __hash__(self):
        return hash(self.__str__())
