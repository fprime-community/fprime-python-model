import sys
from typing import List, Tuple, TypeVar, Callable, TypeAlias
# typing.override was added in Python 3.12. On older versions we fall back to a
# no-op decorator so the codebase stays compatible with Python 3.10+.
if sys.version_info >= (3, 12):
    from typing import override
else:
    def override(func):  # type: ignore[no-redef]
        return func
from fprime_python_model.fpp_ast import fpp_ast
from fprime_python_model.fpp_ast.fpp_ast_node import AstNode
from fprime_python_model.utils.fpp_ast_visitor import AstVisitor, In
from fprime_python_model.utils.line_utils import LineUtils, Line, join_lists, IndentMode
from fprime_python_model.utils.error import InternalError

T = TypeVar("T")

Out: TypeAlias = List[Line]


class AstWriter(AstVisitor, LineUtils):

    def ident(self, s: str) -> Out:
        return self.lines(f"ident {s}")

    def write_trans_unit(self, tu: fpp_ast.TransUnit) -> Out:
        return self.trans_unit(None, tu)

    @override
    def def_alias_type_annotated_node(
        self,
        in_: In,
        a_node: fpp_ast.Annotated[AstNode[fpp_ast.DefAliasType]],
    ) -> Out:
        _, node, _ = a_node
        data = node.data
        return self.prefix_with_dictionary(
            "def alias type", data.is_dictionary_def
        ) + list(
            map(
                self.indent_in,
                self.ident(data.name) + self.type_name_node(data.type_name),
            )
        )

    @override
    def def_abs_type_annotated_node(
        self,
        in_: In,
        a_node: fpp_ast.Annotated[AstNode[fpp_ast.DefAbsType]],
    ) -> Out:
        _, node, _ = a_node
        return self.lines("def abs type") + list(
            map(self.indent_in, self.ident(node.data.name))
        )

    @override
    def def_action_annotated_node(
        self,
        in_: In,
        a_node: fpp_ast.Annotated[AstNode[fpp_ast.DefAction]],
    ) -> Out:
        _, node, _ = a_node
        data = node.data
        parts = self.ident(data.name) + self.lines_opt(
            self.type_name_node, data.type_name
        )
        return self.lines("def action") + list(map(self.indent_in, parts))

    @override
    def def_array_annotated_node(
        self, _in: In, a_node: fpp_ast.Annotated[AstNode[fpp_ast.DefArray]]
    ):
        _, node, _ = a_node
        data = node.data
        result = self.prefix_with_dictionary("def array", data.is_dictionary_def)
        concat_list = (
            self.ident(data.name)
            + self.add_prefix("size", self.expr_node)(data.size)
            + self.type_name_node(data.elt_type)
            + self.lines_opt(self.add_prefix("default", self.expr_node), data.default)
            + self.lines_opt(
                self.add_prefix("format", self.apply_to_data(self.string)), data.format
            )
        )
        return result + list(map(self.indent_in, concat_list))

    @override
    def def_choice_annotated_node(
        self, _in: In, a_node: fpp_ast.Annotated[AstNode[fpp_ast.DefChoice]]
    ):
        _, node, _ = a_node
        data = node.data
        result = self.lines("def choice")
        concat_list = (
            self.ident(data.name)
            + self.add_prefix("guard", self.apply_to_data(self.ident))(data.guard)
            + self.transition_expr(data.if_transition.data)
            + self.transition_expr(data.else_transition.data)
        )
        return result + list(map(self.indent_in, concat_list))

    @override
    def def_component_annotated_node(
        self, _in: In, a_node: fpp_ast.Annotated[AstNode[fpp_ast.DefComponent]]
    ):
        _, node, _ = a_node
        data = node.data
        kind = str(data.kind)
        result = self.lines("def component")
        component_member_lines = [self.component_member(m) for m in data.members]
        concat_list = (
            self.lines(f"kind {kind}")
            + self.ident(data.name)
            + self.flatten(component_member_lines)
        )
        return result + list(map(self.indent_in, concat_list))

    @override
    def def_interface_annotated_node(
        self, _in: In, a_node: fpp_ast.Annotated[AstNode[fpp_ast.DefInterface]]
    ):
        _, node, _ = a_node
        data = node.data
        result = self.lines("def interface")
        interface_member_lines = [self.interface_member(m) for m in data.members]
        concat_list = self.ident(data.name) + self.flatten(interface_member_lines)
        return result + list(map(self.indent_in, concat_list))

    @override
    def def_component_instance_annotated_node(
        self, _in: In, a_node: fpp_ast.Annotated[AstNode[fpp_ast.DefComponentInstance]]
    ):
        _, node, _ = a_node
        data = node.data
        result = self.lines("def component instance")
        init_spec_lines = [
            self.annotate_node(self.spec_init)(spec) for spec in data.init_specs
        ]
        concat_list = (
            self.ident(data.name)
            + self.add_prefix("component", self.qual_ident)(data.component.data)
            + self.add_prefix("base id", self.expr_node)(data.base_id)
            + self.lines_opt(
                self.add_prefix("type", self.apply_to_data(self.string)), data.impl_type
            )
            + self.lines_opt(self.apply_to_data(self.file_string), data.file)
            + self.lines_opt(
                self.add_prefix("queue size", self.expr_node), data.queue_size
            )
            + self.lines_opt(
                self.add_prefix("stack size", self.expr_node), data.stack_size
            )
            + self.lines_opt(self.add_prefix("priority", self.expr_node), data.priority)
            + self.lines_opt(self.add_prefix("cpu", self.expr_node), data.cpu)
            + self.flatten(init_spec_lines)
        )
        return result + list(map(self.indent_in, concat_list))

    @override
    def def_constant_annotated_node(
        self, _in: In, a_node: fpp_ast.Annotated[AstNode[fpp_ast.DefConstant]]
    ):
        _, node, _ = a_node
        data = node.data
        result = self.prefix_with_dictionary("def constant", data.is_dictionary_def)
        concat_list = self.ident(data.name) + self.expr_node(data.value)
        return result + list(map(self.indent_in, concat_list))

    @override
    def def_enum_annotated_node(
        self, _in: In, a_node: fpp_ast.Annotated[AstNode[fpp_ast.DefEnum]]
    ):
        _, node, _ = a_node
        data = node.data
        result = self.prefix_with_dictionary("def enum", data.is_dictionary_def)
        enum_constant_lines = [
            self.annotate_node(self.def_enum_constant)(c) for c in data.constants
        ]
        concat_list = (
            self.ident(data.name)
            + self.lines_opt(self.type_name_node, data.type_name)
            + self.flatten(enum_constant_lines)
            + self.lines_opt(self.add_prefix("default", self.expr_node), data.default)
        )
        return result + list(map(self.indent_in, concat_list))

    @override
    def def_guard_annotated_node(
        self, _in: In, a_node: fpp_ast.Annotated[AstNode[fpp_ast.DefGuard]]
    ):
        _, node, _ = a_node
        data = node.data
        result = self.lines("def guard")
        concat_list = self.ident(data.name) + self.lines_opt(
            self.type_name_node, data.type_name
        )
        return result + [self.indent_in(line) for line in concat_list]

    @override
    def def_module_annotated_node(
        self, _in: In, a_node: fpp_ast.Annotated[AstNode[fpp_ast.DefModule]]
    ):
        _, node, _ = a_node
        data = node.data
        result = self.lines("def module")
        module_member_lines = self.flatten(
            [self.module_member(m) for m in data.members]
        )
        concat_list = self.ident(data.name) + module_member_lines
        return result + list(map(self.indent_in, concat_list))

    @override
    def def_port_annotated_node(
        self, _in: In, a_node: fpp_ast.Annotated[AstNode[fpp_ast.DefPort]]
    ):
        _, node, _ = a_node
        data = node.data
        result = self.lines("def port")
        concat_list = (
            self.ident(data.name)
            + self.formal_param_list(data.params)
            + self.lines_opt(
                self.add_prefix("return", self.type_name_node), data.return_type
            )
        )
        return result + [self.indent_in(line) for line in concat_list]

    @override
    def def_signal_annotated_node(
        self, _in: In, a_node: fpp_ast.Annotated[AstNode[fpp_ast.DefSignal]]
    ):
        _, node, _ = a_node
        data = node.data
        result = self.lines("def signal")
        concat_list = self.ident(data.name) + self.lines_opt(
            self.type_name_node, data.type_name
        )
        return result + [self.indent_in(line) for line in concat_list]

    @override
    def def_state_annotated_node(
        self, _in: In, a_node: fpp_ast.Annotated[AstNode[fpp_ast.DefState]]
    ):
        _, node, _ = a_node
        data = node.data
        result = self.lines("def state")
        concat_list = self.ident(data.name) + self.flatten(
            [self.state_member(m) for m in data.members]
        )
        return result + [self.indent_in(line) for line in concat_list]

    @override
    def def_state_machine_annotated_node(
        self, _in: In, a_node: fpp_ast.Annotated[AstNode[fpp_ast.DefStateMachine]]
    ):
        _, node, _ = a_node
        data = node.data
        result = self.lines("def state machine")
        members = data.members if data.members is not None else []
        state_machine_member_lines = self.flatten(
            [self.state_machine_member(m) for m in members]
        )
        concat_list = self.ident(data.name) + state_machine_member_lines
        return result + [self.indent_in(line) for line in concat_list]

    @override
    def def_struct_annotated_node(
        self, _in: In, a_node: fpp_ast.Annotated[AstNode[fpp_ast.DefStruct]]
    ):
        _, node, _ = a_node
        data = node.data
        result = self.prefix_with_dictionary("def struct", data.is_dictionary_def)
        struct_type_member_lines = [
            self.annotate_node(self.struct_type_member)(m) for m in data.members
        ]
        concat_list = (
            self.ident(data.name)
            + self.flatten(struct_type_member_lines)
            + self.lines_opt(self.expr_node, data.default)
        )
        return result + [self.indent_in(line) for line in concat_list]

    @override
    def def_system_annotated_node(
        self, _in: In, a_node: fpp_ast.Annotated[AstNode[fpp_ast.DefSystem]]
    ):
        _, node, _ = a_node
        data = node.data
        return self.lines("def system") + [
            self.indent_in(line)
            for line in self.ident(data.name) + self.qual_ident(data.topology.data)
        ]

    @override
    def def_topology_annotated_node(
        self, _in: In, a_node: fpp_ast.Annotated[AstNode[fpp_ast.DefTopology]]
    ):
        _, node, _ = a_node
        data = node.data
        result = self.lines("def topology")
        topology_member_lines = [self.topology_member(m) for m in data.members]
        concat_list = list(
            map(
                self.indent_in,
                self.ident(data.name) + self.flatten(topology_member_lines),
            )
        )
        return result + concat_list

    @override
    def default(self, _in: In):
        raise InternalError("AstWriter: Visitor not implemented")

    @override
    def expr_array_node(
        self, _in: In, node: AstNode[fpp_ast.Expr], e: fpp_ast.ExprArray
    ):
        result = self.lines("expr array")
        concat_list = self.flatten([self.expr_node(el) for el in e.elts])
        return result + [self.indent_in(line) for line in concat_list]

    @override
    def expr_array_subscript_node(
        self, _in: In, node: AstNode[fpp_ast.Expr], e: fpp_ast.ExprArraySubscript
    ):
        result = self.lines("expr array subscript")
        return result + [
            self.indent_in(line) for line in self.expr_node(e.e1) + self.expr_node(e.e2)
        ]

    @override
    def expr_binop_node(
        self, _in: In, node: AstNode[fpp_ast.Expr], e: fpp_ast.ExprBinop
    ):
        result = self.lines("expr binop")
        concat_list = self.expr_node(e.e1) + self.binop(e.op) + self.expr_node(e.e2)
        return result + [self.indent_in(line) for line in concat_list]

    @override
    def expr_dot_node(self, _in: In, node: AstNode[fpp_ast.Expr], e: fpp_ast.ExprDot):
        result = self.lines("expr dot")
        concat_list = self.expr_node(e.e) + self.ident(e.id.data)
        return result + [self.indent_in(line) for line in concat_list]

    @override
    def expr_ident_node(
        self, _in: In, node: AstNode[fpp_ast.Expr], e: fpp_ast.ExprIdent
    ):
        return self.ident(e.value)

    @override
    def expr_literal_bool_node(
        self, _in: In, node: AstNode[fpp_ast.Expr], e: fpp_ast.ExprLiteralBool
    ):
        return self.lines(f"literal bool {e.value}")

    @override
    def expr_literal_float_node(
        self, _in: In, node: AstNode[fpp_ast.Expr], e: fpp_ast.ExprLiteralFloat
    ):
        return self.lines(f"literal float {e.value}")

    @override
    def expr_literal_int_node(
        self, _in: In, node: AstNode[fpp_ast.Expr], e: fpp_ast.ExprLiteralInt
    ):
        return self.lines(f"literal int {e.value}")

    @override
    def expr_literal_string_node(
        self, _in: In, node: AstNode[fpp_ast.Expr], e: fpp_ast.ExprLiteralString
    ):
        return self.add_prefix("literal string", self.string)(e.value)

    @override
    def expr_paren_node(
        self, _in: In, node: AstNode[fpp_ast.Expr], e: fpp_ast.ExprParen
    ):
        result = self.lines("expr paren")
        concat_list = self.expr_node(e.e)
        return result + [self.indent_in(line) for line in concat_list]

    @override
    def expr_size_of_node(
        self, _in: In, node: AstNode[fpp_ast.Expr], e: fpp_ast.ExprSizeOf
    ):
        return self.lines("expr sizeof") + self.type_name_node(e.type_name)

    @override
    def expr_struct_node(
        self, _in: In, node: AstNode[fpp_ast.Expr], e: fpp_ast.ExprStruct
    ):
        result = self.lines("expr struct")
        struct_member_lines = self.flatten(
            [self.apply_to_data(self.struct_member)(m) for m in e.members]
        )
        return result + [self.indent_in(line) for line in struct_member_lines]

    @override
    def expr_unop_node(self, _in: In, node: AstNode[fpp_ast.Expr], e: fpp_ast.ExprUnop):
        result = self.lines("expr unop")
        concat_list = self.unop(e.op) + self.expr_node(e.e)
        return result + [self.indent_in(line) for line in concat_list]

    @override
    def spec_command_annotated_node(
        self, _in: In, a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecCommand]]
    ):
        _, node, _ = a_node
        data = node.data
        result = self.lines("spec command")
        concat_list = (
            self.lines(f"kind {str(data.kind)}")
            + self.add_prefix("name", self.ident)(data.name)
            + self.formal_param_list(data.params)
            + self.lines_opt(self.add_prefix("opcode", self.expr_node), data.opcode)
            + self.lines_opt(self.add_prefix("priority", self.expr_node), data.priority)
            + self.lines_opt(self.apply_to_data(self.queue_full), data.queue_full)
        )
        return result + [self.indent_in(line) for line in concat_list]

    @override
    def spec_instance_annotated_node(
        self, _in: In, a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecInstance]]
    ):
        _, node, _ = a_node
        data = node.data
        return join_lists(
            IndentMode.INDENT,
            self.lines("instance"),
            "",
            self.qual_ident(data.instance.data),
        )

    @override
    def spec_connection_graph_annotated_node(
        self, _in: In, a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecConnectionGraph]]
    ):
        def direct(g: fpp_ast.Direct):
            def connection(c: fpp_ast.Connection):
                prefix = "unmatched connection" if c.is_unmatched else "connection"
                lines_list = self.lines(prefix) + list(
                    map(
                        self.indent_in,
                        (
                            self.add_prefix("from port", self.port_instance_identifier)(
                                c.from_port.data
                            )
                            + self.lines_opt(
                                self.add_prefix("index", self.expr_node), c.from_index
                            )
                            + self.add_prefix("to port", self.port_instance_identifier)(
                                c.to_port.data
                            )
                            + self.lines_opt(
                                self.add_prefix("index", self.expr_node), c.to_index
                            )
                        ),
                    )
                )

                return lines_list

            result = self.lines("spec connection graph direct")
            connection_lines = [connection(c) for c in g.connections]
            concat_list = self.flatten(
                self.ident(g.name) + [s for s in connection_lines]
            )
            return result + list(map(self.indent_in, concat_list))

        def pattern(g: fpp_ast.Pattern):
            def target(qid: AstNode[fpp_ast.QualIdent]):
                return self.add_prefix("target", self.qual_ident)(qid.data)

            result = self.lines("spec connection graph pattern")
            target_lines = [target(t) for t in g.targets]
            concat_list = (
                self.lines("kind " + str(g.kind))
                + self.add_prefix("source", self.qual_ident)(g.source.data)
                + self.flatten(target_lines)
            )

            return result + list(map(self.indent_in, self.flatten(concat_list)))

        _, node, _ = a_node
        data = node.data
        if isinstance(data, fpp_ast.Direct):
            return direct(data)
        elif isinstance(data, fpp_ast.Pattern):
            return pattern(data)
        else:
            raise ValueError("Unknown SpecConnectionGraph subtype")

    @override
    def spec_container_annotated_node(
        self, _in: In, a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecContainer]]
    ):
        _, node, _ = a_node
        data = node.data
        result = self.lines("spec container")
        concat_list = (
            self.ident(data.name)
            + self.lines_opt(self.add_prefix("id", self.expr_node), data.id)
            + self.lines_opt(
                self.add_prefix("default priority", self.expr_node),
                data.default_priority,
            )
        )
        return result + [self.indent_in(line) for line in concat_list]

    @override
    def spec_event_annotated_node(
        self, _in: In, a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecEvent]]
    ):
        _, node, _ = a_node
        data = node.data

        def throttle_clause(throttle: AstNode[fpp_ast.EventThrottle]) -> Out:
            return self.add_prefix("throttle", self.expr_node)(
                throttle.data.count
            ) + self.lines_opt(
                self.add_prefix("every", self.expr_node), throttle.data.every
            )

        result = self.lines("spec event")
        concat_list = (
            self.ident(data.name)
            + self.formal_param_list(data.params)
            + self.lines(f"severity {str(data.severity)}")
            + self.lines_opt(self.add_prefix("id", self.expr_node), data.id)
            + self.add_prefix("format", self.string)(data.format.data)
            + self.lines_opt(throttle_clause, data.throttle)
        )
        return result + [self.indent_in(line) for line in concat_list]

    @override
    def spec_include_annotated_node(
        self, _in: In, a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecInclude]]
    ):
        _, node, _ = a_node
        data = node.data
        return self.lines("spec include") + [
            self.indent_in(line) for line in self.file_string(data.file.data)
        ]

    @override
    def spec_initial_transition_annotated_node(
        self, _in: In, a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecInitialTransition]]
    ):
        _, node, _ = a_node
        data = node.data
        return self.lines("spec initial") + [
            self.indent_in(line) for line in self.transition_expr(data.transition.data)
        ]

    @override
    def spec_internal_port_annotated_node(
        self, _in: In, a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecInternalPort]]
    ):
        _, node, _ = a_node
        data = node.data
        result = self.lines("spec internal port")
        concat_list = (
            self.ident(data.name)
            + self.formal_param_list(data.params)
            + self.lines_opt(self.add_prefix("priority", self.expr_node), data.priority)
            + self.lines_opt(self.queue_full, data.queue_full)
        )
        return result + [self.indent_in(line) for line in concat_list]

    @override
    def spec_loc_annotated_node(
        self, _in: In, a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecLoc]]
    ):
        _, node, _ = a_node
        data = node.data
        kind = str(data.kind)
        result = self.lines("spec loc")
        concat_list = (
            self.lines("kind " + kind)
            + self.add_prefix("symbol", self.qual_ident)(data.symbol.data)
            + self.file_string(data.file.data)
        )
        return result + [self.indent_in(line) for line in concat_list]

    @override
    def spec_param_annotated_node(
        self, _in: In, a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecParam]]
    ):
        _, node, _ = a_node
        data = node.data
        header = "external spec param" if data.is_external else "spec param"
        result = self.lines(header)
        concat_list = (
            self.ident(data.name)
            + self.type_name_node(data.type_name)
            + self.lines_opt(self.add_prefix("default", self.expr_node), data.default)
            + self.lines_opt(self.add_prefix("id", self.expr_node), data.id)
            + self.lines_opt(
                self.add_prefix("set opcode", self.expr_node), data.set_opcode
            )
            + self.lines_opt(
                self.add_prefix("save opcode", self.expr_node), data.save_opcode
            )
        )
        return result + [self.indent_in(line) for line in concat_list]

    @override
    def spec_port_instance_annotated_node(
        self, _in: In, a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecPortInstance]]
    ):
        _, node, _ = a_node

        def general(i: fpp_ast.GeneralPortInstance):
            kind = self.lines(f"kind {str(i.kind)}")
            concat_list = (
                kind
                + self.ident(i.name)
                + self.lines_opt(self.add_prefix("array size", self.expr_node), i.size)
                + self.lines_opt(
                    self.add_prefix("port type", self.apply_to_data(self.qual_ident)),
                    i.port,
                )
                + self.lines_opt(
                    self.add_prefix("priority", self.expr_node), i.priority
                )
                + self.lines_opt(self.apply_to_data(self.queue_full), i.queue_full)
            )
            return self.lines("spec port instance general") + [
                self.indent_in(line) for line in concat_list
            ]

        def special(i: fpp_ast.SpecialPortInstance):
            kind = self.lines(f"kind {str(i.kind)}")
            concat_list = (
                self.lines_opt(
                    self.add_prefix("input kind", self.string),
                    str(i.input_kind) if i.input_kind is not None else None,
                )
                + kind
                + self.ident(i.name)
                + self.lines_opt(
                    self.add_prefix("priority", self.expr_node), i.priority
                )
                + self.lines_opt(self.apply_to_data(self.queue_full), i.queue_full)
            )
            return self.lines("spec port instance special") + [
                self.indent_in(line) for line in concat_list
            ]

        data = node.data
        if isinstance(data, fpp_ast.GeneralPortInstance):
            return general(data)
        elif isinstance(data, fpp_ast.SpecialPortInstance):
            return special(data)
        else:
            raise ValueError("Unknown SpecPortInstance subtype")

    @override
    def spec_port_matching_annotated_node(
        self, _in: In, a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecPortMatching]]
    ):
        _, node, _ = a_node
        data = node.data
        result = self.lines("spec port matching")
        concat_list = self.ident(data.port1.data) + self.ident(data.port2.data)
        return result + [self.indent_in(line) for line in concat_list]

    @override
    def spec_record_annotated_node(
        self, in_, a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecRecord]]
    ):
        _, node, _ = a_node
        data = node.data
        if data.is_array:
            write_record_type = self.add_suffix(self.type_name_node, "array")
        else:
            write_record_type = self.type_name_node

        lines_out = self.lines("spec record") + list(
            map(
                self.indent_in,
                self.ident(data.name)
                + write_record_type(data.record_type)
                + self.lines_opt(self.add_prefix("id", self.expr_node), data.id),
            )
        )

        return lines_out

    @override
    def spec_state_entry_annotated_node(
        self, in_, a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecStateEntry]]
    ):
        _, node, _ = a_node
        data = node.data
        return self.lines("spec state entry") + [
            self.indent_in(line) for line in self.action_list(data.actions)
        ]

    @override
    def spec_state_exit_annotated_node(
        self, in_, a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecStateExit]]
    ):
        _, node, _ = a_node
        data = node.data
        return self.lines("spec state exit") + [
            self.indent_in(line) for line in self.action_list(data.actions)
        ]

    @override
    def spec_state_machine_instance_annotated_node(
        self, in_, a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecStateMachineInstance]]
    ):
        _, node, _ = a_node
        data = node.data
        result = self.lines("spec state machine instance")
        lines_out = (
            self.ident(node.data.name)
            + self.add_prefix("state machine", self.qual_ident)(data.state_machine.data)
            + self.lines_opt(self.add_prefix("priority", self.expr_node), data.priority)
            + self.lines_opt(self.queue_full, data.queue_full)
        )

        return result + list(map(self.indent_in, lines_out))

    @override
    def spec_state_transition_annotated_node(
        self, in_, a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecStateTransition]]
    ):
        _, node, _ = a_node
        data = node.data
        lines_out = (
            self.lines("spec state transition")
            + self.add_prefix("signal", self.apply_to_data(self.ident))(data.signal)
            + self.lines_opt(
                self.add_prefix("guard", self.apply_to_data(self.ident)), data.guard
            )
            + self.transition_or_do(data.transition_or_do)
        )
        return [self.indent_in(line) for line in lines_out]

    @override
    def spec_tlm_channel_annotated_node(
        self, in_, a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecTlmChannel]]
    ):
        _, node, _ = a_node
        tc = node.data

        def update(u: fpp_ast.SpecTlmChannelUpdate) -> Out:
            return self.lines(f"update {u}")

        def kind(k: fpp_ast.LimitKind) -> Out:
            return self.lines(str(k))

        def limit(l: fpp_ast.Limit) -> Out:
            k, en = l
            return self.lines("limit") + list(
                map(self.indent_in, kind(k.data) + self.expr_node(en))
            )

        def limits(name: str, ls: List[fpp_ast.Limit]) -> Out:
            return self.flatten(list(map(self.add_prefix_no_indent(name, limit), ls)))

        lines_out = self.lines("spec tlm channel") + list(
            map(
                self.indent_in,
                self.ident(tc.name)
                + self.type_name_node(tc.type_name)
                + self.lines_opt(self.add_prefix("id", self.expr_node), tc.id)
                + self.lines_opt(update, tc.update)
                + self.lines_opt(
                    self.add_prefix("format", self.apply_to_data(self.string)),
                    tc.format,
                )
                + limits("low", tc.low)
                + limits("high", tc.high),
            )
        )

        return lines_out

    @override
    def spec_tlm_packet_annotated_node(
        self, in_, a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecTlmPacket]]
    ):
        _, node, _ = a_node
        data = node.data
        lines_out = self.lines("spec tlm packet") + list(
            map(
                self.indent_in,
                self.ident(data.name)
                + self.lines_opt(self.add_prefix("id", self.expr_node), data.id)
                + self.add_prefix("group", self.expr_node)(data.group)
                + self.flatten([self.tlm_packet_member(m) for m in data.members]),
            )
        )

        return lines_out

    @override
    def spec_tlm_packet_set_annotated_node(
        self, in_, a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecTlmPacketSet]]
    ):
        _, node, _ = a_node
        data = node.data
        packet_set_member_lines = [
            self.indent_in(line)
            for m in data.members
            for line in self.tlm_packet_set_member(m)
        ]
        omitted_channel_lines = [
            self.indent_in(line)
            for o in data.omitted
            for line in self.apply_to_data(self.tlm_channel_identifier)(o)
        ]

        lines_out = self.lines("spec tlm packet set") + list(
            map(
                self.indent_in,
                self.ident(data.name)
                + self.lines("members")
                + packet_set_member_lines
                + self.lines("omitted")
                + omitted_channel_lines,
            )
        )

        return lines_out

    @override
    def spec_top_port_annotated_node(
        self, in_, a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecTopPort]]
    ):
        _, node, _ = a_node
        data = node.data

        lines_to_ident = self.ident(data.name) + self.port_instance_identifier(
            data.underlying_port.data
        )
        return self.lines("spec top port") + [
            self.indent_in(line) for line in lines_to_ident
        ]

    @override
    def spec_interface_import_annotated_node(
        self, in_, a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecImport]]
    ):
        _, node, _ = a_node
        data = node.data
        return self.lines("spec interface import") + [
            self.indent_in(line) for line in self.qual_ident(data.sym.data)
        ]

    @override
    def trans_unit(self, in_, tu: fpp_ast.TransUnit):
        result = []
        for member in tu.members:
            result.append(self.tu_member(member))
        return result

    @override
    def type_name_bool_node(self, in_, node: AstNode[fpp_ast.TypeName]):
        return self.lines("bool")

    @override
    def type_name_float_node(
        self, in_, node: AstNode[fpp_ast.TypeName], tn: fpp_ast.TypeNameFloat
    ):
        return self.lines(str(tn.name))

    @override
    def type_name_int_node(
        self, in_, node: AstNode[fpp_ast.TypeName], tn: fpp_ast.TypeNameInt
    ):
        return self.lines(str(tn.name))

    @override
    def type_name_qual_ident_node(
        self, in_, node: AstNode[fpp_ast.TypeName], tn: fpp_ast.TypeNameQualIdent
    ):
        return self.qual_ident(tn.name.data)

    @override
    def type_name_string_node(
        self, in_, node: AstNode[fpp_ast.TypeName], tn: fpp_ast.TypeNameString
    ):
        return self.lines("string") + [
            self.indent_in(line)
            for line in self.lines_opt(self.add_prefix("size", self.expr_node), tn.size)
        ]

    def expr_node(self, node) -> Out:
        return self.match_expr_node(None, node)

    def annotate(self, pre: List[str], lines: Out, post: List[str]) -> Out:
        def pre_line(s: str) -> Line:
            return self.line(f"@ {s}")

        def post_line(s: str) -> Line:
            return self.line(f"@< {s}")

        pre_lines = [pre_line(s) for s in pre]
        post_lines = [post_line(s) for s in post]
        return pre_lines + lines + post_lines

    def annotate_node(
        self, f: Callable[[T], Out]
    ) -> Callable[[Tuple[List[str], AstNode[T], List[str]]], Out]:
        def wrapped(annotated: Tuple[List[str], AstNode[T], List[str]]) -> Out:
            pre, node, post = annotated
            return self.annotate(pre, f(node.data), post)

        return wrapped

    def queue_full(self, qf: fpp_ast.QueueFull) -> Out:
        return self.lines(f"queue full {qf}")

    def spec_init(self, si: fpp_ast.SpecInit) -> Out:
        return self.lines("spec init") + list(
            map(
                self.indent_in,
                (
                    self.add_prefix("phase", self.expr_node)(si.phase)
                    + self.add_prefix("code", self.string)(si.code)
                ),
            )
        )

    def formal_param(self, fp: fpp_ast.FormalParam) -> Out:
        def kind(k: fpp_ast.FormalParamKind) -> str:
            match k:
                case fpp_ast.FormalParamKind.REF:
                    return "kind ref"
                case fpp_ast.FormalParamKind.VALUE:
                    return "kind value"

        result = self.lines("formal param") + list(
            map(
                self.indent_in,
                self.lines(kind(fp.kind))
                + self.ident(fp.name)
                + self.type_name_node(fp.type_name),
            )
        )
        return result

    def formal_param_list(self, params: fpp_ast.FormalParamList) -> Out:
        return [
            line
            for param in params
            for line in self.annotate_node(self.formal_param)(param)
        ]

    def binop(self, op: fpp_ast.Binop) -> Out:
        return self.lines(f"binop {op}")

    def unop(self, op: fpp_ast.Unop) -> Out:
        return self.lines(f"unop {op}")

    def module_member(self, member: fpp_ast.ModuleMember) -> Out:
        a1, _, a2 = member.node
        l = self.match_module_member(None, member)
        return self.annotate(a1, l, a2)

    def topology_member(self, member: fpp_ast.TopologyMember) -> Out:
        a1, _, a2 = member.node
        l = self.match_topology_member(None, member)
        return self.annotate(a1, l, a2)

    def component_member(self, member: fpp_ast.ComponentMember) -> Out:
        a1, _, a2 = member.node
        l = self.match_component_member(None, member)
        return self.annotate(a1, l, a2)

    def state_member(self, member: fpp_ast.StateMember) -> Out:
        a1, _, a2 = member.node
        l = self.match_state_member(None, member)
        return self.annotate(a1, l, a2)

    def state_machine_member(self, member: fpp_ast.StateMachineMember) -> Out:
        a1, _, a2 = member.node
        l = self.match_state_machine_member(None, member)
        return self.annotate(a1, l, a2)

    def tu_member(self, tum: fpp_ast.TUMember) -> Out:
        return self.module_member(tum)

    def interface_member(self, member: fpp_ast.InterfaceMember) -> Out:
        a1, _, a2 = member.node
        l = self.match_interface_member(None, member)
        return self.annotate(a1, l, a2)

    def struct_member(self, member: fpp_ast.StructMember) -> Out:
        return self.lines("struct member") + list(
            map(
                self.indent_in, (self.ident(member.name) + self.expr_node(member.value))
            )
        )

    def struct_type_member(self, member: fpp_ast.StructTypeMember) -> Out:
        return self.lines("struct type member") + list(
            map(
                self.indent_in,
                self.ident(member.name)
                + self.lines_opt(
                    self.add_prefix("array size", self.expr_node), member.size
                )
                + self.type_name_node(member.type_name)
                + self.lines_opt(
                    self.add_prefix("format", self.apply_to_data(self.string)),
                    member.format,
                ),
            )
        )

    def tlm_packet_member(self, member: fpp_ast.TlmPacketMember) -> Out:
        match member:
            case fpp_ast.TlmPacketMemberSpecInclude():
                return self.spec_include_annotated_node(None, ([], member.node, []))
            case fpp_ast.TlmPacketMemberTlmChannelIdentifier():
                return self.lines("tlm channel identifier") + list(
                    map(self.indent_in, self.tlm_channel_identifier(member.node.data))
                )
            case _:
                raise Exception("TlmPacketMember writer not implemented")

    def tlm_packet_set_member(self, member: fpp_ast.TlmPacketSetMember) -> Out:
        a1, _, a2 = member.node
        l = self.match_tlm_packet_set_member(None, member)
        return self.annotate(a1, l, a2)

    def action_list(self, actions: List[AstNode[fpp_ast.Ident]]) -> Out:
        return [self.line(f"action ident {node.data}") for node in actions]

    def transition_expr(self, transition: fpp_ast.TransitionExpr) -> Out:
        return self.action_list(transition.actions) + self.add_prefix(
            "target", self.apply_to_data(self.qual_ident)
        )(transition.target)

    def string(self, s: str) -> Out:
        return [self.line(split_s) for split_s in s.split("\n")]

    def apply_to_data(self, f):
        def inner(a: fpp_ast.AstNode[T]):
            return f(a.data)

        return inner

    def port_instance_identifier(self, pii: fpp_ast.PortInstanceIdentifier) -> Out:
        qid = fpp_ast.Qualified(pii.interface_instance, pii.port_name)
        return self.qual_ident(qid)

    def tlm_channel_identifier(self, tci: fpp_ast.TlmChannelIdentifier) -> Out:
        qid = fpp_ast.Qualified(tci.component_instance, tci.channel_name)
        return self.qual_ident(qid)

    def qual_ident_string(self, qid: fpp_ast.QualIdent) -> str:
        if isinstance(qid, fpp_ast.Unqualified):
            return qid.name
        elif isinstance(qid, fpp_ast.Qualified):
            return f"{self.qual_ident_string(qid.qualifier.data)}.{qid.name.data}"
        else:
            raise InternalError("Could not write AST for qualified identifier")

    def qual_ident(self, qid: fpp_ast.QualIdent) -> Out:
        return self.lines(f"qual ident {self.qual_ident_string(qid)}")

    def def_enum_constant(self, dec: fpp_ast.DefEnumConstant) -> Out:
        constants = self.ident(dec.name) + self.lines_opt(self.expr_node, dec.value)
        return self.lines("def enum constant") + list(map(self.indent_in, constants))

    def file_string(self, s: str) -> Out:
        return self.lines(f"file {s}")

    def transition_or_do(self, tod):
        if isinstance(tod, fpp_ast.Transition):
            return self.transition_expr(tod.transition.data)
        elif isinstance(tod, fpp_ast.Do):
            return self.action_list(tod.actions)
        else:
            return []

    def add_prefix(self, s: str, f: Callable[[T], Out]) -> Callable[[T], Out]:
        def wrapped(t: T) -> Out:
            return join_lists(IndentMode.INDENT, self.lines(s), " ", f(t))

        return wrapped

    def add_prefix_no_indent(self, s: str, f: Callable[[T], Out]) -> Callable[[T], Out]:
        def wrapped(t: T) -> Out:
            return join_lists(IndentMode.NO_INDENT, self.lines(s), " ", f(t))

        return wrapped

    def add_suffix(self, f: Callable[[T], Out], s: str) -> Callable[[T], Out]:
        def wrapped(t: T) -> Out:
            return join_lists(IndentMode.INDENT, f(t), " ", self.lines(s))

        return wrapped

    def type_name_node(self, node: AstNode[fpp_ast.TypeName]) -> Out:
        func: Callable[[AstNode[fpp_ast.TypeName]], List[Line]] = (
            lambda n: self.match_type_name_node((), n)
        )
        return self.add_prefix("type name", func)(node)

    def flatten(self, list_of_lists: List[List]) -> List:
        result = []
        for item in list_of_lists:
            if isinstance(item, list):
                result.extend(self.flatten(item))
            else:
                result.append(item)
        return result

    def prefix_with_dictionary(self, s: str, is_dictionary_def: bool) -> Out:
        if is_dictionary_def:
            return self.lines(f"dictionary {s}")
        else:
            return self.lines(s)
