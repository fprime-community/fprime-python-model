from dataclasses import dataclass
from typing import TypeVar
from semantics.symbol_interface import SymbolInterface
from semantics.generic_scope import GenericScope
from semantics.name_group import NameGroup

Scope = GenericScope[NameGroup, SymbolInterface]

def empty_scope() -> Scope:
    return GenericScope()
