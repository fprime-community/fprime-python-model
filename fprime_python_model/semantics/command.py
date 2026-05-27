from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, TypeAlias
from typing_extensions import override
from fprime_python_model.fpp_ast.fpp_ast_node import AstNode
from fprime_python_model.fpp_ast import fpp_ast

CommandOpcode: TypeAlias = int


class Command(ABC):
    """
    An FPP command
    """

    @abstractmethod
    def get_name(self) -> str:
        """
        Gets the name of the command

        :return: The name of the command
        :rtype: str
        """
        pass

    @abstractmethod
    def get_node(self) -> AstNode:
        """
        Gets the AST node associated with the command

        :return: The AST node associated with the command
        :rtype: AstNode
        """
        pass


class NonParamKind(ABC):
    pass


@dataclass
class NonParamKindAsync(NonParamKind):
    """
    Async non-parameter command kind

    :param priority: Command priority
    :type priority: Optional[int]
    :param queue_full: Command queue full behavior
    :type queue_full: fpp_ast.QueueFull
    """

    priority: Optional[int]
    queue_full: fpp_ast.QueueFull


@dataclass
class NonParamKindGuarded(NonParamKind):
    """
    Quarded non-parameter command kind
    """

    pass


@dataclass
class NonParamKindSync(NonParamKind):
    """
    Sync non-parameter command kind
    """

    pass


class ParamKind(ABC):
    """
    Parameter command kind
    """

    pass


@dataclass
class ParamKindSave(ParamKind):
    """
    Parameter save command kind
    """

    pass


@dataclass
class ParamKindSet(ParamKind):
    """
    Parameter set command kind
    """

    pass


@dataclass
class CommandNonParam(Command):
    """
    A non-parameter command

    :param a_node: Annotated command AST node
    :type a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecCommand]]
    :param kind: Non-parameter command kind
    :type kind: NonParamKind
    """

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
    """
    A parameter command

    :param a_node: Annotated parameter specifier AST node
    :type a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecParam]]
    :param kind:Parameter command kind
    :type kind: ParamKind
    """

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
