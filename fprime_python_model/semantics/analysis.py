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
    """
    The analysis data structure

    :param input_file_set: The set of files presented to the analyzer
    :type input_file_set: Set[Path]
    :param included_file_set: The set of files included when parsing input
    :type included_file_set: Set[Path]
    :param location_specifier_map: A map from (spec loc kind, qualified name) to spec locs
    :type location_specifier_map: Dict[Tuple[SpecLocKind, QualifiedName], SpecLoc]
    :param parent_symbol_map: A map from AST IDs to their parent symbols
    :type parent_symbol_map: Dict[AstId, Symbol]
    :param symbol_scope_map: A map from AST IDs to their scopes
    :type symbol_scope_map: Dict[AstId, Scope]
    :param use_def_map: A map from AST IDs to their definitions
    :type use_def_map: Dict[AstId, Symbol]
    :param type_map: A map from types and constant AST IDs to their types
    :type type_map: Dict[AstId, Type]
    :param value_map: A map from constant symbol and expression AST IDs to their values
    :type value_map: Dict[AstId, Value]
    :param component_map: A map from component AST IDs to components
    :type component_map: Dict[AstId, Component]
    :param component_instance_map: A map from component instance AST IDs to component instances
    :type component_instance_map: Dict[AstId, ComponentInstance]
    :param interface_map: A map from interface AST IDs to interfaces
    :type interface_map: Dict[AstId, Interface]
    :param topology_map: A map from topology AST IDs to topologies
    :type topology_map: Dict[AstId, Topology]
    :param state_machine_map: A map from state machine AST IDs to state machines
    :type state_machine_map: Dict[AstId, StateMachine]
    """

    input_file_set: Set[Path] = field(default_factory=set)
    included_file_set: Set[Path] = field(default_factory=set)
    location_specifier_map: Dict[Tuple[SpecLocKind, QualifiedName], SpecLoc] = field(
        default_factory=dict
    )
    parent_symbol_map: Dict[AstId, Symbol] = field(default_factory=dict)
    symbol_scope_map: Dict[AstId, Scope] = field(default_factory=dict)
    use_def_map: Dict[AstId, Symbol] = field(default_factory=dict)
    type_map: Dict[AstId, Type] = field(default_factory=dict)
    value_map: Dict[AstId, Value] = field(default_factory=dict)
    component_map: Dict[AstId, Component] = field(default_factory=dict)
    component_instance_map: Dict[AstId, ComponentInstance] = field(default_factory=dict)
    interface_map: Dict[AstId, Interface] = field(default_factory=dict)
    topology_map: Dict[AstId, Topology] = field(default_factory=dict)
    state_machine_map: Dict[AstId, StateMachine] = field(default_factory=dict)

    def get_qualified_name_from_map(self, s: SymbolInterface) -> QualifiedName:
        """
        Gets the qualified name of a symbol
        :param s: Symbol to get the qualified name of
        :type s: SymbolInterface
        :return: Qualified name of the symbol
        :rtype: QualifiedName
        """
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
