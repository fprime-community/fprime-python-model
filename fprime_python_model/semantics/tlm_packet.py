from fprime_python_model.fpp_ast.fpp_ast_node import AstNode
from fprime_python_model.fpp_ast import fpp_ast
from fprime_python_model.fpp_ast.fpp_locations import Location
from fprime_python_model.semantics.tlm_channel import TlmChannelId
from dataclasses import dataclass
from typing import List, Dict, TypeAlias

TlmPacketId: TypeAlias = int


# An FPP telemetry packet
@dataclass
class TlmPacket:
    # The AST node for the packet
    a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecTlmPacket]]
    # The packet group
    group: int
    # The identifiers for the member channels
    member_id_list: List[TlmChannelId]
    # The map from each member ID to a location where a member
    # with that ID is specified.
    # If more than one member has this ID, the map contains the
    # last location.
    member_location_map: Dict[TlmChannelId, Location]

    # Gets the name of the packet
    def get_name(self) -> fpp_ast.Ident:
        return self.a_node[1].data.name

    def get_node(self) -> AstNode[fpp_ast.SpecTlmPacket]:
        return self.a_node[1]
