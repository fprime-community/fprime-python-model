from abc import ABC, abstractmethod
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, TypeVar
from fprime_python_model.fpp_ast.fpp_ast_node import AstNode, AstId
from fprime_python_model.semantics.symbol import PortSymbol
from fprime_python_model.fpp_ast import fpp_ast


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
        return "temp"


@dataclass
class SerialPortInstanceType(PortInstanceType):

    def __str__(self) -> str:
        return "serial"


class PortInstance(ABC):

    def __str__(self):
        return str(self.get_unqualified_name)

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
    def get_node_id(self) -> AstId:
        pass

    @abstractmethod
    def get_unqualified_name(self) -> fpp_ast.Unqualified:
        pass


@dataclass
class GeneralPortInstance(PortInstance):
    a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecPortInstance]]
    specifier: fpp_ast.GeneralPortInstance
    kind: fpp_ast.GeneralKind
    size: Optional[int]
    ty: PortInstanceType
    import_node_ids: List[AstId] = field(default_factory=list)

    def get_node(self) -> AstNode:
        return self.a_node[1]

    def get_node_id(self) -> AstId:
        return self.a_node[1]._id

    def get_unqualified_name(self) -> fpp_ast.Unqualified:
        return fpp_ast.Unqualified(self.specifier.name)


@dataclass
class SpecialPortInstance(PortInstance):
    a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecPortInstance]]
    specifier: fpp_ast.SpecialPortInstance
    symbol: PortSymbol
    priority: Optional[int]
    queue_full: Optional[fpp_ast.QueueFull]
    import_node_ids: List[AstId] = field(default_factory=list)

    def get_node(self) -> AstNode:
        return self.a_node[1]

    def get_node_id(self) -> AstId:
        return self.a_node[1]._id

    def get_unqualified_name(self) -> fpp_ast.Unqualified:
        return fpp_ast.Unqualified(self.specifier.name)


@dataclass
class InternalPortInstance(PortInstance):
    a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecialPortInstance]]
    priority: Optional[int]
    queue_full: Optional[fpp_ast.QueueFull]

    def get_node(self) -> AstNode:
        return self.a_node[1]

    def get_node_id(self) -> AstId:
        return self.a_node[1]._id

    def get_unqualified_name(self) -> fpp_ast.Unqualified:
        return fpp_ast.Unqualified(self.a_node[1].data.name)
