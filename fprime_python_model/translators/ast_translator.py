import json
from typing import Dict, List, Callable, Any, Tuple, Optional
import os
from fprime_python_model.fpp_ast.fpp_locations import Location
from fprime_python_model.fpp_ast import fpp_ast
from fprime_python_model.fpp_ast.fpp_ast_node import AstNode, AstId
from fprime_python_model.utils.error import (
    NotSupportedInFppToJsonException,
    InvalidFppToJsonField,
    InvalidFppToJsonDictionary,
)
from fprime_python_model.utils.error import InternalError


def get_queue_full(d: dict) -> fpp_ast.QueueFull:
    if "Assert" in d:
        return fpp_ast.QueueFull.ASSERT
    elif "Block" in d:
        return fpp_ast.QueueFull.BLOCK
    elif "Drop" in d:
        return fpp_ast.QueueFull.DROP
    elif "Hook" in d:
        return fpp_ast.QueueFull.HOOK
    else:
        raise InvalidFppToJsonDictionary("queue full behavior", d)


def translate_pattern_kind(d: dict) -> fpp_ast.PatternKind:
    kind = list(d.keys())[0]
    match kind:
        case "Command":
            return fpp_ast.PatternKind.COMMAND
        case "Event":
            return fpp_ast.PatternKind.EVENT
        case "Health":
            return fpp_ast.PatternKind.HEALTH
        case "Param":
            return fpp_ast.PatternKind.PARAM
        case "Telemetry":
            return fpp_ast.PatternKind.TELEMETRY
        case "TextEvent":
            return fpp_ast.PatternKind.TEXT_EVENT
        case "Time":
            return fpp_ast.PatternKind.TIME
        case _:
            raise InvalidFppToJsonDictionary("pattern kind", d)


def translate_special_kind(d: dict) -> fpp_ast.SpecialKind:
    if "CommandRecv" in d:
        return fpp_ast.SpecialKind.COMMAND_RECV
    elif "CommandReg" in d:
        return fpp_ast.SpecialKind.COMMAND_REG
    elif "CommandResp" in d:
        return fpp_ast.SpecialKind.COMMAND_RESP
    elif "Event" in d:
        return fpp_ast.SpecialKind.EVENT
    elif "ParamGet" in d:
        return fpp_ast.SpecialKind.PARAM_GET
    elif "ParamSet" in d:
        return fpp_ast.SpecialKind.PARAM_SET
    elif "ProductGet" in d:
        return fpp_ast.SpecialKind.PRODUCT_GET
    elif "ProductRecv" in d:
        return fpp_ast.SpecialKind.PRODUCT_RECV
    elif "ProductRequest" in d:
        return fpp_ast.SpecialKind.PRODUCT_REQUEST
    elif "ProductSend" in d:
        return fpp_ast.SpecialKind.PRODUCT_SEND
    elif "Telemetry" in d:
        return fpp_ast.SpecialKind.TELEMETRY
    elif "TextEvent" in d:
        return fpp_ast.SpecialKind.TEXT_EVENT
    elif "TimeGet" in d:
        return fpp_ast.SpecialKind.TIME_GET
    else:
        raise InvalidFppToJsonDictionary("special port instance kind", d)


def translate_general_kind(d: dict) -> fpp_ast.GeneralKind:
    if "AsyncInput" in d:
        return fpp_ast.GeneralKind.ASYNC_INPUT
    elif "GuardedInput" in d:
        return fpp_ast.GeneralKind.GUARDED_INPUT
    elif "Output" in d:
        return fpp_ast.GeneralKind.OUTPUT
    elif "SyncInput" in d:
        return fpp_ast.GeneralKind.SYNC_INPUT
    else:
        raise InvalidFppToJsonDictionary("general port instance kind", d)


def translate_spec_tlm_channel_update(d: dict) -> fpp_ast.SpecTlmChannelUpdate:
    if "Always" in d:
        return fpp_ast.SpecTlmChannelUpdate.ALWAYS
    elif "OnChange" in d:
        return fpp_ast.SpecTlmChannelUpdate.ON_CHANGE
    else:
        raise InvalidFppToJsonDictionary("telemetry channel update", d)


def translate_spec_loc_kind(d: dict) -> fpp_ast.SpecLocKind:
    if "Component" in d:
        return fpp_ast.SpecLocKind.COMPONENT
    elif "Instance" in d:
        return fpp_ast.SpecLocKind.INSTANCE
    elif "Constant" in d:
        return fpp_ast.SpecLocKind.CONSTANT
    elif "Port" in d:
        return fpp_ast.SpecLocKind.PORT
    elif "StateMachine" in d:
        return fpp_ast.SpecLocKind.STATE_MACHINE
    elif "Type" in d:
        return fpp_ast.SpecLocKind.TYPE
    elif "Interface" in d:
        return fpp_ast.SpecLocKind.INTERFACE
    else:
        raise InvalidFppToJsonDictionary("location specifier kind", d)


class AstTranslator:
    def __init__(self, ast_json_file: str, location_map: Dict[AstId, Location]):
        self.ast_json_file = ast_json_file
        self.location_map = location_map

    def read_ast_node(self, a_node: dict) -> Tuple[Any, AstId]:
        return a_node["AstNode"]["data"], a_node["AstNode"]["id"]

    def translate_string(self, d: dict) -> AstNode[str]:
        data, id = self.read_ast_node(d)
        return AstNode.create_with_id(data, id)

    def translate_ident(self, d: dict) -> AstNode[fpp_ast.Ident]:
        data, id = self.read_ast_node(d)
        return AstNode.create_with_id(fpp_ast.Ident(data), id)

    def translate_qual_ident(self, d: dict) -> AstNode[fpp_ast.QualIdent]:
        data, id = self.read_ast_node(d)
        if data.get("Unqualified"):
            return AstNode.create_with_id(
                fpp_ast.Unqualified(data["Unqualified"]["name"]), id
            )
        elif data.get("Qualified"):
            qualified = data["Qualified"]
            qualifier_dict = qualified["qualifier"]
            return AstNode.create_with_id(
                fpp_ast.Qualified(
                    self.translate_qual_ident(qualifier_dict),
                    self.translate_ident(qualified["name"]),
                ),
                id,
            )
        else:
            raise InternalError("Could not translate qualified identifier")

    def translate_formal_params(self, params_list: List) -> fpp_ast.FormalParamList:
        params = []
        for p in params_list:
            node = p[1]
            data, id = self.read_ast_node(node)
            name = data["name"]
            kind = fpp_ast.FormalParamKind.REF
            if "Value" in data["kind"]:
                kind = fpp_ast.FormalParamKind.VALUE
            type_name_node = self.translate_type_name(data["typeName"])
            formal_param = fpp_ast.FormalParam(kind, name, type_name_node)
            param_ast_node = AstNode.create_with_id(formal_param, id)
            params.append(self.annotate(p[0], param_ast_node, p[2]))
        return params

    def translate_type_name(self, tn: dict) -> AstNode[fpp_ast.TypeName]:
        data, id = self.read_ast_node(tn)
        if "TypeNameFloat" in data:
            name = list(data["TypeNameFloat"]["name"].keys())[0]
            return AstNode.create_with_id(fpp_ast.TypeNameFloat(name), id)
        elif "TypeNameInt" in data:
            name = list(data["TypeNameInt"]["name"].keys())[0]
            return AstNode.create_with_id(fpp_ast.TypeNameInt(name), id)
        elif "TypeNameQualIdent" in data:
            return AstNode.create_with_id(
                fpp_ast.TypeNameQualIdent(
                    self.translate_qual_ident(data["TypeNameQualIdent"]["name"])
                ),
                id,
            )
        elif "TypeNameBool" in data:
            return AstNode.create_with_id(fpp_ast.TypeNameBool(), id)
        elif "TypeNameString" in data:
            return AstNode.create_with_id(
                fpp_ast.TypeNameString(
                    self.translate_optional(
                        data["TypeNameString"]["size"], self.translate_expr
                    )
                ),
                id,
            )
        else:
            raise Exception(f"Invalid type name dictionary {data}")

    def translate_binop(self, d: dict) -> fpp_ast.Binop:
        if "Add" in d:
            return fpp_ast.Binop.ADD
        elif "Sub" in d:
            return fpp_ast.Binop.SUB
        elif "Mul" in d:
            return fpp_ast.Binop.MUL
        elif "Div" in d:
            return fpp_ast.Binop.DIV
        else:
            raise Exception(f"Invalid Binop JSON {d}")

    def translate_expr(self, expr_dict: dict) -> AstNode[fpp_ast.Expr]:
        data, id = self.read_ast_node(expr_dict)
        if "ExprArray" in data:
            elts = []
            for e in data["ExprArray"]["elts"]:
                elts.append(self.translate_expr(e))
            return AstNode.create_with_id(fpp_ast.ExprArray(elts), id)
        elif "ExprArraySubscript" in data:
            return AstNode.create_with_id(
                fpp_ast.ExprArraySubscript(
                    self.translate_expr(data["ExprArraySubscript"]["e1"]),
                    self.translate_expr(data["ExprArraySubscript"]["e2"]),
                ),
                id,
            )
        elif "ExprBinop" in data:
            return AstNode.create_with_id(
                fpp_ast.ExprBinop(
                    self.translate_expr(data["ExprBinop"]["e1"]),
                    self.translate_binop(data["ExprBinop"]["op"]),
                    self.translate_expr(data["ExprBinop"]["e2"]),
                ),
                id,
            )
        elif "ExprDot" in data:
            return AstNode.create_with_id(
                fpp_ast.ExprDot(
                    self.translate_expr(data["ExprDot"]["e"]),
                    self.translate_ident(data["ExprDot"]["id"]),
                ),
                id,
            )
        elif "ExprIdent" in data:
            return AstNode.create_with_id(
                fpp_ast.ExprIdent(data["ExprIdent"]["value"]), id
            )
        elif "ExprLiteralBool" in data:
            if "True" in data["ExprLiteralBool"]["value"]:
                literal_bool = fpp_ast.LiteralBool.TRUE
            else:
                literal_bool = fpp_ast.LiteralBool.FALSE
            return AstNode.create_with_id(fpp_ast.ExprLiteralBool(literal_bool), id)
        elif "ExprLiteralInt" in data:
            return AstNode.create_with_id(
                fpp_ast.ExprLiteralInt(data["ExprLiteralInt"]["value"]), id
            )
        elif "ExprLiteralFloat" in data:
            return AstNode.create_with_id(
                fpp_ast.ExprLiteralFloat(data["ExprLiteralFloat"]["value"]), id
            )
        elif "ExprLiteralString" in data:
            return AstNode.create_with_id(
                fpp_ast.ExprLiteralString(data["ExprLiteralString"]["value"]), id
            )
        elif "ExprParen" in data:
            return AstNode.create_with_id(
                fpp_ast.ExprParen(
                    self.translate_expr(data["ExprParen"]["e"]),
                ),
                id,
            )
        elif "ExprSizeOf" in data:
            return AstNode.create_with_id(
                fpp_ast.ExprSizeOf(
                    self.translate_type_name(data["ExprSizeOf"]["typeName"]),
                ),
                id,
            )
        elif "ExprStruct" in data:
            members = []
            for m in data["ExprStruct"]["members"]:
                members.append(
                    AstNode.create_with_id(
                        fpp_ast.StructMember(
                            m["AstNode"]["data"]["name"],
                            self.translate_expr(m["AstNode"]["data"]["value"]),
                        ),
                        m["AstNode"]["id"],
                    )
                )
            return AstNode.create_with_id(fpp_ast.ExprStruct(members), id)
        elif "ExprUnop" in data:
            return AstNode.create_with_id(
                fpp_ast.ExprUnop(
                    fpp_ast.Unop.MINUS, self.translate_expr(data["ExprUnop"]["e"])
                ),
                id,
            )
        else:
            raise InvalidFppToJsonDictionary(
                "expression", expr_dict, self.location_map.get(id, None)
            )

    def translate_throttle(self, d: Dict[str, dict]) -> AstNode[fpp_ast.EventThrottle]:
        return AstNode.create_with_id(
            fpp_ast.EventThrottle(
                self.translate_expr(d["AstNode"]["data"]["count"]),
                self.translate_optional(
                    d["AstNode"]["data"]["every"], self.translate_expr
                ),
            ),
            d["AstNode"]["id"],
        )

    def translate_transition_expr(self, te: dict) -> AstNode[fpp_ast.TransitionExpr]:
        data, id = self.read_ast_node(te)
        return AstNode.create_with_id(
            fpp_ast.TransitionExpr(
                self.translate_actions(data["actions"]),
                self.translate_qual_ident(data["target"]),
            ),
            id,
        )

    def translate_transition_or_do(self, t: dict) -> fpp_ast.TransitionOrDo:
        if "Transition" in t:
            return fpp_ast.Transition(
                self.translate_transition_expr(t["Transition"]["transition"])
            )
        elif "Do" in t:
            return fpp_ast.Do(self.translate_actions(t["Do"]["actions"]))
        else:
            raise InvalidFppToJsonDictionary("Transition or Do", t)

    def translate_actions(self, l: List) -> List[AstNode[fpp_ast.Ident]]:
        actions = []
        for a in l:
            actions.append(self.translate_ident(a))
        return actions

    def annotate(self, l1: List[str], d: fpp_ast.T, l2: List[str]) -> fpp_ast.Annotated:
        return (l1, d, l2)

    def translate_limit_kind(self, d: dict) -> AstNode[fpp_ast.LimitKind]:
        data, id = self.read_ast_node(d)
        limit_kind = fpp_ast.LimitKind.RED
        if "Yellow" in data:
            limit_kind = fpp_ast.LimitKind.YELLOW
        elif "Orange" in data:
            limit_kind = fpp_ast.LimitKind.ORANGE
        elif "Red" in data:
            limit_kind = fpp_ast.LimitKind.RED
        else:
            raise InvalidFppToJsonDictionary(
                "limit kind", d, self.location_map.get(id, None)
            )
        return AstNode.create_with_id(limit_kind, id)

    def translate_limits(self, l: List) -> List[fpp_ast.Limit]:
        limits = []
        for e in l:
            limits.append((self.translate_limit_kind(e[0]), self.translate_expr(e[1])))
        return limits

    def translate_spec_command_kind(self, d: dict) -> fpp_ast.SpecCommandKind:
        if "Async" in d:
            return fpp_ast.SpecCommandKind.ASYNC
        elif "Sync" in d:
            return fpp_ast.SpecCommandKind.SYNC
        elif "Guarded" in d:
            return fpp_ast.SpecCommandKind.GUARDED
        else:
            raise InvalidFppToJsonDictionary("command kind", d)

    def translate_severity(self, d: dict) -> fpp_ast.SpecEventSeverity:
        if "ActivityHigh" in d:
            return fpp_ast.SpecEventSeverity.ACTIVITY_HIGH
        elif "ActivityLow" in d:
            return fpp_ast.SpecEventSeverity.ACTIVITY_LOW
        elif "Command" in d:
            return fpp_ast.SpecEventSeverity.COMMAND
        elif "Diagnostic" in d:
            return fpp_ast.SpecEventSeverity.DIAGNOSTIC
        elif "Fatal" in d:
            return fpp_ast.SpecEventSeverity.FATAL
        elif "WarningHigh" in d:
            return fpp_ast.SpecEventSeverity.WARNING_HIGH
        elif "WarningLow" in d:
            return fpp_ast.SpecEventSeverity.WARNING_LOW
        else:
            raise InvalidFppToJsonDictionary("event severity", d)

    def translate_def_abs_type(
        self, data: dict, id: AstId
    ) -> AstNode[fpp_ast.DefAbsType]:
        return AstNode.create_with_id(fpp_ast.DefAbsType(data["name"]), id)

    def translate_def_alias_type(
        self, data: dict, id: AstId
    ) -> AstNode[fpp_ast.DefAliasType]:
        return AstNode.create_with_id(
            fpp_ast.DefAliasType(
                data["name"],
                self.translate_type_name(data["typeName"]),
                data["isDictionaryDef"],
            ),
            id,
        )

    def translate_def_array(self, data: dict, id: AstId) -> AstNode[fpp_ast.DefArray]:
        return AstNode.create_with_id(
            fpp_ast.DefArray(
                data["name"],
                self.translate_expr(data["size"]),
                self.translate_type_name(data["eltType"]),
                self.translate_optional(data["default"], self.translate_expr),
                self.translate_optional(data["format"], self.translate_string),
                data["isDictionaryDef"],
            ),
            id,
        )

    def translate_def_constant(
        self, data: dict, id: AstId
    ) -> AstNode[fpp_ast.DefConstant]:
        return AstNode.create_with_id(
            fpp_ast.DefConstant(
                data["name"],
                self.translate_expr(data["value"]),
                data["isDictionaryDef"],
            ),
            id,
        )

    def translate_def_enum(self, data: dict, id: AstId) -> AstNode[fpp_ast.DefEnum]:
        constants = []
        for c in data["constants"]:
            const = c[1]
            const_data, const_id = self.read_ast_node(const)
            node = AstNode.create_with_id(
                fpp_ast.DefEnumConstant(
                    const_data["name"],
                    self.translate_optional(const_data["value"], self.translate_expr),
                ),
                const_id,
            )
            constants.append(self.annotate(c[0], node, c[2]))
        return AstNode.create_with_id(
            fpp_ast.DefEnum(
                data["name"],
                self.translate_optional(data["typeName"], self.translate_type_name),
                constants,
                self.translate_optional(data["default"], self.translate_expr),
                data["isDictionaryDef"],
            ),
            id,
        )

    def translate_def_struct(self, data: dict, id: AstId) -> AstNode[fpp_ast.DefStruct]:
        struct_members = []
        for m in data["members"]:
            member_data, member_id = self.read_ast_node(m[1])
            node = AstNode.create_with_id(
                fpp_ast.StructTypeMember(
                    member_data["name"],
                    self.translate_optional(member_data["size"], self.translate_expr),
                    self.translate_type_name(member_data["typeName"]),
                    self.translate_optional(
                        member_data["format"], self.translate_string
                    ),
                ),
                member_id,
            )
            struct_members.append(self.annotate(m[0], node, m[2]))
        return AstNode.create_with_id(
            fpp_ast.DefStruct(
                data["name"],
                struct_members,
                self.translate_optional(data["default"], self.translate_expr),
                data["isDictionaryDef"],
            ),
            id,
        )

    def translate_component_members(self, l: list) -> List[fpp_ast.ComponentMember]:
        members = []
        for m in l:
            m_dict: dict = m[1]
            m_key = list(m_dict.keys())[0]
            data, id = self.read_ast_node(m_dict[m_key]["node"])
            member: Optional[fpp_ast.ComponentMemberNode] = None
            match m_key:
                case "DefAbsType":
                    member = fpp_ast.ComponentMemberDefAbsType(
                        self.translate_def_abs_type(data, id)
                    )
                case "DefAliasType":
                    member = fpp_ast.ComponentMemberDefAliasType(
                        self.translate_def_alias_type(data, id)
                    )
                case "DefArray":
                    member = fpp_ast.ComponentMemberDefArray(
                        self.translate_def_array(data, id)
                    )
                case "DefConstant":
                    member = fpp_ast.ComponentMemberDefConstant(
                        self.translate_def_constant(data, id)
                    )
                case "DefEnum":
                    member = fpp_ast.ComponentMemberDefEnum(
                        self.translate_def_enum(data, id)
                    )
                case "DefStruct":
                    member = fpp_ast.ComponentMemberDefStruct(
                        self.translate_def_struct(data, id)
                    )
                case "DefStateMachine":
                    member = fpp_ast.ComponentMemberDefStateMachine(
                        self.translate_state_machine(data, id)
                    )
                case "SpecStateMachineInstance":
                    member = fpp_ast.ComponentMemberSpecStateMachineInstance(
                        AstNode.create_with_id(
                            fpp_ast.SpecStateMachineInstance(
                                data["name"],
                                self.translate_qual_ident(data["stateMachine"]),
                                self.translate_optional(
                                    data["priority"], self.translate_expr
                                ),
                                self.translate_optional(
                                    data["queueFull"], get_queue_full
                                ),
                            ),
                            id,
                        )
                    )
                case "SpecCommand":
                    member = fpp_ast.ComponentMemberSpecCommand(
                        AstNode.create_with_id(
                            fpp_ast.SpecCommand(
                                self.translate_spec_command_kind(data["kind"]),
                                data["name"],
                                self.translate_formal_params(data["params"]),
                                self.translate_optional(
                                    data["opcode"], self.translate_expr
                                ),
                                self.translate_optional(
                                    data["priority"], self.translate_expr
                                ),
                                self.translate_optional(
                                    data["queueFull"], self.translate_queue_full
                                ),
                            ),
                            id,
                        )
                    )
                case "SpecTlmChannel":
                    member = fpp_ast.ComponentMemberSpecTlmChannel(
                        AstNode.create_with_id(
                            fpp_ast.SpecTlmChannel(
                                data["name"],
                                self.translate_type_name(data["typeName"]),
                                self.translate_optional(
                                    data["id"], self.translate_expr
                                ),
                                self.translate_optional(
                                    data["update"], translate_spec_tlm_channel_update
                                ),
                                self.translate_optional(
                                    data["format"], self.translate_string
                                ),
                                self.translate_limits(data["low"]),
                                self.translate_limits(data["high"]),
                            ),
                            id,
                        )
                    )
                case "SpecEvent":
                    member = fpp_ast.ComponentMemberSpecEvent(
                        AstNode.create_with_id(
                            fpp_ast.SpecEvent(
                                data["name"],
                                self.translate_formal_params(data["params"]),
                                self.translate_severity(data["severity"]),
                                self.translate_optional(
                                    data["id"], self.translate_expr
                                ),
                                self.translate_string(data["format"]),
                                self.translate_optional(
                                    data["throttle"], self.translate_throttle
                                ),
                            ),
                            id,
                        )
                    )
                case "SpecRecord":
                    member = fpp_ast.ComponentMemberSpecRecord(
                        AstNode.create_with_id(
                            fpp_ast.SpecRecord(
                                data["name"],
                                self.translate_type_name(data["recordType"]),
                                data["isArray"],
                                self.translate_optional(
                                    data["id"], self.translate_expr
                                ),
                            ),
                            id,
                        )
                    )
                case "SpecContainer":
                    member = fpp_ast.ComponentMemberSpecContainer(
                        AstNode.create_with_id(
                            fpp_ast.SpecContainer(
                                data["name"],
                                self.translate_optional(
                                    data["id"], self.translate_expr
                                ),
                                self.translate_optional(
                                    data["defaultPriority"], self.translate_expr
                                ),
                            ),
                            id,
                        )
                    )
                case "SpecParam":
                    member = fpp_ast.ComponentMemberSpecParam(
                        AstNode.create_with_id(
                            fpp_ast.SpecParam(
                                data["name"],
                                self.translate_type_name(data["typeName"]),
                                self.translate_optional(
                                    data["default"], self.translate_expr
                                ),
                                self.translate_optional(
                                    data["id"], self.translate_expr
                                ),
                                self.translate_optional(
                                    data["setOpcode"], self.translate_expr
                                ),
                                self.translate_optional(
                                    data["saveOpcode"], self.translate_expr
                                ),
                                data["isExternal"],
                            ),
                            id,
                        )
                    )
                case "SpecPortMatching":
                    member = fpp_ast.ComponentMemberSpecPortMatching(
                        AstNode.create_with_id(
                            fpp_ast.SpecPortMatching(
                                self.translate_ident(data["port1"]),
                                self.translate_ident(data["port2"]),
                            ),
                            id,
                        )
                    )
                case "SpecInternalPort":
                    member = fpp_ast.ComponentMemberSpecInternalPort(
                        AstNode.create_with_id(
                            fpp_ast.SpecInternalPort(
                                data["name"],
                                self.translate_formal_params(data["params"]),
                                self.translate_optional(
                                    data["priority"], self.translate_expr
                                ),
                                self.translate_optional(
                                    data["queueFull"], get_queue_full
                                ),
                            ),
                            id,
                        )
                    )
                case "SpecPortInstance":
                    member = fpp_ast.ComponentMemberSpecPortInstance(
                        AstNode.create_with_id(self.translate_port_instance(data), id)
                    )
                case "SpecImportInterface":
                    member = fpp_ast.ComponentMemberSpecImportInterface(
                        AstNode.create_with_id(
                            fpp_ast.SpecImport(self.translate_qual_ident(data["sym"])),
                            id,
                        )
                    )
                case _:
                    raise InvalidFppToJsonField(m_key, self.location_map.get(id, None))
            members.append(fpp_ast.ComponentMember(self.annotate(m[0], member, m[2])))
        return members

    def translate_state_members(self, l: List) -> List[fpp_ast.StateMember]:
        members = []
        for m in l:
            m_dict: dict = m[1]
            m_key = list(m_dict.keys())[0]
            data, id = self.read_ast_node(m_dict[m_key]["node"])
            member: Optional[fpp_ast.StateMemberNode] = None
            match m_key:
                case "DefChoice":
                    member = fpp_ast.StateMemberDefChoice(
                        AstNode.create_with_id(
                            fpp_ast.DefChoice(
                                data["name"],
                                self.translate_ident(data["guard"]),
                                self.translate_transition_expr(data["ifTransition"]),
                                self.translate_transition_expr(data["elseTransition"]),
                            ),
                            id,
                        )
                    )
                case "DefState":
                    member = fpp_ast.StateMemberDefState(
                        AstNode.create_with_id(
                            fpp_ast.DefState(
                                data["name"],
                                self.translate_state_members(data["members"]),
                            ),
                            id,
                        )
                    )
                case "SpecStateEntry":
                    member = fpp_ast.StateMemberSpecStateEntry(
                        AstNode.create_with_id(
                            fpp_ast.SpecStateEntry(
                                self.translate_actions(data["actions"])
                            ),
                            id,
                        )
                    )
                case "SpecStateExit":
                    member = fpp_ast.StateMemberSpecStateExit(
                        AstNode.create_with_id(
                            fpp_ast.SpecStateExit(
                                self.translate_actions(data["actions"])
                            ),
                            id,
                        )
                    )
                case "SpecInitialTransition":
                    member = fpp_ast.StateMemberSpecInitialTransition(
                        AstNode.create_with_id(
                            fpp_ast.SpecInitialTransition(
                                self.translate_transition_expr(data["transition"])
                            ),
                            id,
                        )
                    )
                case "SpecStateTransition":
                    signal = self.translate_ident(data["signal"])
                    transition_or_do = self.translate_transition_or_do(
                        data["transitionOrDo"]
                    )
                    member = fpp_ast.StateMemberSpecStateTransition(
                        AstNode.create_with_id(
                            fpp_ast.SpecStateTransition(
                                signal,
                                self.translate_optional(
                                    data["guard"], self.translate_ident
                                ),
                                transition_or_do,
                            ),
                            id,
                        )
                    )
                case _:
                    raise InvalidFppToJsonField(m_key, self.location_map.get(id, None))
            members.append(fpp_ast.StateMember(self.annotate(m[0], member, m[2])))
        return members

    def translate_port_instance_identifier(
        self,
        d: dict,
    ) -> AstNode[fpp_ast.PortInstanceIdentifier]:
        data, id = self.read_ast_node(d)
        return AstNode.create_with_id(
            fpp_ast.PortInstanceIdentifier(
                self.translate_qual_ident(data["interfaceInstance"]),
                self.translate_ident(data["portName"]),
            ),
            id,
        )

    def translate_tlm_channel_identifier(
        self, d: dict
    ) -> AstNode[fpp_ast.TlmChannelIdentifier]:
        data, id = self.read_ast_node(d)
        return AstNode.create_with_id(
            fpp_ast.TlmChannelIdentifier(
                self.translate_qual_ident(data["componentInstance"]),
                self.translate_ident(data["channelName"]),
            ),
            id,
        )

    def translate_special_input_kind(self, d: dict) -> fpp_ast.SpecialInputKind:
        if "Async" in d:
            return fpp_ast.SpecialInputKind.ASYNC
        elif "Sync" in d:
            return fpp_ast.SpecialInputKind.SYNC
        elif "Guarded" in d:
            return fpp_ast.SpecialInputKind.GUARDED
        else:
            raise InvalidFppToJsonDictionary("special input kind", d)

    def translate_optional(
        self, d: dict, func: Callable[[Any], fpp_ast.T]
    ) -> Optional[fpp_ast.T]:
        if "Some" in d:
            return func(d["Some"])
        else:
            return None

    def translate_queue_full(self, d: dict) -> AstNode[fpp_ast.QueueFull]:
        data, id = self.read_ast_node(d)
        return AstNode.create_with_id(get_queue_full(data), id)

    def translate_special_port_instance(self, d: dict) -> fpp_ast.SpecialPortInstance:
        return fpp_ast.SpecialPortInstance(
            self.translate_optional(d["inputKind"], self.translate_special_input_kind),
            translate_special_kind(d["kind"]),
            d["name"],
            self.translate_optional(d["priority"], self.translate_expr),
            self.translate_optional(d["queueFull"], self.translate_queue_full),
        )

    def translate_general_port_instance(self, d: dict) -> fpp_ast.GeneralPortInstance:
        return fpp_ast.GeneralPortInstance(
            translate_general_kind(d["kind"]),
            d["name"],
            self.translate_optional(d["size"], self.translate_expr),
            self.translate_optional(d["port"], self.translate_qual_ident),
            self.translate_optional(d["priority"], self.translate_expr),
            self.translate_optional(d["queueFull"], self.translate_queue_full),
        )

    def translate_port_instance(self, d: dict) -> fpp_ast.SpecPortInstance:
        if "Special" in d:
            return self.translate_special_port_instance(d["Special"])
        elif "General" in d:
            return self.translate_general_port_instance(d["General"])
        else:
            raise InvalidFppToJsonDictionary("port instance", d)

    def translate_init_specs(
        self, l: list
    ) -> List[fpp_ast.Annotated[AstNode[fpp_ast.SpecInit]]]:
        specs = []
        for e in l:
            spec_node = e[1]
            data = spec_node["AstNode"]["data"]
            id = spec_node["AstNode"]["id"]
            spec = AstNode.create_with_id(
                fpp_ast.SpecInit(self.translate_expr(data["phase"]), data["code"]), id
            )
            specs.append(self.annotate(e[0], spec, e[2]))
        return specs

    def translate_state_machine(
        self, data: dict, id: AstId
    ) -> AstNode[fpp_ast.DefStateMachine]:
        if data["members"] == "None":
            sm_members = []
        else:
            sm_members = self.translate_state_machine_members(data["members"])
        return AstNode.create_with_id(
            fpp_ast.DefStateMachine(data["name"], sm_members), id
        )

    def translate_interface_members(self, l: List) -> List[fpp_ast.InterfaceMember]:
        members = []
        for m in l:
            m_dict: dict = m[1]
            m_key = list(m_dict.keys())[0]
            id = m_dict[m_key]["node"]["AstNode"]["id"]
            data: dict = m_dict[m_key]["node"]["AstNode"]["data"]
            member: Optional[fpp_ast.InterfaceMemberNode] = None
            match m_key:
                case "SpecPortInstance":
                    member = fpp_ast.InterfaceMemberSpecPortInstance(
                        AstNode.create_with_id(self.translate_port_instance(data), id)
                    )
                case "SpecImportInterface":
                    member = fpp_ast.InterfaceMemberSpecImportInterface(
                        AstNode.create_with_id(
                            fpp_ast.SpecImport(self.translate_qual_ident(data["sym"])),
                            id,
                        )
                    )
                case _:
                    raise InvalidFppToJsonField(m_key, self.location_map.get(id, None))
            members.append(fpp_ast.InterfaceMember(self.annotate(m[0], member, m[2])))
        return members

    def translate_tlm_packet_set_members(
        self, d: dict
    ) -> List[fpp_ast.TlmPacketSetMember]:
        members = []
        for member in d:
            node = member[1]
            if "SpecTlmPacket" in node:
                spec_tlm_pkt_data, spec_tlm_pkt_id = self.read_ast_node(
                    node["SpecTlmPacket"]["node"]
                )
                tlm_pkt_members: List[fpp_ast.TlmPacketMember] = []
                for m in spec_tlm_pkt_data["members"]:
                    if "TlmChannelIdentifier" in m:
                        chan_ident_node = m["TlmChannelIdentifier"]["node"]
                        tlm_pkt_members.append(
                            fpp_ast.TlmPacketMemberTlmChannelIdentifier(
                                self.translate_tlm_channel_identifier(chan_ident_node)
                            )
                        )
                pkt = fpp_ast.TlmPacketSetMemberSpecTlmPacket(
                    AstNode.create_with_id(
                        fpp_ast.SpecTlmPacket(
                            spec_tlm_pkt_data["name"],
                            self.translate_optional(
                                spec_tlm_pkt_data["id"], self.translate_expr
                            ),
                            self.translate_expr(spec_tlm_pkt_data["group"]),
                            tlm_pkt_members,
                        ),
                        spec_tlm_pkt_id,
                    )
                )
                members.append(
                    fpp_ast.TlmPacketSetMember(self.annotate(member[0], pkt, member[2]))
                )
            elif "SpecInclude" in node:
                raise NotSupportedInFppToJsonException("SpecInclude")
        return members

    def translate_topology_members(self, l: List) -> List[fpp_ast.TopologyMember]:
        members = []
        for m in l:
            m_dict: dict = m[1]
            m_key = list(m_dict.keys())[0]
            id = m_dict[m_key]["node"]["AstNode"]["id"]
            data: dict = m_dict[m_key]["node"]["AstNode"]["data"]
            member: Optional[fpp_ast.TopologyMemberNode] = None
            match m_key:
                case "SpecInstance":
                    member = fpp_ast.TopologyMemberSpecInstance(
                        AstNode.create_with_id(
                            fpp_ast.SpecInstance(
                                self.translate_qual_ident(data["instance"])
                            ),
                            id,
                        )
                    )
                case "SpecConnectionGraph":
                    if "Direct" in data:
                        connections = []
                        for c in data["Direct"]["connections"]:
                            connections.append(
                                fpp_ast.Connection(
                                    c["isUnmatched"],
                                    self.translate_port_instance_identifier(
                                        c["fromPort"]
                                    ),
                                    self.translate_optional(
                                        c["fromIndex"], self.translate_expr
                                    ),
                                    self.translate_port_instance_identifier(
                                        c["toPort"]
                                    ),
                                    self.translate_optional(
                                        c["toIndex"], self.translate_expr
                                    ),
                                )
                            )
                        member = fpp_ast.TopologyMemberSpecConnectionGraph(
                            AstNode.create_with_id(
                                fpp_ast.Direct(data["Direct"]["name"], connections), id
                            )
                        )
                    elif "Pattern" in data:
                        targets = []
                        for t in data["Pattern"]["targets"]:
                            targets.append(self.translate_qual_ident(t))
                        connection_graph: fpp_ast.SpecConnectionGraph = fpp_ast.Pattern(
                            translate_pattern_kind(data["Pattern"]["kind"]),
                            self.translate_qual_ident(data["Pattern"]["source"]),
                            targets,
                        )

                        member = fpp_ast.TopologyMemberSpecConnectionGraph(
                            AstNode.create_with_id(connection_graph, id)
                        )
                    else:
                        raise InvalidFppToJsonDictionary(
                            "connection graph", data, self.location_map.get(id, None)
                        )
                case "SpecTlmPacketSet":
                    omitted = []
                    for o in data["omitted"]:
                        omitted.append(self.translate_tlm_channel_identifier(o))
                    member = fpp_ast.TopologyMemberSpecTlmPacketSet(
                        AstNode.create_with_id(
                            fpp_ast.SpecTlmPacketSet(
                                data["name"],
                                self.translate_tlm_packet_set_members(data["members"]),
                                omitted,
                            ),
                            id,
                        )
                    )
                case "SpecInstance":
                    member = fpp_ast.TopologyMemberSpecInstance(
                        AstNode.create_with_id(
                            fpp_ast.SpecInstance(
                                self.translate_qual_ident(data["instance"])
                            ),
                            id,
                        )
                    )
                case "SpecTopPort":
                    member = fpp_ast.TopologyMemberSpecTopPort(
                        AstNode.create_with_id(
                            fpp_ast.SpecTopPort(
                                fpp_ast.Ident(data["name"]),
                                self.translate_port_instance_identifier(
                                    data["underlyingPort"]
                                ),
                            ),
                            id,
                        )
                    )
                case "SpecInclude":
                    raise NotSupportedInFppToJsonException(m_key)
                case _:
                    raise InvalidFppToJsonField(m_key, self.location_map.get(id, None))
            members.append(fpp_ast.TopologyMember(self.annotate(m[0], member, m[2])))
        return members

    def translate_module_members(self, l: List) -> List[fpp_ast.ModuleMember]:
        members = []
        for m in l:
            m_dict: dict = m[1]
            m_key = list(m_dict.keys())[0]
            data, id = self.read_ast_node(m_dict[m_key]["node"])
            member: Optional[fpp_ast.ModuleMemberNode] = None
            match m_key:
                case "DefAbsType":
                    member = fpp_ast.ModuleMemberDefAbsType(
                        self.translate_def_abs_type(data, id)
                    )
                case "DefAliasType":
                    member = fpp_ast.ModuleMemberDefAliasType(
                        self.translate_def_alias_type(data, id)
                    )
                case "DefArray":
                    member = fpp_ast.ModuleMemberDefArray(
                        self.translate_def_array(data, id)
                    )
                case "DefComponent":
                    if "Active" in data["kind"]:
                        kind = fpp_ast.ComponentKind.ACTIVE
                    elif "Passive" in data["kind"]:
                        kind = fpp_ast.ComponentKind.PASSIVE
                    elif "Queued" in data["kind"]:
                        kind = fpp_ast.ComponentKind.QUEUED
                    else:
                        raise InvalidFppToJsonDictionary(
                            "component kind", data, self.location_map.get(id, None)
                        )
                    member = fpp_ast.ModuleMemberDefComponent(
                        AstNode.create_with_id(
                            fpp_ast.DefComponent(
                                kind,
                                data["name"],
                                self.translate_component_members(data["members"]),
                            ),
                            id,
                        )
                    )
                case "DefComponentInstance":
                    member = fpp_ast.ModuleMemberDefComponentInstance(
                        AstNode.create_with_id(
                            fpp_ast.DefComponentInstance(
                                data["name"],
                                self.translate_qual_ident(data["component"]),
                                self.translate_expr(data["baseId"]),
                                self.translate_optional(
                                    data["implType"], self.translate_string
                                ),
                                self.translate_optional(
                                    data["file"], self.translate_string
                                ),
                                self.translate_optional(
                                    data["queueSize"], self.translate_expr
                                ),
                                self.translate_optional(
                                    data["stackSize"], self.translate_expr
                                ),
                                self.translate_optional(
                                    data["priority"], self.translate_expr
                                ),
                                self.translate_optional(
                                    data["cpu"], self.translate_expr
                                ),
                                self.translate_init_specs(data["initSpecs"]),
                            ),
                            id,
                        )
                    )
                case "DefConstant":
                    member = fpp_ast.ModuleMemberDefConstant(
                        self.translate_def_constant(data, id)
                    )
                case "DefEnum":
                    member = fpp_ast.ModuleMemberDefEnum(
                        self.translate_def_enum(data, id)
                    )
                case "DefInterface":
                    member = fpp_ast.ModuleMemberDefInterface(
                        AstNode.create_with_id(
                            fpp_ast.DefInterface(
                                data["name"],
                                self.translate_interface_members(data["members"]),
                            ),
                            id,
                        )
                    )
                case "DefModule":
                    member = fpp_ast.ModuleMemberDefModule(
                        AstNode.create_with_id(
                            fpp_ast.DefModule(
                                data["name"],
                                self.translate_module_members(data["members"]),
                            ),
                            id,
                        )
                    )
                case "DefPort":
                    member = fpp_ast.ModuleMemberDefPort(
                        AstNode.create_with_id(
                            fpp_ast.DefPort(
                                data["name"],
                                self.translate_formal_params(data["params"]),
                                self.translate_optional(
                                    data["returnType"], self.translate_type_name
                                ),
                            ),
                            id,
                        )
                    )
                case "DefStateMachine":
                    member = fpp_ast.ModuleMemberDefStateMachine(
                        self.translate_state_machine(data, id)
                    )
                case "DefStruct":
                    member = fpp_ast.ModuleMemberDefStruct(
                        self.translate_def_struct(data, id)
                    )
                case "DefTopology":
                    member = fpp_ast.ModuleMemberDefTopology(
                        AstNode.create_with_id(
                            fpp_ast.DefTopology(
                                data["name"],
                                self.translate_topology_members(data["members"]),
                                [
                                    self.translate_qual_ident(n)
                                    for n in data["implements"]
                                ],
                            ),
                            id,
                        )
                    )
                case "SpecInclude":
                    raise NotSupportedInFppToJsonException(m_key)
                case "SpecLoc":
                    member = fpp_ast.ModuleMemberSpecLoc(
                        AstNode.create_with_id(
                            fpp_ast.SpecLoc(
                                translate_spec_loc_kind(data["kind"]),
                                self.translate_qual_ident(data["symbol"]),
                                self.translate_string(data["file"]),
                                data["isDictionaryDef"],
                            ),
                            id,
                        )
                    )
                case _:
                    raise InvalidFppToJsonField(m_key, self.location_map.get(id, None))
            members.append(fpp_ast.ModuleMember(self.annotate(m[0], member, m[2])))
        return members

    def translate_state_machine_members(
        self,
        d: Dict[str, List],
    ) -> List[fpp_ast.StateMachineMember]:
        members = []
        if d.get("Some"):
            for l in d["Some"]:
                for k, v in l[1].items():
                    data, id = self.read_ast_node(v["node"])
                    member: Optional[fpp_ast.StateMachineMemberNode] = None
                    match k:
                        case "DefAbsType":
                            member = fpp_ast.StateMachineMemberDefAbsType(
                                self.translate_def_abs_type(data, id)
                            )
                        case "DefAction":
                            member = fpp_ast.StateMachineMemberDefAction(
                                AstNode.create_with_id(
                                    fpp_ast.DefAction(
                                        data["name"],
                                        self.translate_optional(
                                            data["typeName"], self.translate_type_name
                                        ),
                                    ),
                                    id,
                                )
                            )
                        case "DefAliasType":
                            member = fpp_ast.StateMachineMemberDefAliasType(
                                self.translate_def_alias_type(data, id)
                            )
                        case "DefArray":
                            member = fpp_ast.StateMachineMemberDefArray(
                                self.translate_def_array(data, id)
                            )
                        case "DefChoice":
                            member = fpp_ast.StateMachineMemberDefChoice(
                                AstNode.create_with_id(
                                    fpp_ast.DefChoice(
                                        data["name"],
                                        self.translate_ident(data["guard"]),
                                        self.translate_transition_expr(
                                            data["ifTransition"]
                                        ),
                                        self.translate_transition_expr(
                                            data["elseTransition"]
                                        ),
                                    ),
                                    id,
                                )
                            )
                        case "DefConstant":
                            member = fpp_ast.StateMachineMemberDefConstant(
                                self.translate_def_constant(data, id)
                            )
                        case "DefEnum":
                            member = fpp_ast.StateMachineMemberDefEnum(
                                self.translate_def_enum(data, id)
                            )
                        case "DefGuard":
                            member = fpp_ast.StateMachineMemberDefGuard(
                                AstNode.create_with_id(
                                    fpp_ast.DefGuard(
                                        data["name"],
                                        self.translate_optional(
                                            data["typeName"], self.translate_type_name
                                        ),
                                    ),
                                    id,
                                )
                            )
                        case "DefSignal":
                            member = fpp_ast.StateMachineMemberDefSignal(
                                AstNode.create_with_id(
                                    fpp_ast.DefSignal(
                                        data["name"],
                                        self.translate_optional(
                                            data["typeName"], self.translate_type_name
                                        ),
                                    ),
                                    id,
                                )
                            )
                        case "DefState":
                            member = fpp_ast.StateMachineMemberDefState(
                                AstNode.create_with_id(
                                    fpp_ast.DefState(
                                        data["name"],
                                        self.translate_state_members(data["members"]),
                                    ),
                                    id,
                                )
                            )
                        case "DefStruct":
                            member = fpp_ast.StateMachineMemberDefStruct(
                                self.translate_def_struct(data, id)
                            )
                        case "SpecInclude":
                            member = fpp_ast.StateMachineMemberSpecInclude(
                                AstNode.create_with_id(
                                    fpp_ast.SpecInclude(
                                        self.translate_string(data["file"])
                                    ),
                                    id,
                                )
                            )
                        case "SpecInitialTransition":
                            member = fpp_ast.StateMachineMemberSpecInitialTransition(
                                AstNode.create_with_id(
                                    fpp_ast.SpecInitialTransition(
                                        self.translate_transition_expr(
                                            data["transition"]
                                        )
                                    ),
                                    id,
                                )
                            )
                        case _:
                            raise InvalidFppToJsonField(
                                k, self.location_map.get(id, None)
                            )
                    members.append(
                        fpp_ast.StateMachineMember(self.annotate(l[0], member, l[2]))
                    )
        return members

    def translate_trans_unit_list(self, l: List) -> List[fpp_ast.TransUnit]:
        trans_units = []
        for tu in l:
            trans_unit_members = self.translate_module_members(tu["members"])
            trans_units.append(fpp_ast.TransUnit(trans_unit_members))
        return trans_units

    def translate_ast_json(self) -> List[fpp_ast.TransUnit]:
        if not os.path.exists(self.ast_json_file):
            raise FileNotFoundError(f'File "{self.ast_json_file}" not found')
        with open(self.ast_json_file, "r") as f:
            data: Dict = json.load(f)
            return self.translate_trans_unit_list(data["ast"])
