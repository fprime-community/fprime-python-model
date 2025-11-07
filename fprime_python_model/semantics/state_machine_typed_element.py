from abc import ABC, abstractmethod
from dataclasses import dataclass
from fprime_python_model.fpp_ast import fpp_ast
from fprime_python_model.fpp_ast.fpp_ast_node import AstNode, AstId


class StateMachineTypedElement(ABC):
    @abstractmethod
    def get_node_id(self) -> AstId:
        pass

    @abstractmethod
    def show_kind(self) -> str:
        pass


@dataclass
class StateEntryTypedElement(StateMachineTypedElement):
    a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecStateEntry]]

    def get_node_id(self) -> AstId:
        return self.a_node[1].get_id()

    def show_kind(self) -> str:
        return "entry actions"
    
    def __hash__(self):
        return hash(self.get_node_id())

@dataclass
class StateExitTypedElement(StateMachineTypedElement):
    a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecStateExit]]

    def get_node_id(self) -> AstId:
        return self.a_node[1].get_id()

    def show_kind(self) -> str:
        return "exit actions"
    
    def __hash__(self):
        return hash(self.get_node_id())

@dataclass
class InitialTransitionTypedElement(StateMachineTypedElement):
    a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecInitialTransition]]

    def get_node_id(self) -> AstId:
        return self.a_node[1].get_id()

    def show_kind(self) -> str:
        return "initial transition"
    
    def __hash__(self):
        return hash(self.get_node_id())

@dataclass
class StateTransitionTypedElement(StateMachineTypedElement):
    a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecStateTransition]]

    def get_node_id(self) -> AstId:
        return self.a_node[1].get_id()

    def show_kind(self) -> str:
        return "state transition"
    
    def __hash__(self):
        return hash(self.get_node_id())

@dataclass
class ChoiceTypedElement(StateMachineTypedElement):
    a_node: fpp_ast.Annotated[AstNode[fpp_ast.DefChoice]]

    def get_node_id(self) -> AstId:
        return self.a_node[1].get_id()

    def show_kind(self) -> str:
        return "choice"

    def __hash__(self):
        return hash(self.get_node_id())
