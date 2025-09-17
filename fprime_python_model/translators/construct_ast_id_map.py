from fprime_python_model.utils.fpp_ast_visitor import AstVisitor, In
from typing import Dict, TypeAlias, Tuple, List
from fprime_python_model.fpp_ast.fpp_ast_node import AstId, AstNode
from fprime_python_model.fpp_ast import fpp_ast
from fprime_python_model.utils.error import InternalError

Out: TypeAlias = None


class ConstructAstMap(AstVisitor):

    def __init__(self):
        super().__init__()
        self.ast_id_map: Dict[AstId, AstNode] = dict()
        self.annotated_ast_id_map: Dict[AstId, fpp_ast.Annotated[AstNode]] = dict()

    def default(self, _in: In):
        raise InternalError("ConstructAstMap: Visitor not implemented")

    def add_annotated_node_to_map(self, a_node: fpp_ast.Annotated[AstNode]):
        self.annotated_ast_id_map[a_node[1]._id] = a_node

    def add_node_to_map(self, a_node: AstNode):
        self.ast_id_map[a_node._id] = a_node

    def def_abs_type_annotated_node(
        self, _in: In, a_node: fpp_ast.Annotated[AstNode[fpp_ast.DefAbsType]]
    ) -> Out:
        self.add_annotated_node_to_map(a_node)

    def def_alias_type_annotated_node(
        self, _in: In, a_node: fpp_ast.Annotated[AstNode[fpp_ast.DefAliasType]]
    ) -> Out:
        _, node, _ = a_node
        self.add_annotated_node_to_map(a_node)
        self.type_name_node(node.data.type_name)

    def def_action_annotated_node(
        self, _in: In, a_node: fpp_ast.Annotated[AstNode[fpp_ast.DefAction]]
    ) -> Out:
        _, node, _ = a_node
        data = node.data
        self.add_annotated_node_to_map(a_node)
        if data.type_name:
            self.add_node_to_map(data.type_name)

    def def_array_annotated_node(
        self, _in: In, a_node: fpp_ast.Annotated[AstNode[fpp_ast.DefArray]]
    ) -> Out:
        _, node, _ = a_node
        data = node.data
        self.add_annotated_node_to_map(a_node)
        self.type_name_node(data.elt_type)

    def def_choice_annotated_node(
        self, _in: In, a_node: fpp_ast.Annotated[AstNode[fpp_ast.DefChoice]]
    ) -> Out:
        self.add_annotated_node_to_map(a_node)

    def def_component_annotated_node(
        self, _in: In, a_node: fpp_ast.Annotated[AstNode[fpp_ast.DefComponent]]
    ) -> Out:
        _, node, _ = a_node
        data = node.data
        self.add_annotated_node_to_map(a_node)
        for m in data.members:
            self.component_member(m)

    def def_interface_annotated_node(
        self, _in: In, a_node: fpp_ast.Annotated[AstNode[fpp_ast.DefInterface]]
    ) -> Out:
        _, node, _ = a_node
        data = node.data
        self.add_annotated_node_to_map(a_node)
        for m in data.members:
            self.interface_member(m)

    def def_component_instance_annotated_node(
        self, _in: In, a_node: fpp_ast.Annotated[AstNode[fpp_ast.DefComponentInstance]]
    ) -> Out:
        _, node, _ = a_node
        data = node.data
        self.add_annotated_node_to_map(a_node)

    def def_constant_annotated_node(
        self, _in: In, a_node: fpp_ast.Annotated[AstNode[fpp_ast.DefConstant]]
    ) -> Out:
        self.add_annotated_node_to_map(a_node)

    def def_enum_annotated_node(
        self, _in: In, a_node: fpp_ast.Annotated[AstNode[fpp_ast.DefEnum]]
    ) -> Out:
        _, node, _ = a_node
        data = node.data
        self.add_annotated_node_to_map(a_node)
        if data.type_name:
            self.add_node_to_map(data.type_name)
        for c in data.constants:
            self.def_enum_constant(c)

    def def_guard_annotated_node(
        self, _in: In, a_node: fpp_ast.Annotated[AstNode[fpp_ast.DefGuard]]
    ) -> Out:
        _, node, _ = a_node
        data = node.data
        self.add_annotated_node_to_map(a_node)
        if data.type_name:
            self.add_node_to_map(data.type_name)

    def def_module_annotated_node(
        self, _in: In, a_node: fpp_ast.Annotated[AstNode[fpp_ast.DefModule]]
    ) -> Out:
        _, node, _ = a_node
        data = node.data
        self.add_annotated_node_to_map(a_node)
        for m in data.members:
            self.module_member(m)

    def def_port_annotated_node(
        self, _in: In, a_node: fpp_ast.Annotated[AstNode[fpp_ast.DefPort]]
    ) -> Out:
        _, node, _ = a_node
        data = node.data
        self.add_annotated_node_to_map(a_node)
        if data.return_type:
            self.add_node_to_map(data.return_type)
        self.formal_param_list(data.params)

    def def_signal_annotated_node(
        self, _in: In, a_node: fpp_ast.Annotated[AstNode[fpp_ast.DefSignal]]
    ) -> Out:
        _, node, _ = a_node
        data = node.data
        self.add_annotated_node_to_map(a_node)
        if data.type_name:
            self.add_node_to_map(data.type_name)

    def def_state_annotated_node(
        self, _in: In, a_node: fpp_ast.Annotated[AstNode[fpp_ast.DefState]]
    ) -> Out:
        _, node, _ = a_node
        data = node.data
        self.add_annotated_node_to_map(a_node)
        for m in data.members:
            self.state_member(m)

    def def_state_machine_annotated_node(
        self, _in: In, a_node: fpp_ast.Annotated[AstNode[fpp_ast.DefStateMachine]]
    ):
        _, node, _ = a_node
        data = node.data
        self.add_annotated_node_to_map(a_node)
        if data.members:
            for m in data.members:
                self.state_machine_member(m)

    def def_struct_annotated_node(
        self, _in: In, a_node: fpp_ast.Annotated[AstNode[fpp_ast.DefStruct]]
    ) -> Out:
        _, node, _ = a_node
        data = node.data
        self.add_annotated_node_to_map(a_node)
        for m in data.members:
            self.struct_type_member(m)

    def def_topology_annotated_node(
        self, _in: In, a_node: fpp_ast.Annotated[AstNode[fpp_ast.DefTopology]]
    ) -> Out:
        _, node, _ = a_node
        data = node.data
        self.add_annotated_node_to_map(a_node)
        for m in data.members:
            self.topology_member(m)

    def def_enum_constant(
        self, a_node: fpp_ast.Annotated[AstNode[fpp_ast.DefEnumConstant]]
    ) -> Out:
        self.add_annotated_node_to_map(a_node)

    def expr_array_node(
        self, _in: In, a_node: AstNode[fpp_ast.Expr], e: fpp_ast.ExprArray
    ) -> Out:
        self.add_node_to_map(a_node)

    def expr_binop_node(
        self, _in: In, a_node: AstNode[fpp_ast.Expr], e: fpp_ast.ExprBinop
    ) -> Out:
        self.add_node_to_map(a_node)

    def expr_dot_node(
        self, _in: In, a_node: AstNode[fpp_ast.Expr], e: fpp_ast.ExprDot
    ) -> Out:
        self.add_node_to_map(a_node)

    def expr_ident_node(
        self, _in: In, a_node: AstNode[fpp_ast.Expr], e: fpp_ast.ExprIdent
    ) -> Out:
        self.add_node_to_map(a_node)

    def expr_literal_bool_node(
        self, _in: In, a_node: AstNode[fpp_ast.Expr], e: fpp_ast.ExprLiteralBool
    ) -> Out:
        self.add_node_to_map(a_node)

    def expr_literal_float_node(
        self, _in: In, a_node: AstNode[fpp_ast.Expr], e: fpp_ast.ExprLiteralFloat
    ) -> Out:
        self.add_node_to_map(a_node)

    def expr_literal_int_node(
        self, _in: In, a_node: AstNode[fpp_ast.Expr], e: fpp_ast.ExprLiteralInt
    ) -> Out:
        self.add_node_to_map(a_node)

    def expr_literal_string_node(
        self, _in: In, a_node: AstNode[fpp_ast.Expr], e: fpp_ast.ExprLiteralString
    ) -> Out:
        self.add_node_to_map(a_node)

    def expr_paren_node(
        self, _in: In, a_node: AstNode[fpp_ast.Expr], e: fpp_ast.ExprParen
    ) -> Out:
        self.add_node_to_map(a_node)

    def expr_struct_node(
        self, _in: In, a_node: AstNode[fpp_ast.Expr], e: fpp_ast.ExprStruct
    ) -> Out:
        self.add_node_to_map(a_node)

    def expr_unop_node(
        self, _in: In, a_node: AstNode[fpp_ast.Expr], e: fpp_ast.ExprUnop
    ) -> Out:
        self.add_node_to_map(a_node)

    def spec_command_annotated_node(
        self, _in: In, a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecCommand]]
    ) -> Out:
        self.add_annotated_node_to_map(a_node)
        self.formal_param_list(a_node[1].data.params)

    def spec_comp_instance_annotated_node(
        self, _in: In, a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecCompInstance]]
    ) -> Out:
        self.add_annotated_node_to_map(a_node)

    def spec_connection_graph_annotated_node(
        self, _in: In, a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecConnectionGraph]]
    ) -> Out:
        self.add_annotated_node_to_map(a_node)

    def spec_container_annotated_node(
        self, _in: In, a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecContainer]]
    ) -> Out:
        self.add_annotated_node_to_map(a_node)

    def spec_event_annotated_node(
        self, _in: In, a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecEvent]]
    ) -> Out:
        self.add_annotated_node_to_map(a_node)
        self.formal_param_list(a_node[1].data.params)

    def spec_include_annotated_node(
        self, _in: In, a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecInclude]]
    ) -> Out:
        self.add_annotated_node_to_map(a_node)

    def spec_init_annotated_node(
        self, _in: In, a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecInit]]
    ) -> Out:
        self.add_annotated_node_to_map(a_node)

    def spec_initial_transition_annotated_node(
        self, _in: In, a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecInitialTransition]]
    ) -> Out:
        self.add_annotated_node_to_map(a_node)

    def spec_internal_port_annotated_node(
        self, _in: In, a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecInternalPort]]
    ) -> Out:
        self.add_annotated_node_to_map(a_node)

    def spec_loc_annotated_node(
        self, _in: In, a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecLoc]]
    ) -> Out:
        self.add_annotated_node_to_map(a_node)

    def spec_param_annotated_node(
        self, _in: In, a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecParam]]
    ) -> Out:
        _, node, _ = a_node
        data = node.data
        self.add_annotated_node_to_map(a_node)
        self.type_name_node(data.type_name)

    def spec_port_instance_annotated_node(
        self, _in: In, a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecPortInstance]]
    ) -> Out:
        self.add_annotated_node_to_map(a_node)
        if isinstance(a_node[1].data, fpp_ast.GeneralPortInstance):
            if a_node[1].data.port:
                self.add_node_to_map(a_node[1].data.port)

    def spec_port_matching_annotated_node(
        self, _in: In, a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecPortMatching]]
    ) -> Out:
        self.add_annotated_node_to_map(a_node)

    def spec_record_annotated_node(
        self, _in: In, a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecRecord]]
    ) -> Out:
        _, node, _ = a_node
        data = node.data
        self.add_annotated_node_to_map(a_node)
        self.add_node_to_map(data.record_type)

    def spec_state_entry_annotated_node(
        self, _in: In, a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecStateEntry]]
    ) -> Out:
        self.add_annotated_node_to_map(a_node)

    def spec_state_exit_annotated_node(
        self, _in: In, a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecStateExit]]
    ) -> Out:
        self.add_annotated_node_to_map(a_node)

    def spec_state_machine_instance_annotated_node(
        self,
        _in: In,
        a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecStateMachineInstance]],
    ) -> Out:
        self.add_annotated_node_to_map(a_node)

    def spec_state_transition_annotated_node(
        self, _in: In, a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecStateTransition]]
    ) -> Out:
        self.add_annotated_node_to_map(a_node)

    def spec_tlm_channel_annotated_node(
        self, _in: In, a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecTlmChannel]]
    ) -> Out:
        _, node, _ = a_node
        data = node.data
        self.add_annotated_node_to_map(a_node)
        self.type_name_node(data.type_name)

    def spec_tlm_packet_annotated_node(
        self, _in: In, a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecTlmPacket]]
    ) -> Out:
        self.add_annotated_node_to_map(a_node)

    def spec_tlm_packet_set_annotated_node(
        self, _in: In, a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecTlmPacketSet]]
    ) -> Out:
        _, node, _ = a_node
        data = node.data
        self.add_annotated_node_to_map(a_node)
        for m in data.members:
            self.tlm_packet_set_member(m)

    def spec_top_import_annotated_node(
        self, _in: In, a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecImport]]
    ) -> Out:
        self.add_annotated_node_to_map(a_node)

    def spec_interface_import_annotated_node(
        self, _in: In, a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecImport]]
    ) -> Out:
        self.add_annotated_node_to_map(a_node)

    def module_member(self, member: fpp_ast.ModuleMember) -> Out:
        self.match_module_member(None, member)

    def topology_member(self, member: fpp_ast.TopologyMember) -> Out:
        self.match_topology_member(None, member)

    def component_member(self, member: fpp_ast.ComponentMember) -> Out:
        self.match_component_member(None, member)

    def state_member(self, member: fpp_ast.StateMember) -> Out:
        self.match_state_member(None, member)

    def state_machine_member(self, member: fpp_ast.StateMachineMember) -> Out:
        self.match_state_machine_member(None, member)

    def struct_type_member(
        self, member: fpp_ast.Annotated[AstNode[fpp_ast.StructTypeMember]]
    ) -> Out:
        self.add_annotated_node_to_map(member)
        self.type_name_node(member[1].data.type_name)

    def interface_member(self, member: fpp_ast.InterfaceMember) -> Out:
        self.match_interface_member(None, member)

    def tlm_packet_set_member(self, member: fpp_ast.TlmPacketSetMember) -> Out:
        self.match_tlm_packet_set_member(None, member)

    def expr_node(self, node):
        self.match_expr_node(None, node)

    def tu_member(self, tum: fpp_ast.TUMember) -> Out:
        self.module_member(tum)

    def trans_unit(self, in_, tu: fpp_ast.TransUnit) -> Out:
        for member in tu.members:
            self.tu_member(member)

    def type_name_node(self, node: AstNode[fpp_ast.TypeName]) -> Out:
        self.match_type_name_node(None, node)

    def type_name_bool_node(self, _in: In, a_node: AstNode[fpp_ast.TypeName]) -> Out:
        self.add_node_to_map(a_node)

    def type_name_float_node(
        self, _in: In, a_node: AstNode[fpp_ast.TypeName], tn: fpp_ast.TypeNameFloat
    ) -> Out:
        self.add_node_to_map(a_node)

    def type_name_int_node(
        self, _in: In, a_node: AstNode[fpp_ast.TypeName], tn: fpp_ast.TypeNameInt
    ) -> Out:
        self.add_node_to_map(a_node)

    def type_name_qual_ident_node(
        self, _in: In, a_node: AstNode[fpp_ast.TypeName], tn: fpp_ast.TypeNameQualIdent
    ) -> Out:
        self.add_node_to_map(a_node)

    def type_name_string_node(
        self, _in: In, a_node: AstNode[fpp_ast.TypeName], tn: fpp_ast.TypeNameString
    ) -> Out:
        self.add_node_to_map(a_node)
        if tn.size:
            self.add_node_to_map(tn.size)

    def formal_param_list(self, params: fpp_ast.FormalParamList) -> Out:
        for param in params:
            self.type_name_node(param[1].data.type_name)

    def construct_ast_map(
        self, tu_list: List[fpp_ast.TransUnit]
    ) -> Tuple[Dict[AstId, AstNode], Dict[AstId, fpp_ast.Annotated[AstNode]]]:
        for tu in tu_list:
            self.trans_unit(None, tu)
        return self.ast_id_map, self.annotated_ast_id_map
