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
        self.expr_node(data.size)
        self.type_name_node(data.elt_type)
        if data.default:
            self.expr_node(data.default)
        if data.format:
            self.add_node_to_map(data.format)

    def def_choice_annotated_node(
        self, _in: In, a_node: fpp_ast.Annotated[AstNode[fpp_ast.DefChoice]]
    ) -> Out:
        data = a_node[1].data
        self.add_annotated_node_to_map(a_node)
        self.add_node_to_map(data.guard)
        self.transition_expr_node(data.if_transition)
        self.transition_expr_node(data.else_transition)

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
        self.qual_ident_node(data.component)
        self.expr_node(data.base_id)
        if data.impl_type:
            self.add_node_to_map(data.impl_type)
        if data.file:
            self.add_node_to_map(data.file)
        if data.queue_size:
            self.expr_node(data.queue_size)
        if data.stack_size:
            self.expr_node(data.stack_size)
        if data.priority:
            self.expr_node(data.priority)
        if data.cpu:
            self.expr_node(data.cpu)
        for init_spec_a_node in data.init_specs:
            self.spec_init_annotated_node(None, init_spec_a_node)

    def def_constant_annotated_node(
        self, _in: In, a_node: fpp_ast.Annotated[AstNode[fpp_ast.DefConstant]]
    ) -> Out:
        self.add_annotated_node_to_map(a_node)
        self.expr_node(a_node[1].data.value)

    def def_enum_annotated_node(
        self, _in: In, a_node: fpp_ast.Annotated[AstNode[fpp_ast.DefEnum]]
    ) -> Out:
        _, node, _ = a_node
        data = node.data
        self.add_annotated_node_to_map(a_node)
        if data.type_name:
            self.type_name_node(data.type_name)
        for c in data.constants:
            self.def_enum_constant(c)
        if data.default:
            self.expr_node(data.default)

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
        self.formal_param_list(data.params)
        if data.return_type:
            self.type_name_node(data.return_type)

    def def_signal_annotated_node(
        self, _in: In, a_node: fpp_ast.Annotated[AstNode[fpp_ast.DefSignal]]
    ) -> Out:
        _, node, _ = a_node
        data = node.data
        self.add_annotated_node_to_map(a_node)
        if data.type_name:
            self.type_name_node(data.type_name)

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
        if data.default:
            self.expr_node(data.default)

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
        if a_node[1].data.value:
            self.expr_node(a_node[1].data.value)

    def expr_array_node(
        self, _in: In, a_node: AstNode[fpp_ast.Expr], e: fpp_ast.ExprArray
    ) -> Out:
        self.add_node_to_map(a_node)
        for elem in e.elts:
            self.add_node_to_map(elem)

    def expr_array_subscript_node(
        self, _in: In, a_node: AstNode[fpp_ast.Expr], e: fpp_ast.ExprArraySubscript
    ) -> Out:
        self.add_node_to_map(a_node)
        self.expr_node(e.e1)
        self.expr_node(e.e2)

    def expr_binop_node(
        self, _in: In, a_node: AstNode[fpp_ast.Expr], e: fpp_ast.ExprBinop
    ) -> Out:
        self.add_node_to_map(a_node)
        self.expr_node(e.e1)
        self.expr_node(e.e2)

    def expr_dot_node(
        self, _in: In, a_node: AstNode[fpp_ast.Expr], e: fpp_ast.ExprDot
    ) -> Out:
        self.add_node_to_map(a_node)
        self.add_node_to_map(e.id)
        self.expr_node(e.e)

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
        for member in e.members:
            self.struct_member(member)

    def expr_unop_node(
        self, _in: In, a_node: AstNode[fpp_ast.Expr], e: fpp_ast.ExprUnop
    ) -> Out:
        self.add_node_to_map(a_node)
        self.expr_node(e.e)

    def spec_command_annotated_node(
        self, _in: In, a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecCommand]]
    ) -> Out:
        data = a_node[1].data
        self.add_annotated_node_to_map(a_node)
        self.formal_param_list(data.params)
        if data.opcode:
            self.expr_node(data.opcode)
        if data.priority:
            self.expr_node(data.priority)
        if data.queue_full:
            self.add_node_to_map(data.queue_full)

    def spec_comp_instance_annotated_node(
        self, _in: In, a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecCompInstance]]
    ) -> Out:
        self.add_annotated_node_to_map(a_node)
        self.qual_ident_node(a_node[1].data.instance)

    def spec_connection_graph_annotated_node(
        self, _in: In, a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecConnectionGraph]]
    ) -> Out:
        data = a_node[1].data
        self.add_annotated_node_to_map(a_node)
        if isinstance(data, fpp_ast.Direct):
            for c in data.connections:
                self.connection(c)
        elif isinstance(data, fpp_ast.Pattern):
            self.qual_ident_node(data.source)
            for t in data.targets:
                self.qual_ident_node(t)

    def spec_container_annotated_node(
        self, _in: In, a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecContainer]]
    ) -> Out:
        data = a_node[1].data
        self.add_annotated_node_to_map(a_node)
        if data.id:
            self.expr_node(data.id)
        if data.default_priority:
            self.expr_node(data.default_priority)

    def spec_event_annotated_node(
        self, _in: In, a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecEvent]]
    ) -> Out:
        data = a_node[1].data
        self.add_annotated_node_to_map(a_node)
        self.formal_param_list(a_node[1].data.params)
        if data.id:
            self.add_node_to_map(data.id)
        self.add_node_to_map(data.format)
        if data.throttle:
            self.throttle(data.throttle)

    def spec_include_annotated_node(
        self, _in: In, a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecInclude]]
    ) -> Out:
        self.add_annotated_node_to_map(a_node)
        self.add_node_to_map(a_node[1].data.file)

    def spec_init_annotated_node(
        self, _in: In, a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecInit]]
    ) -> Out:
        self.add_annotated_node_to_map(a_node)
        self.expr_node(a_node[1].data.phase)

    def spec_initial_transition_annotated_node(
        self, _in: In, a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecInitialTransition]]
    ) -> Out:
        self.add_annotated_node_to_map(a_node)
        self.transition_expr_node(a_node[1].data.transition)

    def spec_internal_port_annotated_node(
        self, _in: In, a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecInternalPort]]
    ) -> Out:
        data = a_node[1].data
        self.add_annotated_node_to_map(a_node)
        self.formal_param_list(data.params)
        if data.priority:
            self.expr_node(data.priority)

    def spec_loc_annotated_node(
        self, _in: In, a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecLoc]]
    ) -> Out:
        self.add_annotated_node_to_map(a_node)
        self.qual_ident_node(a_node[1].data.symbol)
        self.add_node_to_map(a_node[1].data.file)

    def spec_param_annotated_node(
        self, _in: In, a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecParam]]
    ) -> Out:
        _, node, _ = a_node
        data = node.data
        self.add_annotated_node_to_map(a_node)
        self.type_name_node(data.type_name)
        if data.default:
            self.expr_node(data.default)
        if data.id:
            self.expr_node(data.id)
        if data.set_opcode:
            self.expr_node(data.set_opcode)
        if data.save_opcode:
            self.expr_node(data.save_opcode)

    def spec_port_instance_annotated_node(
        self, _in: In, a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecPortInstance]]
    ) -> Out:
        data = a_node[1].data
        self.add_annotated_node_to_map(a_node)
        if isinstance(data, fpp_ast.GeneralPortInstance):
            if data.size:
                self.add_node_to_map(data.size)
            if data.port:
                self.qual_ident_node(data.port)
            if data.priority:
                self.add_node_to_map(data.priority)
            if data.queue_full:
                self.add_node_to_map(data.queue_full)
        elif isinstance(data, fpp_ast.SpecialPortInstance):
            if data.priority:
                self.expr_node(data.priority)
            if data.queue_full:
                self.add_node_to_map(data.queue_full)

    def spec_port_matching_annotated_node(
        self, _in: In, a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecPortMatching]]
    ) -> Out:
        self.add_annotated_node_to_map(a_node)
        self.add_node_to_map(a_node[1].data.port1)
        self.add_node_to_map(a_node[1].data.port2)

    def spec_record_annotated_node(
        self, _in: In, a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecRecord]]
    ) -> Out:
        _, node, _ = a_node
        data = node.data
        self.add_annotated_node_to_map(a_node)
        self.type_name_node(data.record_type)
        if data.id:
            self.expr_node(data.id)

    def spec_state_entry_annotated_node(
        self, _in: In, a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecStateEntry]]
    ) -> Out:
        self.add_annotated_node_to_map(a_node)
        for a in a_node[1].data.actions:
            self.add_node_to_map(a)

    def spec_state_exit_annotated_node(
        self, _in: In, a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecStateExit]]
    ) -> Out:
        self.add_annotated_node_to_map(a_node)
        for a in a_node[1].data.actions:
            self.add_node_to_map(a)

    def spec_state_machine_instance_annotated_node(
        self,
        _in: In,
        a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecStateMachineInstance]],
    ) -> Out:
        self.add_annotated_node_to_map(a_node)

    def spec_state_transition_annotated_node(
        self, _in: In, a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecStateTransition]]
    ) -> Out:
        data = a_node[1].data
        self.add_annotated_node_to_map(a_node)
        self.add_node_to_map(data.signal)
        if data.guard:
            self.add_node_to_map(data.guard)
        self.transition_or_do(data.transition_or_do)

    def transition_or_do(self, transition_or_do: fpp_ast.TransitionOrDo):
        if isinstance(transition_or_do, fpp_ast.Transition):
            self.transition_expr_node(transition_or_do.transition)
        elif isinstance(transition_or_do, fpp_ast.Do):
            for a in transition_or_do.actions:
                self.add_node_to_map(a)

    def spec_tlm_channel_annotated_node(
        self, _in: In, a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecTlmChannel]]
    ) -> Out:
        _, node, _ = a_node
        data = node.data
        self.add_annotated_node_to_map(a_node)
        self.type_name_node(data.type_name)
        if data.id:
            self.expr_node(data.id)
        if data.format:
            self.add_node_to_map(data.format)
        self.limits(data.low)
        self.limits(data.high)

    def spec_tlm_packet_annotated_node(
        self, _in: In, a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecTlmPacket]]
    ) -> Out:
        data = a_node[1].data
        self.add_annotated_node_to_map(a_node)
        if data.id:
            self.expr_node(data.id)
        self.expr_node(data.group)
        for m in data.members:
            self.tlm_packet_member(m)

    def spec_tlm_packet_set_annotated_node(
        self, _in: In, a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecTlmPacketSet]]
    ) -> Out:
        _, node, _ = a_node
        data = node.data
        self.add_annotated_node_to_map(a_node)
        for m in data.members:
            self.tlm_packet_set_member(m)
        for o in data.omitted:
            self.tlm_channel_identifier(o)

    def spec_top_import_annotated_node(
        self, _in: In, a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecImport]]
    ) -> Out:
        data = a_node[1].data
        self.add_annotated_node_to_map(a_node)
        self.qual_ident_node(data.sym)

    def spec_interface_import_annotated_node(
        self, _in: In, a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecImport]]
    ) -> Out:
        self.add_annotated_node_to_map(a_node)
        self.qual_ident_node(a_node[1].data.sym)

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
        data = member[1].data
        self.add_annotated_node_to_map(member)
        self.type_name_node(data.type_name)
        if data.size:
            self.expr_node(data.size)
        if data.format:
            self.add_node_to_map(data.format)

    def struct_member(self, member: AstNode[fpp_ast.StructMember]) -> Out:
        self.add_node_to_map(member)
        self.expr_node(member.data.value)

    def interface_member(self, member: fpp_ast.InterfaceMember) -> Out:
        self.match_interface_member(None, member)

    def tlm_packet_set_member(self, member: fpp_ast.TlmPacketSetMember) -> Out:
        self.match_tlm_packet_set_member(None, member)

    def tlm_channel_identifier(
        self, tci_node: AstNode[fpp_ast.TlmChannelIdentifier]
    ) -> Out:
        self.add_node_to_map(tci_node)
        data = tci_node.data
        self.qual_ident_node(data.component_instance)
        self.add_node_to_map(data.channel_name)

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
        self.qual_ident_node(tn.name)

    def type_name_string_node(
        self, _in: In, a_node: AstNode[fpp_ast.TypeName], tn: fpp_ast.TypeNameString
    ) -> Out:
        self.add_node_to_map(a_node)
        if tn.size:
            self.add_node_to_map(tn.size)

    def formal_param_list(self, params: fpp_ast.FormalParamList) -> Out:
        for param in params:
            self.add_node_to_map(param[1])
            self.type_name_node(param[1].data.type_name)

    def port_instance_identifier_node(
        self, node: AstNode[fpp_ast.PortInstanceIdentifier]
    ) -> Out:
        pii = node.data
        self.add_node_to_map(node)
        self.qual_ident_node(pii.component_instance)
        self.add_node_to_map(pii.port_name)

    def connection(self, connection: fpp_ast.Connection) -> Out:
        self.port_instance_identifier_node(connection.from_port)
        if connection.from_index:
            self.expr_node(connection.from_index)
        self.port_instance_identifier_node(connection.to_port)
        if connection.to_index:
            self.expr_node(connection.to_index)

    def qual_ident_node(self, qid_node: AstNode[fpp_ast.QualIdent]) -> Out:
        self.add_node_to_map(qid_node)
        data = qid_node.data
        if isinstance(data, fpp_ast.Qualified):
            self.qual_ident_node(data.qualifier)
            self.add_node_to_map(data.name)

    def transition_expr_node(self, tr_node: AstNode[fpp_ast.TransitionExpr]) -> Out:
        node = tr_node.data
        self.add_node_to_map(tr_node)
        for a in node.actions:
            self.add_node_to_map(a)
        self.qual_ident_node(node.target)

    def tlm_packet_member(self, pm: fpp_ast.TlmPacketMember) -> Out:
        if isinstance(pm, fpp_ast.TlmPacketMemberSpecInclude):
            self.add_node_to_map(pm.node)
            self.add_node_to_map(pm.node.data.file)
        elif isinstance(pm, fpp_ast.TlmPacketMemberTlmChannelIdentifier):
            self.tlm_channel_identifier(pm.node)

    def limits(self, limits: List[fpp_ast.Limit]) -> Out:
        for limit in limits:
            limit_kind, limit_val = limit
            self.add_node_to_map(limit_kind)
            self.expr_node(limit_val)

    def throttle(self, throttle: AstNode[fpp_ast.EventThrottle]) -> Out:
        data = throttle.data
        self.expr_node(data.count)
        if data.every:
            self.expr_node(data.every)

    def construct_ast_map(
        self, tu_list: List[fpp_ast.TransUnit]
    ) -> Tuple[Dict[AstId, AstNode], Dict[AstId, fpp_ast.Annotated[AstNode]]]:
        for tu in tu_list:
            self.trans_unit(None, tu)
        return self.ast_id_map, self.annotated_ast_id_map
