from dataclasses import dataclass, field
from typing import Dict, List
from fprime_python_model.fpp_ast.fpp_ast_node import AstNode
from fprime_python_model.fpp_ast import fpp_ast
from fprime_python_model.semantics.port_instance import (
    PortInstance,
    SpecialPortInstance,
    GeneralPortInstance,
)
from fprime_python_model.semantics.command import Command, CommandOpcode
from fprime_python_model.semantics.tlm_channel import TlmChannel, TlmChannelId
from fprime_python_model.semantics.event import Event, EventId
from fprime_python_model.semantics.param import Param, ParamId
from fprime_python_model.semantics.container import Container, ContainerId
from fprime_python_model.semantics.record import Record, RecordId
from fprime_python_model.semantics.state_machine_instance import StateMachineInstance
from fprime_python_model.semantics.state_machine import StateMachineKind
from fprime_python_model.semantics.name import UnqualifiedName


@dataclass
class PortMatching:
    a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecPortMatching]]
    instance1: GeneralPortInstance
    instance2: GeneralPortInstance

    def __str__(self):
        return f"match {str(self.instance1)} with {str(self.instance2)}"


@dataclass
class Component:
    # The AST node defining the component
    a_node: fpp_ast.Annotated[AstNode[fpp_ast.DefComponent]]
    # The map from port names to port instances
    port_map: Dict[UnqualifiedName, PortInstance] = field(default_factory=dict)
    # The map from special port kinds to special port instances
    special_port_map: Dict[fpp_ast.SpecialKind, SpecialPortInstance] = field(
        default_factory=dict
    )
    # The map from command opcodes to commands
    command_map: Dict[CommandOpcode, Command] = field(default_factory=dict)
    # The map from telemetry channel IDs to channels
    tlm_channel_map: Dict[TlmChannelId, TlmChannel] = field(default_factory=dict)
    # The map from telemetry channel names to channels
    tlm_channel_name_map: Dict[UnqualifiedName, TlmChannel] = field(
        default_factory=dict
    )
    # The map from event IDs to events
    event_map: Dict[EventId, Event] = field(default_factory=dict)
    # The map from parameter IDs to parameters
    param_map: Dict[ParamId, Param] = field(default_factory=dict)
    # The list of port matching specifiers
    spec_port_matching_list: List[
        fpp_ast.Annotated[AstNode[fpp_ast.SpecPortMatching]]
    ] = field(default_factory=list)
    # The map from state machine instance names to state machine instances
    state_machine_instance_map: Dict[UnqualifiedName, StateMachineInstance] = field(
        default_factory=dict
    )
    # The list of port matching constraints
    port_matching_list: List[PortMatching] = field(default_factory=list)
    # The map from container ids to containers
    container_map: Dict[ContainerId, Container] = field(default_factory=dict)
    # The map from record ids to records
    record_map: Dict[RecordId, Record] = field(default_factory=dict)

    def has_parameters(self) -> bool:
        return not self.param_map

    def has_external_parameters(self) -> bool:
        return any(v.is_external for v in self.param_map.values())

    def has_commands(self) -> bool:
        return self.command_map != dict()

    def has_events(self) -> bool:
        return self.event_map != dict()

    def has_telemetry(self) -> bool:
        return self.tlm_channel_map != dict()

    def has_data_products(self) -> bool:
        return self.container_map != dict()

    def has_state_machine_instances(self) -> bool:
        return self.state_machine_instance_map != dict()

    def has_state_machine_instances_of_kind(self, kind: StateMachineKind) -> bool:
        return any(
            v.get_sm_kind() == kind for v in self.state_machine_instance_map.values()
        )

    def get_tlm_channel_by_name(self, name: AstNode[fpp_ast.Ident]) -> TlmChannel:
        for channel in self.tlm_channel_name_map.values():
            if channel.get_name() == name:
                return channel
        raise KeyError(f"Could not find telemetry channel with name {name}")
