import json
from typing import Dict, List, Callable, Any, Tuple, Optional
import os
from fprime_python_model.fpp_ast import fpp_ast
from fprime_python_model.fpp_ast.fpp_ast_node import AstNode, AstId
from fprime_python_model.utils.error import (
    NotSupportedInFppToJsonException,
    InvalidFppToJsonField,
    InvalidFppToJsonDictionary,
)
from fprime_python_model.utils.error import InternalError


def read_ast_node(a_node: dict) -> Tuple[Any, AstId]:
    return a_node["AstNode"]["data"], a_node["AstNode"]["id"]


def translate_string(d: dict) -> AstNode[str]:
    data, id = read_ast_node(d)
    return AstNode.create_with_id(data, id)


def translate_ident(d: dict) -> AstNode[fpp_ast.Ident]:
    data, id = read_ast_node(d)
    return AstNode.create_with_id(fpp_ast.Ident(data), id)


def translate_qual_ident(d: dict) -> AstNode[fpp_ast.QualIdent]:
    data, id = read_ast_node(d)
    if data.get("Unqualified"):
        return AstNode.create_with_id(
            fpp_ast.Unqualified(data["Unqualified"]["name"]), id
        )
    elif data.get("Qualified"):
        qualified = data["Qualified"]
        qualifier_dict = qualified["qualifier"]
        return AstNode.create_with_id(
            fpp_ast.Qualified(
                translate_qual_ident(qualifier_dict), translate_ident(qualified["name"])
            ),
            id,
        )
    else:
        raise InternalError("Could not translate qualified identifier")


def translate_formal_params(params_list: List) -> fpp_ast.FormalParamList:
    params = []
    for p in params_list:
        node = p[1]
        data, id = read_ast_node(node)
        name = data["name"]
        kind = fpp_ast.FormalParamKind.REF
        if "Value" in data["kind"]:
            kind = fpp_ast.FormalParamKind.VALUE
        type_name_node = translate_type_name(data["typeName"])
        formal_param = fpp_ast.FormalParam(kind, name, type_name_node)
        param_ast_node = AstNode.create_with_id(formal_param, id)
        params.append(annotate(p[0], param_ast_node, p[2]))
    return params


def translate_type_name(tn: dict) -> AstNode[fpp_ast.TypeName]:
    data, id = read_ast_node(tn)
    if "TypeNameFloat" in data:
        name = list(data["TypeNameFloat"]["name"].keys())[0]
        return AstNode.create_with_id(fpp_ast.TypeNameFloat(name), id)
    elif "TypeNameInt" in data:
        name = list(data["TypeNameInt"]["name"].keys())[0]
        return AstNode.create_with_id(fpp_ast.TypeNameInt(name), id)
    elif "TypeNameQualIdent" in data:
        return AstNode.create_with_id(
            fpp_ast.TypeNameQualIdent(
                translate_qual_ident(data["TypeNameQualIdent"]["name"])
            ),
            id,
        )
    elif "TypeNameBool" in data:
        return AstNode.create_with_id(fpp_ast.TypeNameBool(), id)
    elif "TypeNameString" in data:
        return AstNode.create_with_id(
            fpp_ast.TypeNameString(
                translate_optional(data["TypeNameString"]["size"], translate_expr)
            ),
            id,
        )
    else:
        raise Exception(f"Invalid type name dictionary {data}")


def translate_binop(d: dict) -> fpp_ast.Binop:
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


def translate_expr(expr_dict: dict) -> AstNode[fpp_ast.Expr]:
    data, id = read_ast_node(expr_dict)
    if "ExprArray" in data:
        elts = []
        for e in data["ExprArray"]["elts"]:
            elts.append(translate_expr(e))
        return AstNode.create_with_id(fpp_ast.ExprArray(elts), id)
    elif "ExprArraySubscript" in data:
        return AstNode.create_with_id(
            fpp_ast.ExprArraySubscript(
                translate_expr(data["ExprArraySubscript"]["e1"]),
                translate_expr(data["ExprArraySubscript"]["e2"]),
            ),
            id,
        )
    elif "ExprBinop" in data:
        return AstNode.create_with_id(
            fpp_ast.ExprBinop(
                translate_expr(data["ExprBinop"]["e1"]),
                translate_binop(data["ExprBinop"]["op"]),
                translate_expr(data["ExprBinop"]["e2"]),
            ),
            id,
        )
    elif "ExprDot" in data:
        return AstNode.create_with_id(
            fpp_ast.ExprDot(
                translate_expr(data["ExprDot"]["e"]),
                translate_ident(data["ExprDot"]["id"]),
            ),
            id,
        )
    elif "ExprIdent" in data:
        return AstNode.create_with_id(fpp_ast.ExprIdent(data["ExprIdent"]["value"]), id)
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
                translate_expr(data["ExprParen"]["e"]),
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
                        translate_expr(m["AstNode"]["data"]["value"]),
                    ),
                    m["AstNode"]["id"],
                )
            )
        return AstNode.create_with_id(fpp_ast.ExprStruct(members), id)
    elif "ExprUnop" in data:
        return AstNode.create_with_id(
            fpp_ast.ExprUnop(fpp_ast.Unop.MINUS, translate_expr(data["ExprUnop"]["e"])),
            id,
        )
    else:
        raise InvalidFppToJsonDictionary("expression", expr_dict)


def translate_throttle(d: Dict[str, dict]) -> AstNode[fpp_ast.EventThrottle]:
    return AstNode.create_with_id(
        fpp_ast.EventThrottle(
            translate_expr(d["AstNode"]["data"]["count"]),
            translate_optional(d["AstNode"]["data"]["every"], translate_expr),
        ),
        d["AstNode"]["id"],
    )


def translate_transition_expr(te: dict) -> AstNode[fpp_ast.TransitionExpr]:
    data, id = read_ast_node(te)
    return AstNode.create_with_id(
        fpp_ast.TransitionExpr(
            translate_actions(data["actions"]), translate_qual_ident(data["target"])
        ),
        id,
    )


def translate_transition_or_do(t: dict) -> fpp_ast.TransitionOrDo:
    if "Transition" in t:
        return fpp_ast.Transition(
            translate_transition_expr(t["Transition"]["transition"])
        )
    elif "Do" in t:
        return fpp_ast.Do(translate_actions(t["Do"]["actions"]))
    else:
        raise InvalidFppToJsonDictionary("Transition or Do", t)


def translate_actions(l: List) -> List[AstNode[fpp_ast.Ident]]:
    actions = []
    for a in l:
        actions.append(translate_ident(a))
    return actions


def annotate(l1: List[str], d: fpp_ast.T, l2: List[str]) -> fpp_ast.Annotated:
    return (l1, d, l2)


def translate_limit_kind(d: dict) -> AstNode[fpp_ast.LimitKind]:
    data, id = read_ast_node(d)
    limit_kind = fpp_ast.LimitKind.RED
    if "Yellow" in data:
        limit_kind = fpp_ast.LimitKind.YELLOW
    elif "Orange" in data:
        limit_kind = fpp_ast.LimitKind.ORANGE
    elif "Red" in data:
        limit_kind = fpp_ast.LimitKind.RED
    else:
        raise InvalidFppToJsonDictionary("limit kind", d)
    return AstNode.create_with_id(limit_kind, id)


def translate_spec_tlm_channel_update(d: dict) -> fpp_ast.SpecTlmChannelUpdate:
    if "Always" in d:
        return fpp_ast.SpecTlmChannelUpdate.ALWAYS
    elif "OnChange" in d:
        return fpp_ast.SpecTlmChannelUpdate.ON_CHANGE
    else:
        raise InvalidFppToJsonDictionary("telemetry channel update", d)


def translate_limits(l: List) -> List[fpp_ast.Limit]:
    limits = []
    for e in l:
        limits.append((translate_limit_kind(e[0]), translate_expr(e[1])))
    return limits


def translate_spec_loc_kind(d: dict) -> fpp_ast.SpecLocKind:
    if "Component" in d:
        return fpp_ast.SpecLocKind.COMPONENT
    elif "ComponentInstance" in d:
        return fpp_ast.SpecLocKind.COMPONENT_INSTANCE
    elif "Constant" in d:
        return fpp_ast.SpecLocKind.CONSTANT
    elif "Port" in d:
        return fpp_ast.SpecLocKind.PORT
    elif "StateMachine" in d:
        return fpp_ast.SpecLocKind.STATE_MACHINE
    elif "Topology" in d:
        return fpp_ast.SpecLocKind.TOPOLOGY
    elif "Type" in d:
        return fpp_ast.SpecLocKind.TYPE
    elif "Interface" in d:
        return fpp_ast.SpecLocKind.INTERFACE
    else:
        raise InvalidFppToJsonDictionary("spec loc kind", d)


def translate_spec_command_kind(d: dict) -> fpp_ast.SpecCommandKind:
    if "Async" in d:
        return fpp_ast.SpecCommandKind.ASYNC
    elif "Sync" in d:
        return fpp_ast.SpecCommandKind.SYNC
    elif "Guarded" in d:
        return fpp_ast.SpecCommandKind.GUARDED
    else:
        raise InvalidFppToJsonDictionary("command kind", d)


def translate_severity(d: dict) -> fpp_ast.SpecEventSeverity:
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


def translate_def_abs_type(data: dict, id: AstId) -> AstNode[fpp_ast.DefAbsType]:
    return AstNode.create_with_id(fpp_ast.DefAbsType(data["name"]), id)


def translate_def_alias_type(data: dict, id: AstId) -> AstNode[fpp_ast.DefAliasType]:
    return AstNode.create_with_id(
        fpp_ast.DefAliasType(
            data["name"], translate_type_name(data["typeName"]), data["isDictionaryDef"]
        ),
        id,
    )


def translate_def_array(data: dict, id: AstId) -> AstNode[fpp_ast.DefArray]:
    return AstNode.create_with_id(
        fpp_ast.DefArray(
            data["name"],
            translate_expr(data["size"]),
            translate_type_name(data["eltType"]),
            translate_optional(data["default"], translate_expr),
            translate_optional(data["format"], translate_string),
            data["isDictionaryDef"],
        ),
        id,
    )


def translate_def_constant(data: dict, id: AstId) -> AstNode[fpp_ast.DefConstant]:
    return AstNode.create_with_id(
        fpp_ast.DefConstant(
            data["name"], translate_expr(data["value"]), data["isDictionaryDef"]
        ),
        id,
    )


def translate_def_enum(data: dict, id: AstId) -> AstNode[fpp_ast.DefEnum]:
    constants = []
    for c in data["constants"]:
        const = c[1]
        const_data, const_id = read_ast_node(const)
        node = AstNode.create_with_id(
            fpp_ast.DefEnumConstant(
                const_data["name"],
                translate_optional(const_data["value"], translate_expr),
            ),
            const_id,
        )
        constants.append(annotate(c[0], node, c[2]))
    return AstNode.create_with_id(
        fpp_ast.DefEnum(
            data["name"],
            translate_optional(data["typeName"], translate_type_name),
            constants,
            translate_optional(data["default"], translate_expr),
            data["isDictionaryDef"],
        ),
        id,
    )


def translate_def_struct(data: dict, id: AstId) -> AstNode[fpp_ast.DefStruct]:
    struct_members = []
    for m in data["members"]:
        member_data, member_id = read_ast_node(m[1])
        node = AstNode.create_with_id(
            fpp_ast.StructTypeMember(
                member_data["name"],
                translate_optional(member_data["size"], translate_expr),
                translate_type_name(member_data["typeName"]),
                translate_optional(member_data["format"], translate_string),
            ),
            member_id,
        )
        struct_members.append(annotate(m[0], node, m[2]))
    return AstNode.create_with_id(
        fpp_ast.DefStruct(
            data["name"],
            struct_members,
            translate_optional(data["default"], translate_expr),
            data["isDictionaryDef"],
        ),
        id,
    )


def translate_component_members(l: list) -> List[fpp_ast.ComponentMember]:
    members = []
    for m in l:
        m_dict: dict = m[1]
        m_key = list(m_dict.keys())[0]
        data, id = read_ast_node(m_dict[m_key]["node"])
        member: Optional[fpp_ast.ComponentMemberNode] = None
        match m_key:
            case "DefAbsType":
                member = fpp_ast.ComponentMemberDefAbsType(
                    translate_def_abs_type(data, id)
                )
            case "DefAliasType":
                member = fpp_ast.ComponentMemberDefAliasType(
                    translate_def_alias_type(data, id)
                )
            case "DefArray":
                member = fpp_ast.ComponentMemberDefArray(translate_def_array(data, id))
            case "DefConstant":
                member = fpp_ast.ComponentMemberDefConstant(
                    translate_def_constant(data, id)
                )
            case "DefEnum":
                member = fpp_ast.ComponentMemberDefEnum(translate_def_enum(data, id))
            case "DefStruct":
                member = fpp_ast.ComponentMemberDefStruct(
                    translate_def_struct(data, id)
                )
            case "DefStateMachine":
                member = fpp_ast.ComponentMemberDefStateMachine(
                    translate_state_machine(data, id)
                )
            case "SpecStateMachineInstance":
                member = fpp_ast.ComponentMemberSpecStateMachineInstance(
                    AstNode.create_with_id(
                        fpp_ast.SpecStateMachineInstance(
                            data["name"],
                            translate_qual_ident(data["stateMachine"]),
                            translate_optional(data["priority"], translate_expr),
                            translate_optional(data["queueFull"], get_queue_full),
                        ),
                        id,
                    )
                )
            case "SpecCommand":
                member = fpp_ast.ComponentMemberSpecCommand(
                    AstNode.create_with_id(
                        fpp_ast.SpecCommand(
                            translate_spec_command_kind(data["kind"]),
                            data["name"],
                            translate_formal_params(data["params"]),
                            translate_optional(data["opcode"], translate_expr),
                            translate_optional(data["priority"], translate_expr),
                            translate_optional(data["queueFull"], translate_queue_full),
                        ),
                        id,
                    )
                )
            case "SpecTlmChannel":
                member = fpp_ast.ComponentMemberSpecTlmChannel(
                    AstNode.create_with_id(
                        fpp_ast.SpecTlmChannel(
                            data["name"],
                            translate_type_name(data["typeName"]),
                            translate_optional(data["id"], translate_expr),
                            translate_optional(
                                data["update"], translate_spec_tlm_channel_update
                            ),
                            translate_optional(data["format"], translate_string),
                            translate_limits(data["low"]),
                            translate_limits(data["high"]),
                        ),
                        id,
                    )
                )
            case "SpecEvent":
                member = fpp_ast.ComponentMemberSpecEvent(
                    AstNode.create_with_id(
                        fpp_ast.SpecEvent(
                            data["name"],
                            translate_formal_params(data["params"]),
                            translate_severity(data["severity"]),
                            translate_optional(data["id"], translate_expr),
                            translate_string(data["format"]),
                            translate_optional(data["throttle"], translate_throttle),
                        ),
                        id,
                    )
                )
            case "SpecRecord":
                member = fpp_ast.ComponentMemberSpecRecord(
                    AstNode.create_with_id(
                        fpp_ast.SpecRecord(
                            data["name"],
                            translate_type_name(data["recordType"]),
                            data["isArray"],
                            translate_optional(data["id"], translate_expr),
                        ),
                        id,
                    )
                )
            case "SpecContainer":
                member = fpp_ast.ComponentMemberSpecContainer(
                    AstNode.create_with_id(
                        fpp_ast.SpecContainer(
                            data["name"],
                            translate_optional(data["id"], translate_expr),
                            translate_optional(data["defaultPriority"], translate_expr),
                        ),
                        id,
                    )
                )
            case "SpecParam":
                member = fpp_ast.ComponentMemberSpecParam(
                    AstNode.create_with_id(
                        fpp_ast.SpecParam(
                            data["name"],
                            translate_type_name(data["typeName"]),
                            translate_optional(data["default"], translate_expr),
                            translate_optional(data["id"], translate_expr),
                            translate_optional(data["setOpcode"], translate_expr),
                            translate_optional(data["saveOpcode"], translate_expr),
                            data["isExternal"],
                        ),
                        id,
                    )
                )
            case "SpecPortMatching":
                member = fpp_ast.ComponentMemberSpecPortMatching(
                    AstNode.create_with_id(
                        fpp_ast.SpecPortMatching(
                            translate_ident(data["port1"]),
                            translate_ident(data["port2"]),
                        ),
                        id,
                    )
                )
            case "SpecInternalPort":
                member = fpp_ast.ComponentMemberSpecInternalPort(
                    AstNode.create_with_id(
                        fpp_ast.SpecInternalPort(
                            data["name"],
                            translate_formal_params(data["params"]),
                            translate_optional(data["priority"], translate_expr),
                            translate_optional(data["queueFull"], get_queue_full),
                        ),
                        id,
                    )
                )
            case "SpecPortInstance":
                member = fpp_ast.ComponentMemberSpecPortInstance(
                    AstNode.create_with_id(translate_port_instance(data), id)
                )
            case "SpecImportInterface":
                member = fpp_ast.ComponentMemberSpecImportInterface(
                    AstNode.create_with_id(
                        fpp_ast.SpecImport(translate_qual_ident(data["sym"])), id
                    )
                )
            case _:
                raise InvalidFppToJsonField(m_key)
        members.append(fpp_ast.ComponentMember(annotate(m[0], member, m[2])))
    return members


def translate_state_members(l: List) -> List[fpp_ast.StateMember]:
    members = []
    for m in l:
        m_dict: dict = m[1]
        m_key = list(m_dict.keys())[0]
        data, id = read_ast_node(m_dict[m_key]["node"])
        member: Optional[fpp_ast.StateMemberNode] = None
        match m_key:
            case "DefChoice":
                member = fpp_ast.StateMemberDefChoice(
                    AstNode.create_with_id(
                        fpp_ast.DefChoice(
                            data["name"],
                            translate_ident(data["guard"]),
                            translate_transition_expr(data["ifTransition"]),
                            translate_transition_expr(data["elseTransition"]),
                        ),
                        id,
                    )
                )
            case "DefState":
                member = fpp_ast.StateMemberDefState(
                    AstNode.create_with_id(
                        fpp_ast.DefState(
                            data["name"], translate_state_members(data["members"])
                        ),
                        id,
                    )
                )
            case "SpecStateEntry":
                member = fpp_ast.StateMemberSpecStateEntry(
                    AstNode.create_with_id(
                        fpp_ast.SpecStateEntry(translate_actions(data["actions"])), id
                    )
                )
            case "SpecStateExit":
                member = fpp_ast.StateMemberSpecStateExit(
                    AstNode.create_with_id(
                        fpp_ast.SpecStateExit(translate_actions(data["actions"])), id
                    )
                )
            case "SpecInitialTransition":
                member = fpp_ast.StateMemberSpecInitialTransition(
                    AstNode.create_with_id(
                        fpp_ast.SpecInitialTransition(
                            translate_transition_expr(data["transition"])
                        ),
                        id,
                    )
                )
            case "SpecStateTransition":
                signal = translate_ident(data["signal"])
                transition_or_do = translate_transition_or_do(data["transitionOrDo"])
                member = fpp_ast.StateMemberSpecStateTransition(
                    AstNode.create_with_id(
                        fpp_ast.SpecStateTransition(
                            signal,
                            translate_optional(data["guard"], translate_ident),
                            transition_or_do,
                        ),
                        id,
                    )
                )
            case _:
                raise InvalidFppToJsonField(m_key)
        members.append(fpp_ast.StateMember(annotate(m[0], member, m[2])))
    return members


def translate_port_instance_identifier(
    d: dict,
) -> AstNode[fpp_ast.PortInstanceIdentifier]:
    data, id = read_ast_node(d)
    return AstNode.create_with_id(
        fpp_ast.PortInstanceIdentifier(
            translate_qual_ident(data["componentInstance"]),
            translate_ident(data["portName"]),
        ),
        id,
    )


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


def translate_tlm_channel_identifier(d: dict) -> AstNode[fpp_ast.TlmChannelIdentifier]:
    data, id = read_ast_node(d)
    return AstNode.create_with_id(
        fpp_ast.TlmChannelIdentifier(
            translate_qual_ident(data["componentInstance"]),
            translate_ident(data["channelName"]),
        ),
        id,
    )


def translate_special_input_kind(d: dict) -> fpp_ast.SpecialInputKind:
    if "Async" in d:
        return fpp_ast.SpecialInputKind.ASYNC
    elif "Sync" in d:
        return fpp_ast.SpecialInputKind.SYNC
    elif "Guarded" in d:
        return fpp_ast.SpecialInputKind.GUARDED
    else:
        raise InvalidFppToJsonDictionary("special input kind", d)


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
        raise InvalidFppToJsonDictionary("special kind", d)


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
        raise InvalidFppToJsonDictionary("general kind", d)


def translate_optional(
    d: dict, func: Callable[[Any], fpp_ast.T]
) -> Optional[fpp_ast.T]:
    if "Some" in d:
        return func(d["Some"])
    else:
        return None


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
        raise InvalidFppToJsonDictionary("queue full", d)


def translate_queue_full(d: dict) -> AstNode[fpp_ast.QueueFull]:
    data, id = read_ast_node(d)
    return AstNode.create_with_id(get_queue_full(data), id)


def translate_special_port_instance(d: dict) -> fpp_ast.SpecialPortInstance:
    return fpp_ast.SpecialPortInstance(
        translate_optional(d["inputKind"], translate_special_input_kind),
        translate_special_kind(d["kind"]),
        d["name"],
        translate_optional(d["priority"], translate_expr),
        translate_optional(d["queueFull"], translate_queue_full),
    )


def translate_general_port_instance(d: dict) -> fpp_ast.GeneralPortInstance:
    return fpp_ast.GeneralPortInstance(
        translate_general_kind(d["kind"]),
        d["name"],
        translate_optional(d["size"], translate_expr),
        translate_optional(d["port"], translate_qual_ident),
        translate_optional(d["priority"], translate_expr),
        translate_optional(d["queueFull"], translate_queue_full),
    )


def translate_port_instance(d: dict) -> fpp_ast.SpecPortInstance:
    if "Special" in d:
        return translate_special_port_instance(d["Special"])
    elif "General" in d:
        return translate_general_port_instance(d["General"])
    else:
        raise InvalidFppToJsonDictionary("port instance", d)


def translate_init_specs(l: list) -> List[fpp_ast.Annotated[AstNode[fpp_ast.SpecInit]]]:
    specs = []
    for e in l:
        spec_node = e[1]
        data = spec_node["AstNode"]["data"]
        id = spec_node["AstNode"]["id"]
        spec = AstNode.create_with_id(
            fpp_ast.SpecInit(translate_expr(data["phase"]), data["code"]), id
        )
        specs.append(annotate(e[0], spec, e[2]))
    return specs


def translate_state_machine(data: dict, id: AstId) -> AstNode[fpp_ast.DefStateMachine]:
    if data["members"] == "None":
        sm_members = []
    else:
        sm_members = translate_state_machine_members(data["members"])
    return AstNode.create_with_id(fpp_ast.DefStateMachine(data["name"], sm_members), id)


def translate_interface_members(l: List) -> List[fpp_ast.InterfaceMember]:
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
                    AstNode.create_with_id(translate_port_instance(data), id)
                )
            case "SpecImportInterface":
                member = fpp_ast.InterfaceMemberSpecImportInterface(
                    AstNode.create_with_id(
                        fpp_ast.SpecImport(translate_qual_ident(data["sym"])), id
                    )
                )
            case _:
                raise InvalidFppToJsonField(m_key)
        members.append(fpp_ast.InterfaceMember(annotate(m[0], member, m[2])))
    return members


def translate_tlm_packet_set_members(d: dict) -> List[fpp_ast.TlmPacketSetMember]:
    members = []
    for member in d:
        node = member[1]
        if "SpecTlmPacket" in node:
            spec_tlm_pkt_data, spec_tlm_pkt_id = read_ast_node(
                node["SpecTlmPacket"]["node"]
            )
            tlm_pkt_members: List[fpp_ast.TlmPacketMember] = []
            for m in spec_tlm_pkt_data["members"]:
                if "TlmChannelIdentifier" in m:
                    chan_ident_node = m["TlmChannelIdentifier"]["node"]
                    tlm_pkt_members.append(
                        fpp_ast.TlmPacketMemberTlmChannelIdentifier(
                            translate_tlm_channel_identifier(chan_ident_node)
                        )
                    )
            pkt = fpp_ast.TlmPacketSetMemberSpecTlmPacket(
                AstNode.create_with_id(
                    fpp_ast.SpecTlmPacket(
                        spec_tlm_pkt_data["name"],
                        translate_optional(spec_tlm_pkt_data["id"], translate_expr),
                        translate_expr(spec_tlm_pkt_data["group"]),
                        tlm_pkt_members,
                    ),
                    spec_tlm_pkt_id,
                )
            )
            members.append(
                fpp_ast.TlmPacketSetMember(annotate(member[0], pkt, member[2]))
            )
        elif "SpecInclude" in node:
            raise NotSupportedInFppToJsonException("SpecInclude")
    return members


def translate_topology_members(l: List) -> List[fpp_ast.TopologyMember]:
    members = []
    for m in l:
        m_dict: dict = m[1]
        m_key = list(m_dict.keys())[0]
        id = m_dict[m_key]["node"]["AstNode"]["id"]
        data: dict = m_dict[m_key]["node"]["AstNode"]["data"]
        member: Optional[fpp_ast.TopologyMemberNode] = None
        match m_key:
            case "SpecCompInstance":
                visibility = fpp_ast.Visibility.PRIVATE
                if "Public" in data["visibility"]:
                    visibility = fpp_ast.Visibility.PUBLIC
                member = fpp_ast.TopologyMemberSpecCompInstance(
                    AstNode.create_with_id(
                        fpp_ast.SpecCompInstance(
                            visibility, translate_qual_ident(data["instance"])
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
                                translate_port_instance_identifier(c["fromPort"]),
                                translate_optional(c["fromIndex"], translate_expr),
                                translate_port_instance_identifier(c["toPort"]),
                                translate_optional(c["toIndex"], translate_expr),
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
                        targets.append(translate_qual_ident(t))
                    connection_graph: fpp_ast.SpecConnectionGraph = fpp_ast.Pattern(
                        translate_pattern_kind(data["Pattern"]["kind"]),
                        translate_qual_ident(data["Pattern"]["source"]),
                        targets,
                    )

                    member = fpp_ast.TopologyMemberSpecConnectionGraph(
                        AstNode.create_with_id(connection_graph, id)
                    )
                else:
                    raise InvalidFppToJsonDictionary("SpecConnectionGraph", data)
            case "SpecTlmPacketSet":
                omitted = []
                for o in data["omitted"]:
                    omitted.append(translate_tlm_channel_identifier(o))
                member = fpp_ast.TopologyMemberSpecTlmPacketSet(
                    AstNode.create_with_id(
                        fpp_ast.SpecTlmPacketSet(
                            data["name"],
                            translate_tlm_packet_set_members(data["members"]),
                            omitted,
                        ),
                        id,
                    )
                )
            case "SpecTopImport":
                member = fpp_ast.TopologyMemberSpecTopImport(
                    AstNode.create_with_id(
                        fpp_ast.SpecImport(translate_qual_ident(data["sym"])), id
                    )
                )
            case "SpecInclude":
                raise NotSupportedInFppToJsonException(m_key)
            case _:
                raise InvalidFppToJsonField(m_key)
        members.append(fpp_ast.TopologyMember(annotate(m[0], member, m[2])))
    return members


def translate_module_members(l: List) -> List[fpp_ast.ModuleMember]:
    members = []
    for m in l:
        m_dict: dict = m[1]
        m_key = list(m_dict.keys())[0]
        data, id = read_ast_node(m_dict[m_key]["node"])
        member: Optional[fpp_ast.ModuleMemberNode] = None
        match m_key:
            case "DefAbsType":
                member = fpp_ast.ModuleMemberDefAbsType(
                    translate_def_abs_type(data, id)
                )
            case "DefAliasType":
                member = fpp_ast.ModuleMemberDefAliasType(
                    translate_def_alias_type(data, id)
                )
            case "DefArray":
                member = fpp_ast.ModuleMemberDefArray(translate_def_array(data, id))
            case "DefComponent":
                if "Active" in data["kind"]:
                    kind = fpp_ast.ComponentKind.ACTIVE
                elif "Passive" in data["kind"]:
                    kind = fpp_ast.ComponentKind.PASSIVE
                elif "Queued" in data["kind"]:
                    kind = fpp_ast.ComponentKind.QUEUED
                else:
                    raise InvalidFppToJsonDictionary("component kind", data)
                member = fpp_ast.ModuleMemberDefComponent(
                    AstNode.create_with_id(
                        fpp_ast.DefComponent(
                            kind,
                            data["name"],
                            translate_component_members(data["members"]),
                        ),
                        id,
                    )
                )
            case "DefComponentInstance":
                member = fpp_ast.ModuleMemberDefComponentInstance(
                    AstNode.create_with_id(
                        fpp_ast.DefComponentInstance(
                            data["name"],
                            translate_qual_ident(data["component"]),
                            translate_expr(data["baseId"]),
                            translate_optional(data["implType"], translate_string),
                            translate_optional(data["file"], translate_string),
                            translate_optional(data["queueSize"], translate_expr),
                            translate_optional(data["stackSize"], translate_expr),
                            translate_optional(data["priority"], translate_expr),
                            translate_optional(data["cpu"], translate_expr),
                            translate_init_specs(data["initSpecs"]),
                        ),
                        id,
                    )
                )
            case "DefConstant":
                member = fpp_ast.ModuleMemberDefConstant(
                    translate_def_constant(data, id)
                )
            case "DefEnum":
                member = fpp_ast.ModuleMemberDefEnum(translate_def_enum(data, id))
            case "DefInterface":
                member = fpp_ast.ModuleMemberDefInterface(
                    AstNode.create_with_id(
                        fpp_ast.DefInterface(
                            data["name"], translate_interface_members(data["members"])
                        ),
                        id,
                    )
                )
            case "DefModule":
                member = fpp_ast.ModuleMemberDefModule(
                    AstNode.create_with_id(
                        fpp_ast.DefModule(
                            data["name"], translate_module_members(data["members"])
                        ),
                        id,
                    )
                )
            case "DefPort":
                member = fpp_ast.ModuleMemberDefPort(
                    AstNode.create_with_id(
                        fpp_ast.DefPort(
                            data["name"],
                            translate_formal_params(data["params"]),
                            translate_optional(data["returnType"], translate_type_name),
                        ),
                        id,
                    )
                )
            case "DefStateMachine":
                member = fpp_ast.ModuleMemberDefStateMachine(
                    translate_state_machine(data, id)
                )
            case "DefStruct":
                member = fpp_ast.ModuleMemberDefStruct(translate_def_struct(data, id))
            case "DefTopology":
                member = fpp_ast.ModuleMemberDefTopology(
                    AstNode.create_with_id(
                        fpp_ast.DefTopology(
                            data["name"], translate_topology_members(data["members"])
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
                            translate_qual_ident(data["symbol"]),
                            translate_string(data["file"]),
                        ),
                        id,
                    )
                )
            case _:
                raise InvalidFppToJsonField(m_key)
        members.append(fpp_ast.ModuleMember(annotate(m[0], member, m[2])))
    return members


def translate_state_machine_members(
    d: Dict[str, List],
) -> List[fpp_ast.StateMachineMember]:
    members = []
    if d.get("Some"):
        for l in d["Some"]:
            for k, v in l[1].items():
                data, id = read_ast_node(v["node"])
                member: Optional[fpp_ast.StateMachineMemberNode] = None
                match k:
                    case "DefAction":
                        member = fpp_ast.StateMachineMemberDefAction(
                            AstNode.create_with_id(
                                fpp_ast.DefAction(
                                    data["name"],
                                    translate_optional(
                                        data["typeName"], translate_type_name
                                    ),
                                ),
                                id,
                            )
                        )
                    case "DefChoice":
                        member = fpp_ast.StateMachineMemberDefChoice(
                            AstNode.create_with_id(
                                fpp_ast.DefChoice(
                                    data["name"],
                                    translate_ident(data["guard"]),
                                    translate_transition_expr(data["ifTransition"]),
                                    translate_transition_expr(data["elseTransition"]),
                                ),
                                id,
                            )
                        )
                    case "DefGuard":
                        member = fpp_ast.StateMachineMemberDefGuard(
                            AstNode.create_with_id(
                                fpp_ast.DefGuard(
                                    data["name"],
                                    translate_optional(
                                        data["typeName"], translate_type_name
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
                                    translate_optional(
                                        data["typeName"], translate_type_name
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
                                    translate_state_members(data["members"]),
                                ),
                                id,
                            )
                        )
                    case "SpecInitialTransition":
                        member = fpp_ast.StateMachineMemberSpecInitialTransition(
                            AstNode.create_with_id(
                                fpp_ast.SpecInitialTransition(
                                    translate_transition_expr(data["transition"])
                                ),
                                id,
                            )
                        )
                    case _:
                        raise InvalidFppToJsonField(k)
                members.append(fpp_ast.StateMachineMember(annotate(l[0], member, l[2])))
    return members


def translate_trans_unit_list(l: List) -> List[fpp_ast.TransUnit]:
    trans_units = []
    for tu in l:
        trans_unit_members = translate_module_members(tu["members"])
        trans_units.append(fpp_ast.TransUnit(trans_unit_members))
    return trans_units


def translate_ast_json(file: str) -> List[fpp_ast.TransUnit]:
    if not os.path.exists(file):
        raise FileNotFoundError(f'File "{file}" not found')
    with open(file, "r") as f:
        data: Dict = json.load(f)
        return translate_trans_unit_list(data["ast"])
