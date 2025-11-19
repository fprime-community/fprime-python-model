from fprime_python_model.semantics.symbol_interface import SymbolInterface
from fprime_python_model.semantics.generic_scope import GenericScope
from fprime_python_model.semantics.name_group import NameGroup

Scope = GenericScope[NameGroup, SymbolInterface]


def empty_scope() -> Scope:
    return GenericScope()
