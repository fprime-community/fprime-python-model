from dataclasses import dataclass, field
from typing import Dict, Set
from fprime_python_model.fpp_ast import fpp_ast
from fprime_python_model.semantics.tlm_channel import TlmChannelId
from fprime_python_model.semantics.symbol import Symbol
from fprime_python_model.semantics.component_instance import ComponentInstance
from fprime_python_model.semantics.command import CommandOpcode, Command
from fprime_python_model.semantics.container import ContainerId, Container
from fprime_python_model.semantics.param import ParamId, Param
from fprime_python_model.semantics.record import RecordId, Record
from fprime_python_model.semantics.tlm_channel import TlmChannelId, TlmChannel
from fprime_python_model.semantics.event import EventId, Event
from fprime_python_model.semantics.name import (
    QualifiedName,
    UnqualifiedName,
    qualified_name_from_ident_list,
)
from fprime_python_model.semantics.tlm_packet_set import TlmPacketSet


# A command entry in the dictionary
@dataclass
class DictionaryCommandEntry:
    instance: ComponentInstance
    command: Command


# A container entry in the dictionary
@dataclass
class DictionaryContainerEntry:
    instance: ComponentInstance
    container: Container


# A param entry in the dictionary
@dataclass
class DictionaryParamEntry:
    instance: ComponentInstance
    param: Param


# A container entry in the dictionary
@dataclass
class DictionaryRecordEntry:
    instance: ComponentInstance
    record: Record


# A telemetry channel entry in the dictionary
@dataclass
class DictionaryTlmChannelEntry:
    instance: ComponentInstance
    tlm_channel: TlmChannel

    def get_qualified_name(self) -> QualifiedName:
        instance_name: QualifiedName = self.instance.qualified_name
        channel_name: fpp_ast.Ident = self.tlm_channel.get_name()
        return qualified_name_from_ident_list(
            instance_name.to_ident_list() + [channel_name]
        )


# An event entry in the dictionary
@dataclass
class DictionaryEventEntry:
    instance: ComponentInstance
    event: Event


# An FPP dictionary
@dataclass
class Dictionary:
    # A set of symbols used in the dictionary
    used_symbol_set: Set[Symbol] = field(default_factory=set)
    # The map from global IDs to command entries
    command_entry_map: Dict[CommandOpcode, DictionaryCommandEntry] = field(
        default_factory=dict
    )
    # The map from global IDs to telemetry channel entries
    tlm_channel_entry_map: Dict[TlmChannelId, DictionaryTlmChannelEntry] = field(
        default_factory=dict
    )
    # The map from global IDs to event entries
    event_entry_map: Dict[EventId, DictionaryEventEntry] = field(default_factory=dict)
    # The map from global IDs to parameter entries
    param_entry_map: Dict[ParamId, DictionaryParamEntry] = field(default_factory=dict)
    # The map from global IDs to record entries
    record_entry_map: Dict[RecordId, DictionaryRecordEntry] = field(
        default_factory=dict
    )
    # The map from global IDs to container entries
    container_entry_map: Dict[ContainerId, DictionaryContainerEntry] = field(
        default_factory=dict
    )
    # The map from packet set names to packet sets
    tlm_packet_set_map: Dict[UnqualifiedName, TlmPacketSet] = field(
        default_factory=dict
    )
