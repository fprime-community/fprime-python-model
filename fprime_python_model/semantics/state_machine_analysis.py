from dataclasses import dataclass, field
from typing import Dict, Optional
from fprime_python_model.semantics.symbol import StateMachineSymbol
from fprime_python_model.fpp_ast import fpp_ast
from fprime_python_model.fpp_ast.fpp_ast_node import AstNode, AstId
from fprime_python_model.semantics.transition_graph import TransitionGraph
from fprime_python_model.semantics.state_machine_symbol import (
    StateMachineSymbolInterface,
    SignalSymbol,
    StateSymbol,
    ActionSymbol,
    GuardSymbol,
    ChoiceSymbol,
)
from fprime_python_model.semantics.transition import Transition, GuardedTransition
from fprime_python_model.semantics.state_machine_scope import StateMachineScope
from fprime_python_model.semantics.state_machine_typed_element import (
    StateMachineTypedElement,
)
from fprime_python_model.semantics.types_values import Type
from fprime_python_model.semantics.state_or_junction import StateOrChoice, State, Choice
from fprime_python_model.utils.error import InternalError

SignalTransitionMap = Dict[AstId, GuardedTransition]
StateTransitionMap = Dict[AstId, GuardedTransition]
SignalStateTransitionMap = Dict[AstId, StateTransitionMap]
TransitionExprMap = Dict[AstId, Transition]


@dataclass
class StateMachineAnalysis:
    symbol: StateMachineSymbol
    symbol_scope_map: Dict[AstId, StateMachineScope] = field(default_factory=dict)
    use_def_map: Dict[AstId, StateMachineSymbolInterface] = field(default_factory=dict)
    transition_graph: TransitionGraph = field(default_factory=TransitionGraph)
    reverse_transition_graph: TransitionGraph = field(default_factory=TransitionGraph)
    type_option_map: Dict[StateMachineTypedElement, Optional[Type]] = field(
        default_factory=dict
    )
    flattened_state_transition_map: SignalStateTransitionMap = field(
        default_factory=dict
    )
    flattened_choice_transition_map: TransitionExprMap = field(default_factory=dict)

    def get_state_symbol(self, state: AstNode[fpp_ast.QualIdent]) -> StateSymbol:
        sym = self.use_def_map[state.get_id()]
        if not isinstance(sym, StateSymbol):
            raise TypeError(f"Expected StateSymbol, got {type(sym).__name__}")
        return sym

    def get_action_symbol(self, state: AstNode[fpp_ast.QualIdent]) -> ActionSymbol:
        sym = self.use_def_map[state.get_id()]
        if not isinstance(sym, ActionSymbol):
            raise TypeError(f"Expected ActionSymbol, got {type(sym).__name__}")
        return sym

    def get_guard_symbol(self, state: AstNode[fpp_ast.QualIdent]) -> GuardSymbol:
        sym = self.use_def_map[state.get_id()]
        if not isinstance(sym, GuardSymbol):
            raise TypeError(f"Expected GuardSymbol, got {type(sym).__name__}")
        return sym

    def get_signal_symbol(self, state: AstNode[fpp_ast.QualIdent]) -> SignalSymbol:
        sym = self.use_def_map[state.get_id()]
        if not isinstance(sym, SignalSymbol):
            raise TypeError(f"Expected SignalSymbol, got {type(sym).__name__}")
        return sym

    def get_state_or_choice(self, soc: AstNode[fpp_ast.QualIdent]) -> StateOrChoice:
        maybe_soc = self.use_def_map.get(soc.get_id())
        if isinstance(maybe_soc, StateSymbol):
            return State(maybe_soc)
        elif isinstance(maybe_soc, ChoiceSymbol):
            return Choice(maybe_soc)
        else:
            raise InternalError("expected state or choice")
