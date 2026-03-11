from dataclasses import dataclass
from abc import ABC,abstractmethod
from fprime_python_model.semantics.name import QualifiedName
from fprime_python_model.semantics.port_interface import PortInterface
from fprime_python_model.semantics.port_instance import PortInstance
from fprime_python_model.semantics.component_instance import ComponentInstance
from fprime_python_model.semantics.topology import Topology
from fprime_python_model.fpp_ast.fpp_ast_node import AstNode
from fprime_python_model.fpp_ast import fpp_ast


class InterfaceInstance(ABC):

    @abstractmethod
    def to_string(self) -> str:
        pass

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


@dataclass
class InterfaceComponentInstance(InterfaceInstance):
    ci: ComponentInstance

    def get_qualified_name(self) -> QualifiedName:
        return self.ci.get_qualified_name()

    def get_unqualified_name(self) -> str:
        return self.ci.get_unqualified_name()

    def get_interface(self) -> PortInterface:
        return self.ci.get_interface()


@dataclass
class InterfaceTopology:
    top: Topology

    def get_qualified_name(self) -> QualifiedName:
        return self.top.get_qualified_name()

    def get_unqualified_name(self) -> str:
        return self.top.get_unqualified_name()

    def get_interface(self) -> PortInterface:
        return self.top.port_interface
