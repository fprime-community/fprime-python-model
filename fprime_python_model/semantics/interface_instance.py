from dataclasses import dataclass
from abc import ABC, abstractmethod
from fprime_python_model.semantics.name import QualifiedName
from fprime_python_model.semantics.port_interface import PortInterface
from fprime_python_model.semantics.port_instance import PortInstance
from fprime_python_model.semantics.component_instance import ComponentInstance
from fprime_python_model.fpp_ast.fpp_ast_node import AstNode
from fprime_python_model.fpp_ast import fpp_ast
from typing import TYPE_CHECKING

# fix circular dependency, ignores import during execution
if TYPE_CHECKING:
    from fprime_python_model.semantics.topology import Topology


class InterfaceInstance(ABC):

    def __str__(self) -> str:
        return str(self.get_qualified_name())

    @abstractmethod
    def get_qualified_name(self) -> QualifiedName:
        pass

    @abstractmethod
    def get_unqualified_name(self) -> str:
        pass

    @abstractmethod
    def get_interface(self) -> PortInterface:
        pass

    def get_port_instance(self, name: AstNode[fpp_ast.Ident]) -> PortInstance:
        return self.get_interface().get_port_instance(name, self.get_unqualified_name())

    def __hash__(self):
        return hash(self.get_qualified_name())


@dataclass
class InterfaceComponentInstance(InterfaceInstance):
    ci: ComponentInstance

    def get_qualified_name(self) -> QualifiedName:
        return self.ci.get_qualified_name()

    def get_unqualified_name(self) -> str:
        return self.ci.get_unqualified_name()

    def get_interface(self) -> PortInterface:
        return self.ci.get_interface()

    def __hash__(self):
        return super().__hash__()


@dataclass
class InterfaceTopology(InterfaceInstance):
    top: "Topology"

    def get_qualified_name(self) -> QualifiedName:
        return self.top.get_qualified_name()

    def get_unqualified_name(self) -> str:
        return self.top.get_unqualified_name()

    def get_interface(self) -> PortInterface:
        return self.top.port_interface

    def __hash__(self):
        return super().__hash__()
