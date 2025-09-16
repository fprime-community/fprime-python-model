from fprime_python_model.semantics.symbol import StateMachineSymbol
from enum import Enum


class StateMachineKind(Enum):
    EXTERNAL = "external"
    INTERNAL = "internal"


def get_symbol_kind(sym: StateMachineSymbol) -> StateMachineKind:
    if sym.node[1].data.members:
        return StateMachineKind.INTERNAL
    return StateMachineKind.EXTERNAL
