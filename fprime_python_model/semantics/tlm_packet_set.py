from fprime_python_model.fpp_ast.fpp_ast_node import AstNode
from fprime_python_model.fpp_ast import fpp_ast
from fprime_python_model.fpp_ast.fpp_locations import Location
from fprime_python_model.semantics.tlm_channel import TlmChannelId
from fprime_python_model.semantics.tlm_packet import TlmPacketId, TlmPacket
from dataclasses import dataclass, field
from typing import Dict, Set


# An FPP telemetry packet set
@dataclass
class TlmPacketSet:
    # The annotated AST node
    a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecTlmPacketSet]]
    # The map from packet IDs to packets
    packet_map: Dict[TlmPacketId, TlmPacket] = field(default_factory=dict)
    # The next default packet ID
    default_packet_id: TlmPacketId = 0
    # The set of omitted channel IDs
    omitted_channel_set: Set[TlmChannelId] = field(default_factory=set)
    # The map from each omitted channel ID to a location
    # where the channel is marked as omitted.
    # If the channel appears more than once in the omitted list in
    # the source model, the map contains the last location.
    omitted_location_map: Dict[TlmChannelId, Location] = field(default_factory=dict)

    # Gets the name of the packet
    def get_name(self) -> fpp_ast.Ident:
        return self.a_node[1].data.name

    # Gets the channels used in the packet set
    def get_used_id_set(self) -> Set[TlmChannelId]:
        out_set: Set = set()
        for tlm_packet in self.packet_map.values():
            out_set |= set(tlm_packet.member_id_list)
        return out_set

    def get_node(self) -> AstNode[fpp_ast.SpecTlmPacketSet]:
        return self.a_node[1]
