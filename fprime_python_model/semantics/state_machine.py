from dataclasses import dataclass
from fprime_python_model.semantics.symbol import StateMachineSymbol
from fprime_python_model.fpp_ast import fpp_ast
from fprime_python_model.fpp_ast.fpp_ast_node import AstNode
from fprime_python_model.semantics.state_machine_analysis import StateMachineAnalysis
from fprime_python_model.semantics.state import get_substates
from fprime_python_model.utils.error import InternalError
from fprime_python_model.utils.fpp_ast_visitor import AstVisitor
from enum import Enum
from typing import Set, TypeAlias, List
from typing_extensions import override


class StateMachineKind(Enum):
    EXTERNAL = "external"
    INTERNAL = "internal"


def get_symbol_kind(sym: StateMachineSymbol) -> StateMachineKind:
    if sym.node[1].data.members:
        return StateMachineKind.INTERNAL
    return StateMachineKind.EXTERNAL


@dataclass
class StateMachine:
    a_node: fpp_ast.Annotated[AstNode[fpp_ast.DefStateMachine]]
    sma: StateMachineAnalysis


def get_initial_specifier(sm: fpp_ast.DefStateMachine):
    members = sm.members or []

    specifiers = []

    for member in members:
        pre, inner, post = member.node

        if isinstance(inner, fpp_ast.StateMachineMemberSpecInitialTransition):
            specifiers.append((pre, inner.node, post))

    if len(specifiers) == 1:
        return specifiers[0]

    raise InternalError(
        "state machine must have exactly one initial transition specifier"
    )


def get_actions(state_machine: fpp_ast.DefStateMachine):
    members = state_machine.members or []

    actions = []

    for member in members:
        pre, inner, post = member.node

        if isinstance(inner, fpp_ast.StateMachineMemberDefAction):
            actions.append((pre, inner.node, post))

    return actions


def get_guards(state_machine: fpp_ast.DefStateMachine):
    members = state_machine.members or []

    guards = []

    for member in members:
        pre, inner, post = member.node

        if isinstance(inner, fpp_ast.StateMachineMemberDefGuard):
            guards.append((pre, inner.node, post))

    return guards


def get_signals(state_machine: fpp_ast.DefStateMachine):
    members = state_machine.members or []

    signals = []

    for member in members:
        pre, inner, post = member.node

        if isinstance(inner, fpp_ast.StateMachineMemberDefSignal):
            signals.append((pre, inner.node, post))

    return signals


class GetLeafStates(AstVisitor):

    States: TypeAlias = Set[fpp_ast.Annotated[AstNode[fpp_ast.DefState]]]

    In: TypeAlias = States

    Out: TypeAlias = States

    def default(self, states: States):
        return states

    @override
    def def_state_machine_annotated_node_internal(
        self,
        states: States,
        a_node: fpp_ast.Annotated[AstNode[fpp_ast.DefStateMachine]],
        members: List[fpp_ast.StateMachineMember],
    ):
        for member in members:
            states = self.match_state_machine_member(states, member)
        return states

    @override
    def def_state_annotated_node(
        self, states: States, a_node: fpp_ast.Annotated[AstNode[fpp_ast.DefState]]
    ):
        data = a_node[1].data

        substates = get_substates(data)

        if not substates:
            return states | {a_node}

        members = data.members or []

        for member in members:
            states = self.match_state_member(states, member)

        return states
