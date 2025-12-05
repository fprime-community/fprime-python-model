from typing import List, TypeVar, Callable, TypeAlias, Optional
from fprime_python_model.fpp_ast import fpp_ast
from fprime_python_model.fpp_ast.fpp_ast_node import AstNode
from fprime_python_model.utils.fpp_ast_visitor import AstVisitor, In
from fprime_python_model.utils.line_utils import (
    LineUtils,
    Line,
    Lines,
    add_prefix_and_suffix,
    blank,
)
from fprime_python_model.utils.error import InternalError
from fprime_python_model.fpp_ast.fpp_reserved_words import keywords

T = TypeVar("T")

Out: TypeAlias = Lines


class FppWriter(AstVisitor, LineUtils):

    def write_trans_unit(self, tu: fpp_ast.TransUnit) -> Out:
        return self.trans_unit(None, tu)

    def apply_to_data(self, f: Callable[[T], Out]) -> Callable[[AstNode[T]], Out]:
        def inner(a: fpp_ast.AstNode[T]):
            return f(a.data)

        return inner

    def ident(self, id: fpp_ast.Ident) -> str:
        return f"${id}" if id in keywords else id

    def ident_as_lines(self, x) -> Out:
        return Lines(self.lines(self.ident(x)))

    def blank_separated(self, f: Callable[[T], Lines], items: List[T]) -> Lines:
        if not items:
            return Lines([])
        result: List[Line] = []
        for i, item in enumerate(items):
            result.extend(f(item))
            if i < len(items) - 1:
                result.append(blank())
        return Lines(result)

    def annotate(self, pre: List[str], lines: Out, post: List[str]) -> Lines:
        pre1 = [self.line(f"@ {s}") for s in pre]
        post1 = [self.line(f"@< {s}") for s in post]
        return Lines(pre1 + lines.lines).join(" ", Lines(post1))

    def annotate_node(
        self, f: Callable[[T], Out]
    ) -> Callable[[fpp_ast.Annotated[AstNode]], Out]:
        def inner(a_node: fpp_ast.Annotated[AstNode]) -> Out:
            a1, node, a2 = a_node
            return self.annotate(a1, f(node.data), a2)

        return inner

    def string(self, s: str) -> Out:
        s = s.replace("\\", "\\\\").replace('"', '\\"')

        ss = s.split("\n")

        if not ss:
            return Lines(self.lines('""'))
        elif len(ss) == 1:
            return Lines(self.lines(f'"{ss[0]}"'))
        else:
            return Lines(
                self.lines('"""') + [self.line(x) for x in ss] + self.lines('"""')
            )

    def unop(self, op: fpp_ast.Unop) -> str:
        return str(op)

    def binop(self, op: fpp_ast.Binop) -> str:
        return f" {str(op)} "

    def add_braces(self, ls: Out) -> Out:
        return Lines(self.lines("{") + list(map(self.indent_in, ls)) + self.lines("}"))

    def add_braces_if_non_empty(self, ls: Out) -> Out:
        if ls.lines:
            return self.add_braces(ls)
        else:
            return ls

    def action_list(self, actions: List[AstNode[fpp_ast.Ident]]):
        if not actions:
            return Lines(self.lines(""))

        inner = [
            self.indent_in(y)
            for action in actions
            for y in self.apply_to_data(self.ident_as_lines)(action)
        ]

        return Lines(self.lines("do")).join(
            " ", Lines(self.lines("{") + inner + self.lines("}"))
        )

    def port_instance_id(self, pii: fpp_ast.PortInstanceIdentifier) -> Out:
        return self.qual_ident(pii.component_instance.data).add_suffix(
            f".{self.ident(pii.port_name.data)}"
        )

    def tlm_channel_id(self, tci: fpp_ast.TlmChannelIdentifier) -> Out:
        return self.qual_ident(tci.component_instance.data).add_suffix(
            f".{self.ident(tci.channel_name.data)}"
        )

    def bracket_expr_node(self, en: AstNode[fpp_ast.Expr]) -> Out:
        return self.expr_node(en).add_prefix_and_suffix("[", "]")

    def connection(self, c: fpp_ast.Connection) -> Out:
        return (
            Lines(self.lines("unmatched" if c.is_unmatched else ""))
            .join("", self.port_instance_id(c.from_port.data))
            .join_opt(c.from_index, "", self.bracket_expr_node)
            .join(" -> ", self.port_instance_id(c.to_port.data))
            .join_opt(c.to_index, "", self.bracket_expr_node)
        )

    def qual_ident_string(self, qid: fpp_ast.QualIdent) -> str:
        if isinstance(qid, fpp_ast.Unqualified):
            return self.ident(qid.name)
        elif isinstance(qid, fpp_ast.Qualified):
            return (
                self.qual_ident_string(qid.qualifier.data)
                + "."
                + self.ident(qid.name.data)
            )
        else:
            raise InternalError("Invalid qual ident")

    def qual_ident(self, qid: fpp_ast.QualIdent) -> Out:
        return Lines(self.lines(self.qual_ident_string(qid)))

    def queue_full(self, qf: fpp_ast.QueueFull) -> Out:
        return Lines(self.lines(str(qf)))

    def spec_init(self, si: fpp_ast.SpecInit) -> Out:
        return (
            self.expr_node(si.phase)
            .add_prefix("phase ")
            .join_no_indent(" ", self.string(si.code))
        )

    def formal_param(self, fp: fpp_ast.FormalParam) -> Out:
        if fp.kind == fpp_ast.FormalParamKind.REF:
            prefix = "ref "
        else:
            prefix = ""

        name = prefix + self.ident(fp.name)

        return Lines(self.lines(name)).join(": ", self.type_name_node(fp.type_name))

    def formal_param_list(self, fpl: fpp_ast.FormalParamList) -> Out:
        if not fpl:
            return Lines(self.lines(""))
        else:
            annotated_param_lines = []
            for formal_param in fpl:
                param = formal_param
                for annotated in self.annotate_node(self.formal_param)(param):
                    annotated_param_lines.append(self.indent_in(annotated))

            return Lines(self.lines("(") + annotated_param_lines + self.lines(")"))

    def component_member(self, member: fpp_ast.ComponentMember) -> Out:
        pre, _, post = member.node
        l = self.match_component_member(None, member)
        return self.annotate(pre, l, post)

    def interface_member(self, member: fpp_ast.InterfaceMember) -> Out:
        pre, _, post = member.node
        l = self.match_interface_member(None, member)
        return self.annotate(pre, l, post)

    def state_member(self, member: fpp_ast.StateMember) -> Out:
        pre, _, post = member.node
        l = self.match_state_member(None, member)
        return self.annotate(pre, l, post)

    def struct_member(self, member: fpp_ast.StructMember) -> Out:
        return Lines(self.lines(self.ident(member.name))).join_no_indent(
            " = ", self.expr_node(member.value)
        )

    def struct_type_member(self, member: fpp_ast.StructTypeMember) -> Out:
        return (
            Lines(self.lines(f"{self.ident(member.name)}:"))
            .join_opt(member.size, " ", self.bracket_expr_node)
            .join_no_indent(" ", self.type_name_node(member.type_name))
            .join_opt(member.format, " format ", self.apply_to_data(self.string))
        )

    def transition_expr(self, transition: fpp_ast.TransitionExpr) -> Out:
        sep = "enter " if not transition.actions else " enter "

        return self.action_list(transition.actions).join_no_indent(
            sep, self.qual_ident(transition.target.data)
        )

    def module_member(self, member: fpp_ast.ModuleMember) -> Out:
        pre, _, post = member.node
        l = self.match_module_member(None, member)
        return self.annotate(pre, l, post)

    def state_machine_member(self, member: fpp_ast.StateMachineMember) -> Out:
        pre, _, post = member.node
        l = self.match_state_machine_member(None, member)
        return self.annotate(pre, l, post)

    def tlm_packet_member(self, member: fpp_ast.TlmPacketMember) -> Out:
        match member:
            case fpp_ast.TlmPacketMemberSpecInclude(node):
                return self.spec_include_annotated_node(None, ([], node, []))
            case fpp_ast.TlmPacketMemberTlmChannelIdentifier(node):
                return self.tlm_channel_id(node.data)
            case _:
                return self.default(None)

    def tlm_packet_set_member(self, member: fpp_ast.TlmPacketSetMember) -> Out:
        pre, _, post = member.node
        l = self.match_tlm_packet_set_member(None, member)
        return self.annotate(pre, l, post)

    def topology_member(self, member: fpp_ast.TopologyMember) -> Out:
        pre, _, post = member.node
        l = self.match_topology_member(None, member)
        return self.annotate(pre, l, post)

    def trans_unit(self, _in, tu) -> Out:
        return self.blank_separated(self.tu_member, tu.members)

    def transition_or_do(self, tod: fpp_ast.TransitionOrDo) -> Out:
        if isinstance(tod, fpp_ast.Transition):
            return self.transition_expr(tod.transition.data)
        elif isinstance(tod, fpp_ast.Do):
            return self.action_list(tod.actions)
        else:
            raise InternalError("Invalid transition or do")

    def def_enum_constant(self, dec: fpp_ast.DefEnumConstant) -> Out:
        return Lines(self.lines(self.ident(dec.name))).join_opt(
            dec.value, " = ", self.expr_node
        )

    def def_alias_type_annotated_node(
        self, _in: In, a_node: fpp_ast.Annotated[AstNode[fpp_ast.DefAliasType]]
    ):
        _, node, _ = a_node
        data = node.data
        return Lines(
            self.lines(
                self.prefix_with_dictionary(
                    f"type {self.ident(data.name)} = ", data.is_dictionary_def
                )
            )
        ).join("", self.type_name_node(data.type_name))

    def def_abs_type_annotated_node(
        self, _in: In, a_node: fpp_ast.Annotated[AstNode[fpp_ast.DefAbsType]]
    ):
        _, node, _ = a_node
        data = node.data
        return Lines(self.lines(f"type {self.ident(data.name)}"))

    def def_action_annotated_node(
        self, _in: In, a_node: fpp_ast.Annotated[AstNode[fpp_ast.DefAction]]
    ):
        _, node, _ = a_node
        data = node.data
        return Lines(self.lines(f"action {self.ident(data.name)}")).join_opt(
            data.type_name, ": ", self.type_name_node
        )

    def def_array_annotated_node(
        self, _in: In, a_node: fpp_ast.Annotated[AstNode[fpp_ast.DefArray]]
    ):
        _, node, _ = a_node
        data = node.data
        return (
            Lines(
                self.lines(
                    self.prefix_with_dictionary(
                        f"array {self.ident(data.name)} = [", data.is_dictionary_def
                    )
                )
            )
            .join_no_indent("", self.expr_node(data.size))
            .join_no_indent("] ", self.type_name_node(data.elt_type))
            .join_opt(data.default, " default ", self.expr_node)
            .join_opt(data.format, " format ", self.apply_to_data(self.string))
        )

    def def_choice_annotated_node(
        self, _in: In, a_node: fpp_ast.Annotated[AstNode[fpp_ast.DefChoice]]
    ):
        _, node, _ = a_node
        data = node.data

        start_lines = self.lines(f"choice {self.ident(data.name)}" + " {")

        guard_lines = Lines(self.lines(f"if {data.guard.data}")).join(
            " ", self.transition_expr(data.if_transition.data)
        )
        indented_guard = Lines([self.indent_in(line) for line in guard_lines.lines])

        else_lines = Lines(self.lines("else")).join(
            " ", self.transition_expr(data.else_transition.data)
        )

        all_lines = (
            start_lines
            + indented_guard.join_with_break("", else_lines).lines
            + self.lines("}")
        )

        return Lines(all_lines)

    def def_component_annotated_node(
        self, _in, a_node: fpp_ast.Annotated[AstNode[fpp_ast.DefComponent]]
    ):
        _, node, _ = a_node
        data = node.data
        kind = str(data.kind)
        lines = [
            self.line(f"{kind} component {self.ident(data.name)}" + " {"),
            blank(),
        ]

        members = self.blank_separated(self.component_member, data.members)
        lines.extend(self.indent_in(m) for m in members)
        lines.extend([blank(), self.line("}")])

        return Lines(lines)

    def def_component_instance_annotated_node(
        self, _in, a_node: fpp_ast.Annotated[AstNode[fpp_ast.DefComponentInstance]]
    ):
        def init_specs(ls: List[fpp_ast.Annotated[AstNode[fpp_ast.SpecInit]]]):
            annotated = []
            for l in ls:
                annotated += self.annotate_node(self.spec_init)(l).lines
            return self.add_braces_if_non_empty(Lines(annotated))

        _, node, _ = a_node
        data = node.data

        return (
            Lines(self.lines(f"instance {self.ident(data.name)}"))
            .join_no_indent(": ", self.qual_ident(data.component.data))
            .join_no_indent(" base id ", self.expr_node(data.base_id))
            .join_opt_with_break(
                data.impl_type, "type ", self.apply_to_data(self.string)
            )
            .join_opt_with_break(data.file, "at ", self.apply_to_data(self.string))
            .join_opt_with_break(data.queue_size, "queue size ", self.expr_node)
            .join_opt_with_break(data.stack_size, "stack size ", self.expr_node)
            .join_opt_with_break(data.priority, "priority ", self.expr_node)
            .join_opt_with_break(data.cpu, "cpu ", self.expr_node)
            .join_with_break("", init_specs(data.init_specs))
        )

    def def_interface_annotated_node(
        self, _in, a_node: fpp_ast.Annotated[AstNode[fpp_ast.DefInterface]]
    ):
        _, node, _ = a_node
        data = node.data
        lines = [self.line(f"interface {self.ident(data.name)}" + " {"), blank()]
        members = self.blank_separated(self.interface_member, data.members)
        lines.extend(self.indent_in(m) for m in members)
        lines.extend([blank(), self.line("}")])

        return Lines(lines)

    def def_constant_annotated_node(
        self, _in, a_node: fpp_ast.Annotated[AstNode[fpp_ast.DefConstant]]
    ):
        _, node, _ = a_node
        data = node.data
        return Lines(
            self.lines(
                self.prefix_with_dictionary(
                    f"constant {self.ident(data.name)}", data.is_dictionary_def
                )
            )
        ).join(" = ", self.expr_node(data.value))

    def def_enum_annotated_node(
        self, _in, a_node: fpp_ast.Annotated[AstNode[fpp_ast.DefEnum]]
    ):
        _, node, _ = a_node
        data = node.data

        lines = Lines(
            self.lines(
                self.prefix_with_dictionary(
                    f"enum {self.ident(data.name)}", data.is_dictionary_def
                )
            )
        ).join_opt(data.type_name, ": ", self.type_name_node)

        constants_lines = []
        for const in data.constants:
            for annotated in self.annotate_node(self.def_enum_constant)(const):
                constants_lines.append(annotated)

        return lines.join_no_indent(
            " ", self.add_braces(Lines(constants_lines))
        ).join_opt(data.default, " default ", self.expr_node)

    def def_guard_annotated_node(
        self, _in, a_node: fpp_ast.Annotated[AstNode[fpp_ast.DefGuard]]
    ):
        _, node, _ = a_node
        data = node.data
        return Lines(self.lines(f"guard {self.ident(data.name)}")).join_opt(
            data.type_name, ": ", self.type_name_node
        )

    def def_module_annotated_node(
        self, _in, a_node: fpp_ast.Annotated[AstNode[fpp_ast.DefModule]]
    ):
        _, node, _ = a_node
        data = node.data
        lines = [self.line(f"module {self.ident(data.name)}" + " {"), blank()]
        members = self.blank_separated(self.module_member, data.members)
        lines.extend(self.indent_in(m) for m in members)
        lines.extend([blank(), self.line("}")])
        return Lines(lines)

    def def_port_annotated_node(
        self, _in, a_node: fpp_ast.Annotated[AstNode[fpp_ast.DefPort]]
    ):
        _, node, _ = a_node
        data = node.data
        return (
            Lines(self.lines(f"port {self.ident(data.name)}"))
            .join("", self.formal_param_list(data.params))
            .join_opt(data.return_type, " -> ", self.type_name_node)
        )

    def def_signal_annotated_node(
        self, _in, a_node: fpp_ast.Annotated[AstNode[fpp_ast.DefSignal]]
    ):
        _, node, _ = a_node
        data = node.data
        return Lines(self.lines(f"signal {self.ident(data.name)}")).join_opt(
            data.type_name, ": ", self.type_name_node
        )

    def def_state_annotated_node(
        self, _in, a_node: fpp_ast.Annotated[AstNode[fpp_ast.DefState]]
    ):
        _, node, _ = a_node
        data = node.data
        name = self.ident(data.name)
        if not data.members:
            return Lines(self.lines(f"state {name}"))
        else:
            lines = [self.line(f"state {name}" + " {"), blank()]
            members = self.blank_separated(self.state_member, data.members)
            lines.extend(self.indent_in(m) for m in members)
            lines.extend([blank(), self.line("}")])
            return Lines(lines)

    def def_state_machine_annotated_node(
        self, _in, a_node: fpp_ast.Annotated[AstNode[fpp_ast.DefStateMachine]]
    ):
        _, node, _ = a_node
        data = node.data
        name = self.ident(data.name)
        if not data.members:
            return Lines(self.lines(f"state machine {name}"))
        else:
            lines = [self.line(f"state machine {name}" + " {"), blank()]
            members = self.blank_separated(self.state_machine_member, data.members)
            lines.extend(self.indent_in(m) for m in members)
            lines.extend([blank(), self.line("}")])
            return Lines(lines)

    def def_struct_annotated_node(
        self, _in, a_node: fpp_ast.Annotated[AstNode[fpp_ast.DefStruct]]
    ):
        _, node, _ = a_node
        data = node.data
        struct_lines = []
        for m in data.members:
            out: Lines = self.annotate_node(self.struct_type_member)(m)
            struct_lines += out.lines
        return (
            Lines(
                self.lines(
                    self.prefix_with_dictionary(
                        f"struct {self.ident(data.name)}", data.is_dictionary_def
                    )
                )
            )
            .join_no_indent(" ", self.add_braces(Lines(struct_lines)))
            .join_opt(data.default, " default ", self.expr_node)
        )

    def def_topology_annotated_node(
        self, _in, a_node: fpp_ast.Annotated[AstNode[fpp_ast.DefTopology]]
    ):
        _, node, _ = a_node
        data = node.data
        return Lines(
            [self.line(f"topology {self.ident(data.name)} " + "{"), blank()]
            + list(
                map(
                    self.indent_in,
                    self.blank_separated(self.topology_member, data.members),
                )
            )
            + [blank(), self.line("}")]
        )

    def expr_array_node(self, _in, node, e):
        return Lines(
            [self.line("[")]
            + [self.indent_in(x) for elt in e.elts for x in self.expr_node(elt)]
            + [self.line("]")]
        )

    def expr_array_subscript_node(
        self, _in, node: AstNode[fpp_ast.Expr], e: fpp_ast.ExprArraySubscript
    ):
        return self.expr_node(e.e1).join(
            "", self.expr_node(e.e2).add_prefix_and_suffix("[", "]")
        )

    def expr_dot_node(self, _in, node, e):
        return self.expr_node(e.e).join_no_indent(".", Lines(self.lines(e.id.data)))

    def expr_ident_node(self, _in, node, e):
        return Lines(self.lines(e.value))

    def expr_literal_bool_node(self, _in, node, e):
        return Lines(self.lines(str(e.value)))

    def expr_literal_float_node(self, _in, node, e):
        return Lines(self.lines(e.value))

    def expr_literal_int_node(self, _in, node, e):
        return Lines(self.lines(e.value))

    def expr_literal_string_node(self, _in, node, e):
        return self.string(e.value)

    def expr_paren_node(self, _in, node, e):
        return Lines(add_prefix_and_suffix("(", self.expr_node(e.e).lines, ")"))

    def expr_struct_node(self, _in, node, e):
        struct_lines = []
        for m in e.members:
            out: Lines = self.apply_to_data(self.struct_member)(m)
            struct_lines += out.lines
        return self.add_braces(Lines(struct_lines))

    def expr_unop_node(self, _in, node, e):
        return Lines(self.lines(self.unop(e.op))).join_no_indent(
            "", self.expr_node(e.e)
        )

    def expr_binop_node(
        self, _in: In, node: AstNode[fpp_ast.Expr], e: fpp_ast.ExprBinop
    ):
        return self.expr_node(e.e1).join_no_indent(
            self.binop(e.op), self.expr_node(e.e2)
        )

    def spec_command_annotated_node(
        self, _in, a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecCommand]]
    ):
        _, node, _ = a_node
        data = node.data
        kind = str(data.kind)
        return (
            Lines(self.lines(f"{kind} command {self.ident(data.name)}"))
            .join("", self.formal_param_list(data.params))
            .join_opt_with_break(data.opcode, "opcode ", self.expr_node)
            .join_opt_with_break(data.priority, "priority ", self.expr_node)
            .join_opt_with_break(
                data.queue_full, "", self.apply_to_data(self.queue_full)
            )
        )

    def spec_comp_instance_annotated_node(
        self, _in, a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecCompInstance]]
    ):
        _, node, _ = a_node
        data = node.data
        visibility = "" if data.visibility == fpp_ast.Visibility.PUBLIC else "private "
        return Lines(self.lines(visibility)).join(
            "instance ", self.qual_ident(data.instance.data)
        )

    def spec_connection_graph_annotated_node(
        self, _in, a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecConnectionGraph]]
    ):
        def direct(scg: fpp_ast.Direct) -> Lines:
            connection_lines = []
            for c in scg.connections:
                connection_lines += self.connection(c).lines
            return Lines(
                self.lines(f"connections {self.ident(scg.name)}")
            ).join_no_indent(" ", self.add_braces(Lines(connection_lines)))

        def pattern(scg: fpp_ast.Pattern) -> Lines:
            target_lines = []
            for t in scg.targets:
                out: Lines = self.apply_to_data(self.qual_ident)(t)
                target_lines += out.lines
            return Lines(
                self.lines(
                    f"{str(scg.kind)} connections instance {self.qual_ident(scg.source.data)}"
                )
            ).join_no_indent(" ", self.add_braces_if_non_empty(Lines(target_lines)))

        _, node, _ = a_node

        if isinstance(node.data, fpp_ast.Direct):
            return direct(node.data)
        elif isinstance(node.data, fpp_ast.Pattern):
            return pattern(node.data)
        return Lines(self.lines(""))

    def spec_container_annotated_node(
        self, _in, a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecContainer]]
    ):
        _, node, _ = a_node
        data = node.data
        return (
            Lines(self.lines(f"product container {self.ident(data.name)}"))
            .join_opt(data.id, " id ", self.expr_node)
            .join_opt(data.default_priority, " default priority ", self.expr_node)
        )

    def spec_event_annotated_node(
        self, _in, a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecEvent]]
    ):
        def event_throttle(throttle: AstNode[fpp_ast.EventThrottle]):
            return (
                self.expr_node(throttle.data.count)
                .add_prefix("throttle ")
                .join_opt(throttle.data.every, " every ", self.expr_node)
            )

        _, node, _ = a_node
        data = node.data
        severity = str(data.severity)
        return (
            Lines(self.lines(f"event {self.ident(data.name)}"))
            .join("", self.formal_param_list(data.params))
            .join_with_break("severity ", Lines(self.lines(severity)))
            .join_opt_with_break(data.id, "id ", self.expr_node)
            .join_with_break("format ", self.string(data.format.data))
            .join_opt_with_break(data.throttle, "", event_throttle)
        )

    def spec_include_annotated_node(
        self, _in, a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecInclude]]
    ):
        _, node, _ = a_node
        data = node.data
        return Lines(self.lines("include")).join(" ", self.string(data.file.data))

    def spec_initial_transition_annotated_node(
        self, _in, a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecInitialTransition]]
    ):
        _, node, _ = a_node
        data = node.data
        return Lines(self.lines("initial ")).join(
            "", self.transition_expr(data.transition.data)
        )

    def spec_interface_import_annotated_node(
        self, _in, a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecImport]]
    ):
        _, node, _ = a_node
        data = node.data
        return self.qual_ident(data.sym.data).add_prefix("import ")

    def spec_internal_port_annotated_node(
        self, _in, a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecInternalPort]]
    ):
        _, node, _ = a_node
        data = node.data
        return (
            Lines(self.lines(f"internal port {self.ident(data.name)}"))
            .join("", self.formal_param_list(data.params))
            .join_opt_with_break(data.priority, "priority ", self.expr_node)
            .join_opt_with_break(data.queue_full, "", self.queue_full)
        )

    def spec_loc_annotated_node(
        self, _in, a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecLoc]]
    ):
        _, node, _ = a_node
        data = node.data
        kind = str(data.kind)
        return (
            Lines(
                self.lines(
                    f"locate {self.prefix_with_dictionary(kind, data.is_dictionary_def)}"
                )
            )
            .join_no_indent(" ", self.qual_ident(data.symbol.data))
            .join_no_indent(" at ", self.string(data.file.data))
        )

    def spec_param_annotated_node(
        self, _in, a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecParam]]
    ):
        _, node, _ = a_node
        data = node.data
        external = "external " if data.is_external else ""
        return (
            Lines(self.lines(f"{external}param {self.ident(data.name)}"))
            .join(": ", self.type_name_node(data.type_name))
            .join_opt(data.default, " default ", self.expr_node)
            .join_opt(data.id, " id ", self.expr_node)
            .join_opt_with_break(data.set_opcode, "set opcode ", self.expr_node)
            .join_opt_with_break(data.save_opcode, "save opcode ", self.expr_node)
        )

    def spec_port_instance_annotated_node(
        self, _in, a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecPortInstance]]
    ):
        def general(i: fpp_ast.GeneralPortInstance):
            kind = str(i.kind)

            def port(port_opt: Optional[AstNode[fpp_ast.QualIdent]]):
                if not port_opt:
                    return Lines(self.lines("serial"))
                else:
                    return self.qual_ident(port_opt.data)

            return (
                Lines(self.lines(f"{kind} port {self.ident(i.name)}:"))
                .join_opt(i.size, " ", self.bracket_expr_node)
                .join_no_indent(" ", port(i.port))
                .join_opt_with_break(i.priority, "priority ", self.expr_node)
                .join_opt_with_break(
                    i.queue_full, "", self.apply_to_data(self.queue_full)
                )
            )

        def special(i: fpp_ast.SpecialPortInstance):
            kind = str(i.kind)
            input_kind = f"{i.input_kind} " if i.input_kind else ""
            return (
                Lines(self.lines(f"{input_kind}{kind} port {self.ident(i.name)}"))
                .join_opt_with_break(i.priority, "priority ", self.expr_node)
                .join_opt_with_break(
                    i.queue_full, "", self.apply_to_data(self.queue_full)
                )
            )

        _, node, _ = a_node
        data = node.data
        if isinstance(data, fpp_ast.GeneralPortInstance):
            return general(data)
        elif isinstance(data, fpp_ast.SpecialPortInstance):
            return special(data)
        else:
            return Lines(self.lines(""))

    def spec_port_matching_annotated_node(
        self, _in, a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecPortMatching]]
    ):
        _, node, _ = a_node
        data = node.data
        port1 = data.port1.data
        port2 = data.port2.data
        return Lines(self.lines(f"match {port1} with {port2}"))

    def spec_record_annotated_node(
        self, _in, a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecRecord]]
    ):
        def record_type(type_name: AstNode[fpp_ast.TypeName], is_array: bool):
            tn = self.type_name_node(type_name)
            if is_array:
                return tn.add_suffix(" array")
            return tn

        _, node, _ = a_node
        data = node.data
        return (
            Lines(self.lines(f"product record {self.ident(data.name)}"))
            .join_no_indent(": ", record_type(data.record_type, data.is_array))
            .join_opt(data.id, " id ", self.expr_node)
        )

    def spec_state_entry_annotated_node(
        self, _in, a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecStateEntry]]
    ):
        _, node, _ = a_node
        data = node.data
        return Lines(self.lines("entry ")).join("", self.action_list(data.actions))

    def spec_state_exit_annotated_node(
        self, _in, a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecStateExit]]
    ):
        _, node, _ = a_node
        data = node.data
        return Lines(self.lines("exit ")).join("", self.action_list(data.actions))

    def spec_state_machine_instance_annotated_node(
        self, _in, a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecStateMachineInstance]]
    ):
        _, node, _ = a_node
        data = node.data
        return (
            Lines(self.lines(f"state machine instance {self.ident(data.name)}"))
            .join_no_indent(": ", self.qual_ident(data.state_machine.data))
            .join_opt_with_break(data.priority, "priority ", self.expr_node)
            .join_opt_with_break(data.queue_full, "", self.queue_full)
        )

    def spec_state_transition_annotated_node(
        self, _in, a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecStateTransition]]
    ):
        _, node, _ = a_node
        data = node.data
        return (
            Lines(self.lines(f"on {self.ident(data.signal.data)}"))
            .join_opt(data.guard, " if ", self.apply_to_data(self.ident_as_lines))
            .join(" ", self.transition_or_do(data.transition_or_do))
        )

    def spec_tlm_channel_annotated_node(
        self, _in, a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecTlmChannel]]
    ):
        _, node, _ = a_node
        data = node.data

        def update(u: fpp_ast.SpecTlmChannelUpdate) -> Lines:
            return Lines(self.lines(str(u)))

        def limit(l: fpp_ast.Limit) -> Lines:
            k, en = l
            return Lines(self.lines(str(k.data))).join(" ", self.expr_node(en))

        def opt_list(l: T) -> Optional[T]:
            if not l:
                return None
            else:
                return l

        def limit_seq(ls: List[fpp_ast.Limit]) -> Lines:
            limit_lines = []
            for l in ls:
                limit_lines += limit(l).lines
            return self.add_braces(Lines(limit_lines))

        return (
            Lines(self.lines(f"telemetry {self.ident(data.name)}"))
            .join_no_indent(": ", self.type_name_node(data.type_name))
            .join_opt(data.id, " id ", self.expr_node)
            .join_opt(data.update, " update ", update)
            .join_opt_with_break(
                data.format, "format ", self.apply_to_data(self.string)
            )
            .join_opt_with_break(opt_list(data.low), "low ", limit_seq)
            .join_opt_with_break(opt_list(data.high), "high ", limit_seq)
        )

    def spec_tlm_packet_annotated_node(
        self, _in: In, a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecTlmPacket]]
    ):
        _, node, _ = a_node
        data = node.data
        member_lines = []
        for m in data.members:
            member_lines += self.tlm_packet_member(m).lines
        return (
            Lines(self.lines(f"packet {self.ident(data.name)}"))
            .join_opt(data.id, " id ", self.expr_node)
            .join_no_indent(" group ", self.expr_node(data.group))
            .join_no_indent(" ", self.add_braces(Lines(member_lines)))
        )

    def spec_tlm_packet_set_annotated_node(
        self, _in: In, a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecTlmPacketSet]]
    ):
        _, node, _ = a_node
        data = node.data

        member_lines = Lines(
            [blank()]
            + self.blank_separated(self.tlm_packet_set_member, data.members).lines
            + [blank()]
        )
        member_block = self.add_braces(member_lines)

        omitted_lines = [
            line
            for o in data.omitted
            for line in self.apply_to_data(self.tlm_channel_id)(o).lines
        ]
        omitted_block = self.add_braces_if_non_empty(Lines(omitted_lines))

        header = Lines(self.lines(f"telemetry packets {self.ident(data.name)}"))

        return header.join_no_indent(" ", member_block).join_no_indent(
            " omit ", omitted_block
        )

    def spec_top_import_annotated_node(
        self, _in: In, a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecImport]]
    ) -> Out:
        _, node, _ = a_node
        data = node.data
        return self.qual_ident(data.sym.data).add_prefix("import ")

    def def_state_machine_annotated_node_external(self, _in, node):
        return super().def_state_machine_annotated_node_external(_in, node)

    def def_state_machine_annotated_node_internal(self, _in, node, members):
        return super().def_state_machine_annotated_node_internal(_in, node, members)

    def type_name_bool_node(self, _in, node):
        return Lines(self.lines("bool"))

    def type_name_float_node(self, _in, node, tn):
        return Lines(self.lines(str(tn.name)))

    def type_name_int_node(self, _in, node, tn):
        return Lines(self.lines(str(tn.name)))

    def type_name_qual_ident_node(self, _in, node, tn):
        return self.qual_ident(tn.name.data)

    def type_name_string_node(self, _in, node, tn):
        return Lines(self.lines("string")).join_opt(tn.size, " size ", self.expr_node)

    def expr_node(self, expr: AstNode[fpp_ast.Expr]) -> Out:
        return self.match_expr_node(None, expr)

    def type_name_node(self, node: AstNode[fpp_ast.TypeName]) -> Lines:
        return self.match_type_name_node(None, node)

    def tu_member(self, tum: fpp_ast.TUMember) -> Out:
        return self.module_member(tum)

    def default(self, _in: In):
        raise InternalError("FppWriter: Visitor not implemented")

    def flatten(self, list_of_lists: List[List]) -> List:
        result = []
        for item in list_of_lists:
            if isinstance(item, list):
                result.extend(self.flatten(item))
            else:
                result.append(item)
        return result

    def prefix_with_dictionary(self, s: str, is_dictionary_def) -> str:
        if is_dictionary_def:
            return f"dictionary {s}"
        else:
            return s
