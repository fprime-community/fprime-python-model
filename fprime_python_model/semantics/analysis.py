from dataclasses import dataclass, field
from typing import Optional, Set, List, Dict, Tuple
from fprime_python_model.fpp_ast.fpp_ast_node import AstId
from fprime_python_model.fpp_ast.fpp_ast import Ident, SpecLocKind, SpecLoc
from typing import Any
from fprime_python_model.semantics.symbol import (
    Symbol,
    SymbolInterface,
)
from fprime_python_model.semantics.name import QualifiedName
from fprime_python_model.semantics.scope import Scope
from fprime_python_model.semantics.types_values import Type, Value
from fprime_python_model.semantics.component import Component
from fprime_python_model.semantics.component_instance import ComponentInstance
from fprime_python_model.semantics.topology import Topology
from fprime_python_model.semantics.state_machine import StateMachine
from fprime_python_model.semantics.interface import Interface
from pathlib import Path


@dataclass
class Analysis:
    """The analysis data structure"""

    # The set of files presented to the analyzer
    input_file_set: Set[Path] = field(default_factory=set)

    # The set of files included when parsing input
    included_file_set: Set[Path] = field(default_factory=set)

    # A map from (spec loc kind, qualified name) to spec locs
    location_specifier_map: Dict[Tuple[SpecLocKind, QualifiedName], SpecLoc] = field(
        default_factory=dict
    )

    # Mapping from Ast Ids to their parent symbols
    parent_symbol_map: Dict[AstId, Symbol] = field(default_factory=dict)

    # Mapping from Ast Ids with scopes to their scopes
    symbol_scope_map: Dict[AstId, Scope] = field(default_factory=dict)

    # Mapping from uses (by node ID) to their definitions
    use_def_map: Dict[AstId, Symbol] = field(default_factory=dict)

    # Mapping from types and constant symbols to their types
    type_map: Dict[AstId, Type] = field(default_factory=dict)

    # Mapping from constant symbol and expression AST IDs to their values
    value_map: Dict[AstId, Value] = field(default_factory=dict)

    # Map from component Ast IDs to components
    component_map: Dict[AstId, Component] = field(default_factory=dict)

    # Map from component instance symbol IDs to component instances
    component_instance_map: Dict[AstId, ComponentInstance] = field(default_factory=dict)

    # Map from interface symbol IDs to interfaces
    interface_map: Dict[AstId, Interface] = field(default_factory=dict)

    # Map from topology symbol IDs to topologies
    topology_map: Dict[AstId, Topology] = field(default_factory=dict)

    # Map from state machine symbol IDs to state machines
    state_machine_map: Dict[AstId, StateMachine] = field(default_factory=dict)

    def get_qualified_name_from_map(self, s: SymbolInterface) -> QualifiedName:
        result: List[Ident] = []
        current: Optional[SymbolInterface] = s

        while current is not None:
            result.append(current.get_unqualified_name())
            current = self.parent_symbol_map.get(current.get_node_id())

        result.reverse()
        if not result:
            return QualifiedName([], "")
        else:
            return QualifiedName(result[:-1], result[-1])
