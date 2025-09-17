from abc import ABC, abstractmethod
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, override, TypeAlias
from fprime_python_model.fpp_ast.fpp_ast_node import AstNode, AstId
from fprime_python_model.fpp_ast import fpp_ast
from fprime_python_model.fpp_ast.fpp_locations import Location

CommandOpcode: TypeAlias = int


class Command(ABC):

    @abstractmethod
    def get_name(self) -> str:
        pass

    @abstractmethod
    def get_node(self) -> AstNode:
        pass


class NonParamKind(ABC):
    pass


@dataclass
class NonParamKindAsync(NonParamKind):
    priority: Optional[int]
    queue_full: fpp_ast.QueueFull


@dataclass
class NonParamKindGuarded(NonParamKind):
    pass


@dataclass
class NonParamKindSync(NonParamKind):
    pass


class ParamKind(ABC):
    pass


@dataclass
class ParamKindSave(ParamKind):
    pass


@dataclass
class ParamKindSet(ParamKind):
    pass


@dataclass
class CommandNonParam(Command):
    a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecCommand]]
    kind: NonParamKind

    @override
    def get_name(self) -> str:
        return self.a_node[1].data.name

    @override
    def get_node(self) -> AstNode:
        return self.a_node[1]


@dataclass
class CommandParam(Command):
    a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecParam]]
    kind: ParamKind

    @override
    def get_name(self):
        param_name = self.a_node[1].data.name.upper()
        if isinstance(self.kind, ParamKindSave):
            return f"{param_name}_PRM_SAVE"
        else:
            return f"{param_name}_PRM_SET"

    @override
    def get_node(self) -> AstNode:
        return self.a_node[1]
