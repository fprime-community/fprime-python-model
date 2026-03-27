from abc import ABC, abstractmethod
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, override
from fprime_python_model.fpp_ast.fpp_ast_node import AstNode, AstId
from fprime_python_model.semantics.symbol import PortSymbol
from fprime_python_model.fpp_ast import fpp_ast
from fprime_python_model.semantics.name import UnqualifiedName


# An FPP port instance signature
@dataclass
class PortInstanceSignature:
    pi: "PortInstance"

    @override
    def __eq__(self, other):
        if isinstance(other, PortInstanceSignature):
            return (
                other.pi.get_direction() == self.pi.get_direction()
                and other.pi.get_array_size() == self.pi.get_array_size()
                and other.pi.get_type() == self.pi.get_type()
                and other.pi.get_unqualified_name() == self.pi.get_unqualified_name()
            )
        return False


class Direction(Enum):
    INPUT = "input"
    OUTPUT = "output"

    def show(dir_opt: Optional["Direction"]) -> str:
        if dir_opt is not None:
            return str(dir_opt)
        else:
            return "none"

    @staticmethod
    def are_compatible(
        dirs: Tuple[Optional["Direction"], Optional["Direction"]],
    ) -> bool:
        in_dir, out_dir = dirs
        if in_dir is not None and out_dir is not None:
            return out_dir == Direction.OUTPUT and in_dir == Direction.INPUT
        return False


class PortInstanceType(ABC):

    def show(type_opt: Optional["PortInstanceType"]) -> str:
        if type_opt is not None:
            return str(type_opt)
        return "none"

    def are_compatible(
        to_1: Optional["PortInstanceType"], to_2: Optional["PortInstanceType"]
    ) -> bool:
        if to_1 is not None:
            return True
        elif to_2 is not None:
            return True
        elif to_1 is None and to_2 is None:
            return to_1 == to_2
        return False


@dataclass
class DefPortPortInstanceType(PortInstanceType):
    symbol: PortSymbol

    def __str__(self) -> str:
        return self.symbol.get_unqualified_name()


@dataclass
class SerialPortInstanceType(PortInstanceType):

    def __str__(self) -> str:
        return "serial"


class PortInstance(ABC):

    def __str__(self):
        return str(self.get_unqualified_name())

    def get_array_size(self) -> int:
        return 1

    def get_direction(self) -> Optional[Direction]:
        return None

    def get_type(self) -> Optional[PortInstanceType]:
        return None

    @abstractmethod
    def get_node(self) -> AstNode:
        pass

    @abstractmethod
    def get_unqualified_name(self) -> UnqualifiedName:
        pass

    @abstractmethod
    def get_import_node_ids(self) -> List[AstId]:
        pass


@dataclass
class GeneralPortInstance(PortInstance):
    a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecPortInstance]]
    specifier: fpp_ast.GeneralPortInstance
    kind: fpp_ast.GeneralKind
    size: int
    ty: PortInstanceType
    import_node_ids: List[AstId] = field(default_factory=list)

    def get_direction(self) -> Optional[Direction]:
        match self.kind:
            case fpp_ast.GeneralKind.OUTPUT:
                return Direction.OUTPUT
            case _:
                return Direction.INPUT

    def get_array_size(self) -> int:
        return self.size

    def get_type(self) -> Optional[PortInstanceType]:
        return self.ty

    def get_node(self) -> AstNode:
        return self.a_node[1]

    def get_unqualified_name(self) -> UnqualifiedName:
        return self.specifier.name

    def get_import_node_ids(self) -> List[AstId]:
        return self.import_node_ids


@dataclass
class SpecialPortInstance(PortInstance):
    a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecPortInstance]]
    specifier: fpp_ast.SpecialPortInstance
    symbol: PortSymbol
    priority: Optional[int]
    queue_full: Optional[fpp_ast.QueueFull]
    import_node_ids: List[AstId] = field(default_factory=list)

    def get_direction(self) -> Optional[Direction]:
        match self.specifier.kind:
            case fpp_ast.SpecialKind.COMMAND_RECV:
                return Direction.INPUT
            case fpp_ast.SpecialKind.PRODUCT_RECV:
                return Direction.INPUT
            case _:
                return Direction.OUTPUT

    def get_type(self):
        return DefPortPortInstanceType(self.symbol)

    def get_node(self) -> AstNode:
        return self.a_node[1]

    def get_unqualified_name(self) -> UnqualifiedName:
        return self.specifier.name

    def get_import_node_ids(self) -> List[AstId]:
        return self.import_node_ids


@dataclass
class InternalPortInstance(PortInstance):
    a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecialPortInstance]]
    priority: Optional[int]
    queue_full: Optional[fpp_ast.QueueFull]

    def get_node(self) -> AstNode:
        return self.a_node[1]

    def get_unqualified_name(self) -> UnqualifiedName:
        return self.a_node[1].data.name

    def get_import_node_ids(self):
        return []


@dataclass
class TopologyPortInstance(PortInstance):
    a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecTopPort]]
    underlying_port: PortInstance

    @override
    def get_direction(self) -> Optional[Direction]:
        return self.underlying_port.get_direction()

    @override
    def get_array_size(self) -> int:
        return self.underlying_port.get_array_size()

    @override
    def get_node(self) -> AstNode:
        return self.a_node[1]

    @override
    def get_type(self) -> Optional[PortInstanceType]:
        return self.underlying_port.get_type()

    @override
    def get_unqualified_name(self) -> UnqualifiedName:
        return self.a_node[1].data.name
    
    @override
    def get_import_node_ids(self):
        return []

    @override
    def __str__(self):
        return f"{str(self.get_unqualified_name())} -> {str(self.underlying_port)}"
