from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple, Optional, Iterable
from fprime_python_model.fpp_ast import fpp_ast
from fprime_python_model.fpp_ast.fpp_ast_node import AstNode, AstId
from fprime_python_model.fpp_ast.fpp_locations import Location
from fprime_python_model.semantics.component_instance import ComponentInstance
from fprime_python_model.semantics.connection_pattern import ConnectionPattern
from fprime_python_model.semantics.name import UnqualifiedName, QualifiedName
from fprime_python_model.semantics.connection import Connection
from fprime_python_model.semantics.port_instance_identifier import (
    PortInstanceIdentifier,
)
from fprime_python_model.semantics.port_instance import PortInstance, Direction
from fprime_python_model.semantics.interface_instance import (
    InterfaceInstance,
    InterfaceComponentInstance,
)
from fprime_python_model.semantics.port_interface import PortInterface
from fprime_python_model.semantics.topology_port import TopologyPort

@dataclass
class Topology:
    a_node: fpp_ast.Annotated[AstNode[fpp_ast.DefTopology]]
    qualified_name: QualifiedName
    direct_topologies: Dict[AstId, Location] = field(default_factory=dict)
    direct_component_instances: Dict[AstId, Location] = field(default_factory=dict)
    transitive_import_set: Set[AstId] = field(default_factory=set)
    instance_map: Dict[InterfaceInstance, Location] = field(default_factory=dict)
    port_map: Dict[UnqualifiedName, TopologyPort] = field(
        default_factory=dict
    )
    port_interface: PortInterface = field(
        default_factory=lambda: PortInterface("topology")
    )
    pattern_map: Dict[fpp_ast.PatternKind, ConnectionPattern] = field(
        default_factory=dict
    )
    connection_map: Dict[UnqualifiedName, List[Connection]] = field(
        default_factory=dict
    )
    local_connection_map: Dict[UnqualifiedName, List[Connection]] = field(
        default_factory=dict
    )
    output_connection_map: Dict[PortInstanceIdentifier, Set[Connection]] = field(
        default_factory=dict
    )
    input_connection_map: Dict[PortInstanceIdentifier, Set[Connection]] = field(
        default_factory=dict
    )
    from_port_number_map: Dict[Connection, int] = field(default_factory=dict)
    to_port_number_map: Dict[Connection, int] = field(default_factory=dict)
    unconnected_port_set: Set[PortInstanceIdentifier] = field(default_factory=set)

    def get_name(self) -> fpp_ast.Ident:
        return self.a_node[1].data.name

    def get_unqualified_name(self) -> fpp_ast.Ident:
        return self.a_node[1].data.name

    def get_port_number(self, pi: PortInstance, c: Connection) -> Optional[int]:
        if pi.get_direction() == Direction.INPUT:
            return self.to_port_number_map.get(c)
        else:
            return self.from_port_number_map.get(c)

    def connection_exists_between(
        self, from_pii: PortInstanceIdentifier, to_pii: PortInstanceIdentifier
    ) -> bool:
        return len(self.get_connections_between(from_pii, to_pii)) > 0

    def get_connections_between(
        self, from_pii: PortInstanceIdentifier, to_pii: PortInstanceIdentifier
    ) -> Set[Connection]:
        return {
            c
            for c in self.get_connections_from(from_pii)
            if c.to_endpoint.port == to_pii
        }

    def get_connections_from(self, from_pii: PortInstanceIdentifier) -> Set[Connection]:
        return self.output_connection_map.get(from_pii, set())

    def get_connections_to(self, to_pii: PortInstanceIdentifier) -> Set[Connection]:
        return self.input_connection_map.get(to_pii, set())

    def get_connections_at(self, pii: PortInstanceIdentifier) -> Set[Connection]:
        pi = pii.port_instance
        if pi.get_direction() == Direction.INPUT:
            return self.input_connection_map.get(pii, set())
        elif pi.get_direction() == Direction.OUTPUT:
            return self.output_connection_map.get(pii, set())
        else:
            return set()

    def get_used_port_numbers(
        self, pi: PortInstance, cs: Iterable[Connection]
    ) -> Set[int]:
        out_set = set()
        for c in cs:
            pn = self.get_port_number(pi, c)
            if pn is not None:
                out_set.add(pn)
        return out_set

    def get_qualified_name(self) -> QualifiedName:
        return self.qualified_name

    def component_instance_map(self) -> Dict[ComponentInstance, Location]:
        out_dict: Dict[ComponentInstance, Location] = dict()
        for inst, loc in self.instance_map.items():
            if isinstance(inst, InterfaceComponentInstance):
                out_dict[inst.ci] = loc
        return out_dict
