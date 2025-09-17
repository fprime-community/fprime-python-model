from dataclasses import dataclass, field
from typing import Optional, Set, List, Dict, Tuple
from fprime_python_model.fpp_ast.fpp_ast_node import AstId
from typing import Any
from fprime_python_model.semantics.symbol import (
    Symbol,
    ComponentSymbol,
    ComponentInstanceSymbol,
    StateMachineSymbol,
    ConstantSymbol,
    TopologySymbol,
)
from fprime_python_model.semantics.scope import Scope
from fprime_python_model.semantics.types_values import Type, Value
from fprime_python_model.semantics.component import Component
from pathlib import Path


@dataclass
class Analysis:
    """The analysis data structure"""

    # The set of files presented to the analyzer
    input_file_set: Set[Path] = field(default_factory=set)

    # The set of files included when parsing input
    included_file_set: Set[Path] = field(default_factory=set)

    # A map from (spec loc kind, qualified name) to spec locs
    location_specifier_map: Dict[Tuple[Any, Any], Any] = field(default_factory=dict)

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

    # Map from component instance symbols to component instances
    component_instance_map: Dict[ComponentInstanceSymbol, Any] = field(
        default_factory=dict
    )

    # # Map from interface symbols to interfaces
    # Not in fpp-to-json analysis output
    # interface_map: Dict[InterfaceSymbol, Any] = field(default_factory=dict)

    # Map from topology symbols to topologies
    topology_map: Dict[TopologySymbol, Any] = field(default_factory=dict)

    # Map from state machine symbols to state machines
    state_machine_map: Dict[StateMachineSymbol, Any] = field(default_factory=dict)
