from abc import ABC, abstractmethod
from typing import Generic, TypeVar, List
from fprime_python_model.fpp_ast.fpp_ast_node import AstNode
from fprime_python_model.fpp_ast import fpp_ast
from fprime_python_model.utils.error import InternalError

In = TypeVar("In")
Out = TypeVar("Out")


class AstVisitor(ABC, Generic[In, Out]):

    @abstractmethod
    def default(self, _in: In) -> Out:
        pass

    def def_abs_type_annotated_node(
        self, _in: In, node: fpp_ast.Annotated[AstNode[fpp_ast.DefAbsType]]
    ) -> Out:
        return self.default(_in)

    def def_alias_type_annotated_node(
        self, _in: In, node: fpp_ast.Annotated[AstNode[fpp_ast.DefAliasType]]
    ) -> Out:
        return self.default(_in)

    def def_action_annotated_node(
        self, _in: In, node: fpp_ast.Annotated[AstNode[fpp_ast.DefAction]]
    ) -> Out:
        return self.default(_in)

    def def_array_annotated_node(
        self, _in: In, node: fpp_ast.Annotated[AstNode[fpp_ast.DefArray]]
    ) -> Out:
        return self.default(_in)

    def def_choice_annotated_node(
        self, _in: In, node: fpp_ast.Annotated[AstNode[fpp_ast.DefChoice]]
    ) -> Out:
        return self.default(_in)

    def def_component_annotated_node(
        self, _in: In, node: fpp_ast.Annotated[AstNode[fpp_ast.DefComponent]]
    ) -> Out:
        return self.default(_in)

    def def_interface_annotated_node(
        self, _in: In, node: fpp_ast.Annotated[AstNode[fpp_ast.DefInterface]]
    ) -> Out:
        return self.default(_in)

    def def_component_instance_annotated_node(
        self, _in: In, node: fpp_ast.Annotated[AstNode[fpp_ast.DefComponentInstance]]
    ) -> Out:
        return self.default(_in)

    def def_constant_annotated_node(
        self, _in: In, node: fpp_ast.Annotated[AstNode[fpp_ast.DefConstant]]
    ) -> Out:
        return self.default(_in)

    def def_enum_annotated_node(
        self, _in: In, node: fpp_ast.Annotated[AstNode[fpp_ast.DefEnum]]
    ) -> Out:
        return self.default(_in)

    def def_guard_annotated_node(
        self, _in: In, node: fpp_ast.Annotated[AstNode[fpp_ast.DefGuard]]
    ) -> Out:
        return self.default(_in)

    def def_module_annotated_node(
        self, _in: In, node: fpp_ast.Annotated[AstNode[fpp_ast.DefModule]]
    ) -> Out:
        return self.default(_in)

    def def_port_annotated_node(
        self, _in: In, node: fpp_ast.Annotated[AstNode[fpp_ast.DefPort]]
    ) -> Out:
        return self.default(_in)

    def def_signal_annotated_node(
        self, _in: In, node: fpp_ast.Annotated[AstNode[fpp_ast.DefSignal]]
    ) -> Out:
        return self.default(_in)

    def def_state_annotated_node(
        self, _in: In, node: fpp_ast.Annotated[AstNode[fpp_ast.DefState]]
    ) -> Out:
        return self.default(_in)

    def def_state_machine_annotated_node(
        self, _in: In, node: fpp_ast.Annotated[AstNode[fpp_ast.DefStateMachine]]
    ) -> Out:
        if node[1].data.members is not None:
            return self.def_state_machine_annotated_node_internal(
                _in, node, node[1].data.members
            )
        else:
            return self.def_state_machine_annotated_node_external(_in, node)

    def def_state_machine_annotated_node_external(
        self, _in: In, node: fpp_ast.Annotated[AstNode[fpp_ast.DefStateMachine]]
    ) -> Out:
        return self.default(_in)

    def def_state_machine_annotated_node_internal(
        self,
        _in: In,
        node: fpp_ast.Annotated[AstNode[fpp_ast.DefStateMachine]],
        members: List[fpp_ast.StateMachineMember],
    ) -> Out:
        return self.default(_in)

    def def_struct_annotated_node(
        self, _in: In, node: fpp_ast.Annotated[AstNode[fpp_ast.DefStruct]]
    ) -> Out:
        return self.default(_in)

    def def_topology_annotated_node(
        self, _in: In, node: fpp_ast.Annotated[AstNode[fpp_ast.DefTopology]]
    ) -> Out:
        return self.default(_in)

    def expr_array_node(
        self, _in: In, node: AstNode[fpp_ast.Expr], e: fpp_ast.ExprArray
    ) -> Out:
        return self.default(_in)

    def expr_array_subscript_node(
        self, _in: In, node: AstNode[fpp_ast.Expr], e: fpp_ast.ExprArraySubscript
    ) -> Out:
        return self.default(_in)

    def expr_binop_node(
        self, _in: In, node: AstNode[fpp_ast.Expr], e: fpp_ast.ExprBinop
    ) -> Out:
        return self.default(_in)

    def expr_dot_node(
        self, _in: In, node: AstNode[fpp_ast.Expr], e: fpp_ast.ExprDot
    ) -> Out:
        return self.default(_in)

    def expr_ident_node(
        self, _in: In, node: AstNode[fpp_ast.Expr], e: fpp_ast.ExprIdent
    ) -> Out:
        return self.default(_in)

    def expr_literal_bool_node(
        self, _in: In, node: AstNode[fpp_ast.Expr], e: fpp_ast.ExprLiteralBool
    ) -> Out:
        return self.default(_in)

    def expr_literal_float_node(
        self, _in: In, node: AstNode[fpp_ast.Expr], e: fpp_ast.ExprLiteralFloat
    ) -> Out:
        return self.default(_in)

    def expr_literal_int_node(
        self, _in: In, node: AstNode[fpp_ast.Expr], e: fpp_ast.ExprLiteralInt
    ) -> Out:
        return self.default(_in)

    def expr_literal_string_node(
        self, _in: In, node: AstNode[fpp_ast.Expr], e: fpp_ast.ExprLiteralString
    ) -> Out:
        return self.default(_in)

    def expr_paren_node(
        self, _in: In, node: AstNode[fpp_ast.Expr], e: fpp_ast.ExprParen
    ) -> Out:
        return self.default(_in)

    def expr_struct_node(
        self, _in: In, node: AstNode[fpp_ast.Expr], e: fpp_ast.ExprStruct
    ) -> Out:
        return self.default(_in)

    def expr_unop_node(
        self, _in: In, node: AstNode[fpp_ast.Expr], e: fpp_ast.ExprUnop
    ) -> Out:
        return self.default(_in)

    def spec_command_annotated_node(
        self, _in: In, node: fpp_ast.Annotated[AstNode[fpp_ast.SpecCommand]]
    ) -> Out:
        return self.default(_in)

    def spec_comp_instance_annotated_node(
        self, _in: In, node: fpp_ast.Annotated[AstNode[fpp_ast.SpecCompInstance]]
    ) -> Out:
        return self.default(_in)

    def spec_connection_graph_annotated_node(
        self, _in: In, node: fpp_ast.Annotated[AstNode[fpp_ast.SpecConnectionGraph]]
    ) -> Out:
        return self.default(_in)

    def spec_container_annotated_node(
        self, _in: In, node: fpp_ast.Annotated[AstNode[fpp_ast.SpecContainer]]
    ) -> Out:
        return self.default(_in)

    def spec_event_annotated_node(
        self, _in: In, node: fpp_ast.Annotated[AstNode[fpp_ast.SpecEvent]]
    ) -> Out:
        return self.default(_in)

    def spec_include_annotated_node(
        self, _in: In, node: fpp_ast.Annotated[AstNode[fpp_ast.SpecInclude]]
    ) -> Out:
        return self.default(_in)

    def spec_init_annotated_node(
        self, _in: In, node: fpp_ast.Annotated[AstNode[fpp_ast.SpecInit]]
    ) -> Out:
        return self.default(_in)

    def spec_initial_transition_annotated_node(
        self, _in: In, node: fpp_ast.Annotated[AstNode[fpp_ast.SpecInitialTransition]]
    ) -> Out:
        return self.default(_in)

    def spec_internal_port_annotated_node(
        self, _in: In, node: fpp_ast.Annotated[AstNode[fpp_ast.SpecInternalPort]]
    ) -> Out:
        return self.default(_in)

    def spec_loc_annotated_node(
        self, _in: In, node: fpp_ast.Annotated[AstNode[fpp_ast.SpecLoc]]
    ) -> Out:
        return self.default(_in)

    def spec_param_annotated_node(
        self, _in: In, node: fpp_ast.Annotated[AstNode[fpp_ast.SpecParam]]
    ) -> Out:
        return self.default(_in)

    def spec_port_instance_annotated_node(
        self, _in: In, node: fpp_ast.Annotated[AstNode[fpp_ast.SpecPortInstance]]
    ) -> Out:
        return self.default(_in)

    def spec_port_matching_annotated_node(
        self, _in: In, node: fpp_ast.Annotated[AstNode[fpp_ast.SpecPortMatching]]
    ) -> Out:
        return self.default(_in)

    def spec_record_annotated_node(
        self, _in: In, node: fpp_ast.Annotated[AstNode[fpp_ast.SpecRecord]]
    ) -> Out:
        return self.default(_in)

    def spec_state_entry_annotated_node(
        self, _in: In, node: fpp_ast.Annotated[AstNode[fpp_ast.SpecStateEntry]]
    ) -> Out:
        return self.default(_in)

    def spec_state_exit_annotated_node(
        self, _in: In, node: fpp_ast.Annotated[AstNode[fpp_ast.SpecStateExit]]
    ) -> Out:
        return self.default(_in)

    def spec_state_machine_instance_annotated_node(
        self,
        _in: In,
        node: fpp_ast.Annotated[AstNode[fpp_ast.SpecStateMachineInstance]],
    ) -> Out:
        return self.default(_in)

    def spec_state_transition_annotated_node(
        self, _in: In, node: fpp_ast.Annotated[AstNode[fpp_ast.SpecStateTransition]]
    ) -> Out:
        return self.default(_in)

    def spec_tlm_channel_annotated_node(
        self, _in: In, node: fpp_ast.Annotated[AstNode[fpp_ast.SpecTlmChannel]]
    ) -> Out:
        return self.default(_in)

    def spec_tlm_packet_annotated_node(
        self, _in: In, node: fpp_ast.Annotated[AstNode[fpp_ast.SpecTlmPacket]]
    ) -> Out:
        return self.default(_in)

    def spec_tlm_packet_set_annotated_node(
        self, _in: In, node: fpp_ast.Annotated[AstNode[fpp_ast.SpecTlmPacketSet]]
    ) -> Out:
        return self.default(_in)

    def spec_top_import_annotated_node(
        self, _in: In, node: fpp_ast.Annotated[AstNode[fpp_ast.SpecImport]]
    ) -> Out:
        return self.default(_in)

    def spec_interface_import_annotated_node(
        self, _in: In, node: fpp_ast.Annotated[AstNode[fpp_ast.SpecImport]]
    ) -> Out:
        return self.default(_in)

    def trans_unit(self, _in: In, tu: fpp_ast.TransUnit) -> Out:
        return self.default(_in)

    def type_name_bool_node(self, _in: In, node: AstNode[fpp_ast.TypeName]) -> Out:
        return self.default(_in)

    def type_name_float_node(
        self, _in: In, node: AstNode[fpp_ast.TypeName], tn: fpp_ast.TypeNameFloat
    ) -> Out:
        return self.default(_in)

    def type_name_int_node(
        self, _in: In, node: AstNode[fpp_ast.TypeName], tn: fpp_ast.TypeNameInt
    ) -> Out:
        return self.default(_in)

    def type_name_qual_ident_node(
        self, _in: In, node: AstNode[fpp_ast.TypeName], tn: fpp_ast.TypeNameQualIdent
    ) -> Out:
        return self.default(_in)

    def type_name_string_node(
        self, _in: In, node: AstNode[fpp_ast.TypeName], tn: fpp_ast.TypeNameString
    ) -> Out:
        return self.default(_in)

    def match_component_member(self, _in: In, member: fpp_ast.ComponentMember) -> Out:
        pre, node, post = member.node
        match node:
            case fpp_ast.ComponentMemberDefAbsType(node1):
                return self.def_abs_type_annotated_node(_in, (pre, node1, post))
            case fpp_ast.ComponentMemberDefAliasType(node1):
                return self.def_alias_type_annotated_node(_in, (pre, node1, post))
            case fpp_ast.ComponentMemberDefArray(node1):
                return self.def_array_annotated_node(_in, (pre, node1, post))
            case fpp_ast.ComponentMemberDefConstant(node1):
                return self.def_constant_annotated_node(_in, (pre, node1, post))
            case fpp_ast.ComponentMemberDefEnum(node1):
                return self.def_enum_annotated_node(_in, (pre, node1, post))
            case fpp_ast.ComponentMemberDefStateMachine(node1):
                return self.def_state_machine_annotated_node(_in, (pre, node1, post))
            case fpp_ast.ComponentMemberDefStruct(node1):
                return self.def_struct_annotated_node(_in, (pre, node1, post))
            case fpp_ast.ComponentMemberSpecCommand(node1):
                return self.spec_command_annotated_node(_in, (pre, node1, post))
            case fpp_ast.ComponentMemberSpecContainer(node1):
                return self.spec_container_annotated_node(_in, (pre, node1, post))
            case fpp_ast.ComponentMemberSpecEvent(node1):
                return self.spec_event_annotated_node(_in, (pre, node1, post))
            case fpp_ast.ComponentMemberSpecInclude(node1):
                return self.spec_include_annotated_node(_in, (pre, node1, post))
            case fpp_ast.ComponentMemberSpecInternalPort(node1):
                return self.spec_internal_port_annotated_node(_in, (pre, node1, post))
            case fpp_ast.ComponentMemberSpecParam(node1):
                return self.spec_param_annotated_node(_in, (pre, node1, post))
            case fpp_ast.ComponentMemberSpecPortInstance(node1):
                return self.spec_port_instance_annotated_node(_in, (pre, node1, post))
            case fpp_ast.ComponentMemberSpecPortMatching(node1):
                return self.spec_port_matching_annotated_node(_in, (pre, node1, post))
            case fpp_ast.ComponentMemberSpecRecord(node1):
                return self.spec_record_annotated_node(_in, (pre, node1, post))
            case fpp_ast.ComponentMemberSpecStateMachineInstance(node1):
                return self.spec_state_machine_instance_annotated_node(
                    _in, (pre, node1, post)
                )
            case fpp_ast.ComponentMemberSpecTlmChannel(node1):
                return self.spec_tlm_channel_annotated_node(_in, (pre, node1, post))
            case fpp_ast.ComponentMemberSpecImportInterface(node1):
                return self.spec_interface_import_annotated_node(
                    _in, (pre, node1, post)
                )
            case _:
                return self.default(_in)

    def match_interface_member(self, _in: In, member: fpp_ast.InterfaceMember):
        pre, node, post = member.node
        match node:
            case fpp_ast.InterfaceMemberSpecPortInstance(node1):
                return self.spec_port_instance_annotated_node(_in, (pre, node1, post))
            case fpp_ast.InterfaceMemberSpecImportInterface(node1):
                return self.spec_interface_import_annotated_node(
                    _in, (pre, node1, post)
                )

    def match_expr_node(self, _in: In, node: AstNode[fpp_ast.Expr]) -> Out:
        expr = node.data
        match expr:
            case fpp_ast.ExprArray():
                return self.expr_array_node(_in, node, expr)
            case fpp_ast.ExprArraySubscript():
                return self.expr_array_subscript_node(_in, node, expr)
            case fpp_ast.ExprBinop():
                return self.expr_binop_node(_in, node, expr)
            case fpp_ast.ExprDot():
                return self.expr_dot_node(_in, node, expr)
            case fpp_ast.ExprIdent():
                return self.expr_ident_node(_in, node, expr)
            case fpp_ast.ExprLiteralBool():
                return self.expr_literal_bool_node(_in, node, expr)
            case fpp_ast.ExprLiteralFloat():
                return self.expr_literal_float_node(_in, node, expr)
            case fpp_ast.ExprLiteralInt():
                return self.expr_literal_int_node(_in, node, expr)
            case fpp_ast.ExprLiteralString():
                return self.expr_literal_string_node(_in, node, expr)
            case fpp_ast.ExprParen():
                return self.expr_paren_node(_in, node, expr)
            case fpp_ast.ExprStruct():
                return self.expr_struct_node(_in, node, expr)
            case fpp_ast.ExprUnop():
                return self.expr_unop_node(_in, node, expr)
            case _:
                return self.default(_in)

    def match_module_member(self, _in: In, member: fpp_ast.ModuleMember) -> Out:
        pre, node, post = member.node
        match node:
            case fpp_ast.ModuleMemberDefAbsType():
                return self.def_abs_type_annotated_node(_in, (pre, node.node, post))
            case fpp_ast.ModuleMemberDefAliasType():
                return self.def_alias_type_annotated_node(_in, (pre, node.node, post))
            case fpp_ast.ModuleMemberDefArray():
                return self.def_array_annotated_node(_in, (pre, node.node, post))
            case fpp_ast.ModuleMemberDefComponent():
                return self.def_component_annotated_node(_in, (pre, node.node, post))
            case fpp_ast.ModuleMemberDefInterface():
                return self.def_interface_annotated_node(_in, (pre, node.node, post))
            case fpp_ast.ModuleMemberDefComponentInstance():
                return self.def_component_instance_annotated_node(
                    _in, (pre, node.node, post)
                )
            case fpp_ast.ModuleMemberDefConstant():
                return self.def_constant_annotated_node(_in, (pre, node.node, post))
            case fpp_ast.ModuleMemberDefEnum():
                return self.def_enum_annotated_node(_in, (pre, node.node, post))
            case fpp_ast.ModuleMemberDefModule():
                return self.def_module_annotated_node(_in, (pre, node.node, post))
            case fpp_ast.ModuleMemberDefPort():
                return self.def_port_annotated_node(_in, (pre, node.node, post))
            case fpp_ast.ModuleMemberDefStateMachine():
                return self.def_state_machine_annotated_node(
                    _in, (pre, node.node, post)
                )
            case fpp_ast.ModuleMemberDefStruct():
                return self.def_struct_annotated_node(_in, (pre, node.node, post))
            case fpp_ast.ModuleMemberDefTopology():
                return self.def_topology_annotated_node(_in, (pre, node.node, post))
            case fpp_ast.ModuleMemberSpecInclude():
                return self.spec_include_annotated_node(_in, (pre, node.node, post))
            case fpp_ast.ModuleMemberSpecLoc():
                return self.spec_loc_annotated_node(_in, (pre, node.node, post))
            case _:
                return self.default(_in)

    def match_state_machine_member(
        self, _in: In, member: fpp_ast.StateMachineMember
    ) -> Out:
        pre, node, post = member.node
        match node:
            case fpp_ast.StateMachineMemberDefAction():
                return self.def_action_annotated_node(_in, (pre, node.node, post))
            case fpp_ast.StateMachineMemberDefGuard():
                return self.def_guard_annotated_node(_in, (pre, node.node, post))
            case fpp_ast.StateMachineMemberDefChoice():
                return self.def_choice_annotated_node(_in, (pre, node.node, post))
            case fpp_ast.StateMachineMemberDefSignal():
                return self.def_signal_annotated_node(_in, (pre, node.node, post))
            case fpp_ast.StateMachineMemberDefState():
                return self.def_state_annotated_node(_in, (pre, node.node, post))
            case fpp_ast.StateMachineMemberSpecInitialTransition():
                return self.spec_initial_transition_annotated_node(
                    _in, (pre, node.node, post)
                )
            case _:
                return self.default(_in)

    def match_state_member(self, _in: In, member: fpp_ast.StateMember) -> Out:
        pre, node, post = member.node
        match node:
            case fpp_ast.StateMemberDefChoice():
                return self.def_choice_annotated_node(_in, (pre, node.node, post))
            case fpp_ast.StateMemberDefState():
                return self.def_state_annotated_node(_in, (pre, node.node, post))
            case fpp_ast.StateMemberSpecInitialTransition():
                return self.spec_initial_transition_annotated_node(
                    _in, (pre, node.node, post)
                )
            case fpp_ast.StateMemberSpecStateEntry():
                return self.spec_state_entry_annotated_node(_in, (pre, node.node, post))
            case fpp_ast.StateMemberSpecStateExit():
                return self.spec_state_exit_annotated_node(_in, (pre, node.node, post))
            case fpp_ast.StateMemberSpecStateTransition():
                return self.spec_state_transition_annotated_node(
                    _in, (pre, node.node, post)
                )
            case _:
                return self.default(_in)

    def match_tlm_packet_set_member(
        self, _in: In, member: fpp_ast.TlmPacketSetMember
    ) -> Out:
        pre, node, post = member.node

        match node:
            case fpp_ast.TlmPacketSetMemberSpecTlmPacket():
                return self.spec_tlm_packet_annotated_node(_in, (pre, node.node, post))
            case fpp_ast.TlmPacketSetMemberSpecInclude():
                return self.spec_include_annotated_node(_in, (pre, node.node, post))
            case _:
                raise InternalError("Could not match TlmPacketSetMember")

    def match_topology_member(self, _in: In, member: fpp_ast.TopologyMember) -> Out:
        pre, node, post = member.node

        match node:
            case fpp_ast.TopologyMemberSpecCompInstance():
                return self.spec_comp_instance_annotated_node(
                    _in, (pre, node.node, post)
                )
            case fpp_ast.TopologyMemberSpecConnectionGraph():
                return self.spec_connection_graph_annotated_node(
                    _in, (pre, node.node, post)
                )
            case fpp_ast.TopologyMemberSpecInclude():
                return self.spec_include_annotated_node(_in, (pre, node.node, post))
            case fpp_ast.TopologyMemberSpecTlmPacketSet():
                return self.spec_tlm_packet_set_annotated_node(
                    _in, (pre, node.node, post)
                )
            case fpp_ast.TopologyMemberSpecTopImport():
                return self.spec_top_import_annotated_node(_in, (pre, node.node, post))
            case _:
                return self.default(_in)

    def match_tu_member(self, _in: In, member: fpp_ast.TUMember) -> Out:
        return self.match_module_member(_in, member)

    def match_type_name_node(self, _in: In, node: AstNode[fpp_ast.TypeName]) -> Out:
        data = node.data

        match data:
            case fpp_ast.TypeNameBool():
                return self.type_name_bool_node(_in, node)
            case fpp_ast.TypeNameFloat():
                return self.type_name_float_node(_in, node, data)
            case fpp_ast.TypeNameInt():
                return self.type_name_int_node(_in, node, data)
            case fpp_ast.TypeNameQualIdent():
                return self.type_name_qual_ident_node(_in, node, data)
            case fpp_ast.TypeNameString():
                return self.type_name_string_node(_in, node, data)
            case _:
                return self.default(_in)
