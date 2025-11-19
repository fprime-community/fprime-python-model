from fprime_python_model.semantics.state_machine_symbol import (
    StateMachineSymbolInterface,
)
from fprime_python_model.semantics.generic_scope import GenericScope
from fprime_python_model.semantics.state_machine_name_group import StateMachineNameGroup

StateMachineScope = GenericScope[StateMachineNameGroup, StateMachineSymbolInterface]


def empty_scope() -> StateMachineScope:
    return GenericScope()
