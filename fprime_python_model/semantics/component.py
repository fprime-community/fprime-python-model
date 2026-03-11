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
from fprime_python_model.semantics.port_interface import PortInterface


@dataclass
class PortMatching:
    """
    A port patching

    :param a_node: Annotated port matching AST node
    :type a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecPortMatching]]
    :param instance1: First port instance
    :type instance1: GeneralPortInstance
    :param instance2: Second port instance
    :type instance2: GeneralPortInstance
    """

    a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecPortMatching]]
    instance1: GeneralPortInstance
    instance2: GeneralPortInstance

    def __str__(self):
        """
        Gets the string representation of the port matching

        :return: Port matching string
        :rtype: str
        """
        return f"match {str(self.instance1)} with {str(self.instance2)}"


@dataclass
class Component:
    """
    An FPP component

    :param a_node: The annotated AST node defining the component
    :type a_node: fpp_ast.Annotated[AstNode[fpp_ast.DefComponent]]
    :param port_interface: The port interface of the component
    :type port_interface: PortInterface
    :param command_map: The map from command opcodes to commands
    :type command_map: Dict[CommandOpcode, Command]
    :param tlm_channel_map: The map from telemetry channel IDs to channels
    :type tlm_channel_map: Dict[TlmChannelId, TlmChannel]
    :param tlm_channel_name_map: The map from telemetry channel names to channels
    :type tlm_channel_name_map: Dict[UnqualifiedName, TlmChannel]
    :param event_map: The map from event IDs to events
    :type event_map: Dict[EventId, Event]
    :param param_map: The map from parameter IDs to parameters
    :type param_map: Dict[ParamId, Param]
    :param spec_port_matching_list: The list of port matching specifiers
    :type spec_port_matching_list: List[fpp_ast.Annotated[AstNode[fpp_ast.SpecPortMatching]]]
    :param state_machine_instance_map: The map from state machine instance names to state machine instances
    :type state_machine_instance_map: Dict[UnqualifiedName, StateMachineInstance]
    :param port_matching_list: The list of port matching constraints
    :type port_matching_list: List[PortMatching]
    :param constainer_map: The map from container IDs to containers
    :type container_map: Dict[ContainerId, Container]
    :param record_map: The map from record IDs to records
    :type record_map: Dict[RecordId, Record]
    """

    a_node: fpp_ast.Annotated[AstNode[fpp_ast.DefComponent]]
    port_interface: PortInterface = field(default=lambda: PortInterface("component"))
    command_map: Dict[CommandOpcode, Command] = field(default_factory=dict)
    tlm_channel_map: Dict[TlmChannelId, TlmChannel] = field(default_factory=dict)
    tlm_channel_name_map: Dict[UnqualifiedName, TlmChannel] = field(
        default_factory=dict
    )
    event_map: Dict[EventId, Event] = field(default_factory=dict)
    param_map: Dict[ParamId, Param] = field(default_factory=dict)
    spec_port_matching_list: List[
        fpp_ast.Annotated[AstNode[fpp_ast.SpecPortMatching]]
    ] = field(default_factory=list)
    state_machine_instance_map: Dict[UnqualifiedName, StateMachineInstance] = field(
        default_factory=dict
    )
    port_matching_list: List[PortMatching] = field(default_factory=list)
    container_map: Dict[ContainerId, Container] = field(default_factory=dict)
    record_map: Dict[RecordId, Record] = field(default_factory=dict)

    def port_map(self) -> Dict[UnqualifiedName, PortInstance]:
        return self.port_interface.port_map

    def special_port_map(self) -> Dict[fpp_ast.SpecialKind, SpecialPortInstance]:
        return self.port_interface.special_port_map

    def has_parameters(self) -> bool:
        """
        Query whether the component has parameters

        :return: True if the component has parameters, False otherwise
        :rtype: bool
        """
        return not self.param_map

    def has_external_parameters(self) -> bool:
        """
        Query whether the component has external parameters

        :return: True if the component has external parameters, False otherwise
        :rtype: bool
        """
        return any(v.is_external for v in self.param_map.values())

    def has_commands(self) -> bool:
        """
        Query whether the component has commands

        :return: True if the component has commands, False otherwise
        :rtype: bool
        """
        return not self.command_map

    def has_events(self) -> bool:
        """
        Query whether the component has events

        :return: True if the component has events, False otherwise
        :rtype: bool
        """
        return not self.event_map

    def has_telemetry(self) -> bool:
        """
        Query whether the component has telemetry

        :return: True if the component has telemetry, False otherwise
        :rtype: bool
        """
        return not self.tlm_channel_map

    def has_data_products(self) -> bool:
        """
        Query whether the component has data products

        :return: True if the component has data products, False otherwise
        :rtype: bool
        """
        return not self.container_map

    def has_state_machine_instances(self) -> bool:
        """
        Query whether the component has state machine instances

        :return: True of the component has state machine instances, False otherwise
        :rtype: bool
        """
        return not self.state_machine_instance_map

    def has_state_machine_instances_of_kind(self, kind: StateMachineKind) -> bool:
        """
        Query whether the state machine has instances of the specified kind

        :param kind: Kind of state machine
        :type kind: StateMachineKind
        :return: True if the component has state machine instances of the specified kind, False otherwise
        :rtype: bool
        """
        return any(
            v.get_sm_kind() == kind for v in self.state_machine_instance_map.values()
        )

    def get_tlm_channel_by_name(self, name: AstNode[fpp_ast.Ident]) -> TlmChannel:
        """
        Gets a telemetry channel by name

        :param name: AstNode corresponding to the name of the telemetry channel
        :type name: AstNode[fpp_ast.Ident]
        :raises KeyError: Key error is raised if the telemetry channel is not found
        :return: Telemetry channel
        :rtype: TlmChannel
        """
        for channel in self.tlm_channel_name_map.values():
            if channel.get_name() == name:
                return channel
        raise KeyError(f"Could not find telemetry channel with name {name}")
