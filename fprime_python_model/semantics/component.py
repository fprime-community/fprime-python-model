from dataclasses import dataclass, field
from typing import Dict, List
from fprime_python_model.fpp_ast.fpp_ast_node import AstNode
from fprime_python_model.fpp_ast import fpp_ast
from fprime_python_model.semantics.port_instance import (
    PortInstance,
    SpecialPortInstance,
)
from fprime_python_model.semantics.command import Command, CommandOpcode
from fprime_python_model.semantics.tlm_channel import TlmChannel, TlmChannelId
from fprime_python_model.semantics.event import Event, EventId
from fprime_python_model.semantics.param import Param, ParamId
from fprime_python_model.semantics.container import Container, ContainerId
from fprime_python_model.semantics.record import Record, RecordId
from fprime_python_model.semantics.state_machine_instance import StateMachineInstance


@dataclass
class Component:
    # The AST node defining the component
    a_node: fpp_ast.Annotated[AstNode[fpp_ast.DefComponent]]
    # The map from port names to port instances
    port_map: Dict[fpp_ast.Unqualified, PortInstance] = field(default_factory=dict)
    # The map from special port kinds to special port instances
    special_port_map: Dict[fpp_ast.SpecialKind, SpecialPortInstance] = field(
        default_factory=dict
    )
    # The map from command opcodes to commands
    command_map: Dict[CommandOpcode, Command] = field(default_factory=dict)
    # The map from telemetry channel IDs to channels
    tlm_channel_map: Dict[TlmChannelId, TlmChannel] = field(default_factory=dict)
    # The map from telemetry channel names to channels
    tlm_channel_name_map: Dict[fpp_ast.Unqualified, TlmChannel] = field(
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
    state_machine_instance_map: Dict[fpp_ast.Unqualified, StateMachineInstance] = field(
        default_factory=dict
    )
    # # The list of port matching constraints
    # port_matching_list: List[ComponentPortMatching] = field(default_factory=list)
    # The map from container ids to containers
    container_map: Dict[ContainerId, Container] = field(default_factory=dict)
    # The map from record ids to records
    record_map: Dict[RecordId, Record] = field(default_factory=dict)
