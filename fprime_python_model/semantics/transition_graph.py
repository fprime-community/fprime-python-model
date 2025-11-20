from dataclasses import dataclass, field
from typing import Optional, Dict, Set
from abc import ABC, abstractmethod
from fprime_python_model.semantics.state_machine_symbol import (
    StateSymbol,
    ChoiceSymbol,
)
from fprime_python_model.fpp_ast import fpp_ast
from fprime_python_model.fpp_ast.fpp_ast_node import AstNode
from fprime_python_model.semantics.state_or_junction import StateOrChoice, State, Choice
from fprime_python_model.semantics.state_machine_typed_element import (
    StateMachineTypedElement,
    InitialTransitionTypedElement,
    StateTransitionTypedElement,
    ChoiceTypedElement,
)
from fprime_python_model.fpp_ast.fpp_locations import Location


@dataclass
class TransitionGraphNode:
    soc: StateOrChoice


class Arc(ABC):

    @abstractmethod
    def get_start_node(self) -> TransitionGraphNode:
        pass

    @abstractmethod
    def get_end_node(self) -> TransitionGraphNode:
        pass

    @abstractmethod
    def get_typed_element(self) -> StateMachineTypedElement:
        pass

    @abstractmethod
    def show_kind(self) -> str:
        pass

    @abstractmethod
    def show_transition(self, loc: Location) -> str:
        pass


@dataclass
class InitialArc(Arc):
    start_state: StateSymbol
    a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecInitialTransition]]
    end_node: TransitionGraphNode

    def get_start_node(self) -> TransitionGraphNode:
        return TransitionGraphNode(State(self.start_state))

    def get_end_node(self) -> TransitionGraphNode:
        return self.end_node

    def get_typed_element(self):
        return InitialTransitionTypedElement(self.a_node)

    def show_kind(self) -> str:
        return "initial transition"

    def show_transition(self, loc: Location) -> str:
        end_name = self.end_node.soc.get_name()
        return f"{self.show_kind()} at {str(loc.path)}:{loc.pos} to {end_name}"

    def __hash__(self):
        return hash(
            (
                self.start_state.get_node_id(),
                self.a_node[1].get_id(),
                self.end_node.soc.get_symbol().get_node_id(),
            )
        )


@dataclass
class StateArc(Arc):
    start_state: StateSymbol
    a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecStateTransition]]
    end_node: TransitionGraphNode

    def get_start_node(self) -> TransitionGraphNode:
        return TransitionGraphNode(State(self.start_state))

    def get_end_node(self):
        return self.end_node

    def get_typed_element(self):
        return StateTransitionTypedElement(self.a_node)

    def show_kind(self) -> str:
        return "state transition"

    def show_transition(self, loc: Location) -> str:
        end_name = self.end_node.soc.get_name()
        return f"{self.show_kind()} at {str(loc.path)}:{loc.pos} to {end_name}"

    def __hash__(self):
        return hash(
            (
                self.start_state.get_node_id(),
                self.a_node[1].get_id(),
                self.end_node.soc.get_symbol().get_node_id(),
            )
        )


@dataclass
class ChoiceArc(Arc):
    start_choice: ChoiceSymbol
    a_node: AstNode[fpp_ast.TransitionExpr]
    end_node: TransitionGraphNode

    def get_start_node(self) -> TransitionGraphNode:
        return TransitionGraphNode(Choice(self.start_choice))

    def get_end_node(self):
        return self.end_node

    def get_typed_element(self):
        return ChoiceTypedElement(self.start_choice.node)

    def show_kind(self) -> str:
        return "choice transition"

    def show_transition(self, loc: Location) -> str:
        end_name = self.end_node.soc.get_name()
        return f"{self.show_kind()} at {str(loc.path)}:{loc.pos} to {end_name}"

    def __hash__(self):
        return hash(
            (
                self.start_choice.get_node_id(),
                self.a_node.get_id(),
                self.end_node.soc.get_symbol().get_node_id(),
            )
        )


ArcMap = Dict[str, Set[Arc]]  # temporary string key, should be symbol ID


@dataclass
class TransitionGraph:
    initial_node: Optional[TransitionGraphNode] = None
    arc_map: ArcMap = field(default_factory=dict)
