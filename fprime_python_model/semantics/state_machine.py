from dataclasses import dataclass
from fprime_python_model.semantics.symbol import StateMachineSymbol
from fprime_python_model.fpp_ast import fpp_ast
from fprime_python_model.fpp_ast.fpp_ast_node import AstNode
from fprime_python_model.semantics.state_machine_analysis import StateMachineAnalysis
from enum import Enum


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
