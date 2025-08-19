from fpp_locations import Locations, Location
import json
from typing import Dict, List, Callable, Any
import os
from fpp_ast import *
from fpp_ast_node import T, AstId
from pathlib import Path
from error import NotSupportedInFppToJsonException, InvalidFppToJsonField


def read_ast_node(a_node: dict) -> Tuple[dict, AstId]:
    return a_node["AstNode"]["data"], a_node["AstNode"]["id"]


def translate_string(d: dict) -> AstNode[str]:
    data, id = read_ast_node(d)
    return AstNode.create_with_id(data, id)


def translate_ident(d: dict) -> AstNode[Ident]:
    data, id = read_ast_node(d)
    return AstNode.create_with_id(Ident(data), id)


def translate_qual_ident(d: dict) -> AstNode[QualIdent]:
    data, id = read_ast_node(d)
    if data.get("Unqualified"):
        return AstNode.create_with_id(Unqualified(data["Unqualified"]["name"]), id)
    elif data.get("Qualified"):
        qualified = data["Qualified"]
        qualifier_dict = qualified["qualifier"]
        return AstNode.create_with_id(
            Qualified(
                translate_qual_ident(qualifier_dict), translate_ident(qualified["name"])
            ),
            id,
        )
    # TODO: raise error


def translate_formal_params(params_list: List) -> List[Annotated[FormalParam]]:
    params = []
    for p in params_list:
        node = p[1]
        data, id = read_ast_node(node)
        name = data["name"]
        kind = FormalParamKind.REF
        if "Value" in data["kind"]:
            kind = FormalParamKind.VALUE
        type_name_node = translate_type_name(data["typeName"])
        formal_param = FormalParam(kind, name, type_name_node)
        param_ast_node = AstNode.create_with_id(formal_param, id)
        params.append(annotate(p[0], param_ast_node, p[2]))
    return params


def translate_type_name(tn: dict) -> AstNode[TypeName]:
    data, id = read_ast_node(tn)
    if "TypeNameFloat" in data:
        name = list(data["TypeNameFloat"]["name"].keys())[0]
        return AstNode.create_with_id(TypeNameFloat(name), id)
    elif "TypeNameInt" in data:
        name = list(data["TypeNameInt"]["name"].keys())[0]
        return AstNode.create_with_id(TypeNameInt(name), id)
    elif "TypeNameQualIdent" in data:
        return AstNode.create_with_id(
            TypeNameQualIdent(translate_qual_ident(data["TypeNameQualIdent"]["name"])),
            id,
        )
    elif "TypeNameBool" in data:
        return AstNode.create_with_id(TypeNameBool(), id)
    elif "TypeNameString" in data:
        return AstNode.create_with_id(TypeNameString(None), id)
    else:
        raise Exception(f"Invalid type name dictionary {data}")


def translate_binop(d: dict) -> Binop:
    if "Add" in d:
        return Binop.ADD
    elif "Sub" in d:
        return Binop.SUB
    elif "Mul" in d:
        return Binop.MUL
    elif "Div" in d:
        return Binop.DIV
    else:
        raise Exception(f"Invalid Binop JSON {d}")


def translate_expr(expr_dict: dict) -> AstNode[Expr]:
    data, id = read_ast_node(expr_dict)
    if "ExprArray" in data:
        elts = []
        for e in data["ExprArray"]["elts"]:
            elts.append(translate_expr(e))
        return AstNode.create_with_id(ExprArray(elts), id)
    elif "ExprBinop" in data:
        return AstNode.create_with_id(
            ExprBinop(
                translate_expr(data["ExprBinop"]["e1"]),
                translate_binop(data["ExprBinop"]["op"]),
                translate_expr(data["ExprBinop"]["e2"]),
            ),
            id,
        )
    elif "ExprDot" in data:
        return AstNode.create_with_id(
            ExprDot(
                translate_expr(data["ExprDot"]["e"]),
                translate_ident(data["ExprDot"]["id"]),
            ),
            id,
        )
    elif "ExprIdent" in data:
        return AstNode.create_with_id(ExprIdent(data["ExprIdent"]["value"]), id)
    elif "ExprLiteralBool" in data:
        return AstNode.create_with_id(
            ExprLiteralBool(data["ExprLiteralBool"]["value"]), id
        )
    elif "ExprLiteralInt" in data:
        return AstNode.create_with_id(
            ExprLiteralInt(data["ExprLiteralInt"]["value"]), id
        )
    elif "ExprLiteralFloat" in data:
        return AstNode.create_with_id(
            ExprLiteralFloat(data["ExprLiteralFloat"]["value"]), id
        )
    elif "ExprLiteralString" in data:
        return AstNode.create_with_id(
            ExprLiteralString(data["ExprLiteralString"]["value"]), id
        )
    elif "ExprParen" in data:
        raise Exception("Translation for ExprParen not implemented.")
    elif "ExprStruct" in data:
        members = []
        for m in data["ExprStruct"]["members"]:
            members.append(
                AstNode.create_with_id(
                    StructMember(
                        m["AstNode"]["data"]["name"],
                        translate_expr(m["AstNode"]["data"]["value"]),
                    ),
                    m["AstNode"]["id"],
                )
            )
        return AstNode.create_with_id(ExprStruct(members), id)
    elif "ExprUnop" in data:
        return AstNode.create_with_id(
            ExprUnop(Unop.MINUS, translate_expr(data["ExprUnop"]["e"])), id
        )
    else:
        raise Exception(f"Invalid expression dictionary {expr_dict}")


def translate_transition_expr(te: dict) -> AstNode[TransitionExpr]:
    data, _ = read_ast_node(te)
    return TransitionExpr(
        translate_actions(data["actions"]), translate_qual_ident(data["target"])
    )


def translate_transition_or_do(t: dict) -> AstNode[TransitionOrDo]:
    if "Transition" in t:
        return Transition(
            AstNode.create_with_id(
                translate_transition_expr(t["Transition"]["transition"]),
                t["Transition"]["transition"]["AstNode"]["id"],
            )
        )
    elif "Do" in t:
        return Do(translate_actions(t["Do"]["actions"]))
    else:
        raise Exception(f"Invalid Transition or Do JSON {t}")


def translate_actions(l: List) -> List[AstNode[Ident]]:
    actions = []
    for a in l:
        actions.append(translate_ident(a))
    return actions


def annotate(l1: List[str], d: T, l2: List[str]) -> Annotated:
    return [(l1, d, l2)]


def translate_limit_kind(d: dict) -> AstNode[LimitKind]:
    data, id = read_ast_node(d)
    limit_kind = LimitKind.RED
    if "Yellow" in data:
        limit_kind = LimitKind.YELLOW
    elif "Orange" in data:
        limit_kind = LimitKind.ORANGE
    return AstNode.create_with_id(limit_kind, id)


def translate_spec_tlm_channel_update(d: dict) -> SpecTlmChannelUpdate:
    if "Always" in d:
        return SpecTlmChannelUpdate.ALWAYS
    elif "OnChange" in d:
        return SpecTlmChannelUpdate.ON_CHANGE
    else:
        raise InvalidFppToJsonField("")


def translate_limits(l: List) -> List[Limit]:
    limits = []
    for e in l:
        limits.append((translate_limit_kind(e[0]), translate_expr(e[1])))
    return limits


def translate_spec_command_kind(d: dict) -> SpecCommandKind:
    if "Async" in d:
        return SpecCommandKind.ASYNC
    elif "Sync" in d:
        return SpecCommandKind.SYNC
    else:
        return SpecCommandKind.GUARDED


def translate_severity(d: dict) -> SpecEventSeverity:
    if "ActivityHigh" in d:
        return SpecEventSeverity.ACTIVITY_HIGH
    elif "ActivityLow" in d:
        return SpecEventSeverity.ACTIVITY_LOW
    elif "Command" in d:
        return SpecEventSeverity.COMMAND
    elif "Diagnostic" in d:
        return SpecEventSeverity.DIAGNOSTIC
    elif "Fatal" in d:
        return SpecEventSeverity.FATAL
    elif "WarningHigh" in d:
        return SpecEventSeverity.WARNING_HIGH
    else:
        return SpecEventSeverity.WARNING_LOW

def translate_def_abs_type(data: dict, id: AstId) -> AstNode[DefAbsType]:
    return AstNode.create_with_id(DefAbsType(data["name"]), id)

def translate_def_alias_type(data: dict, id: AstId) -> AstNode[DefAliasType]:
    return AstNode.create_with_id(
        DefAliasType(data["name"], translate_type_name(data["typeName"])),
        id,
    )

def translate_def_array(data: dict, id: AstId) -> AstNode[DefArray]:
    return AstNode.create_with_id(
        DefArray(
            data["name"],
            translate_expr(data["size"]),
            translate_type_name(data["eltType"]),
            translate_optional(data["default"], translate_expr),
            translate_optional(data["format"], translate_string),
        ),
        id
    )

def translate_def_constant(data: dict, id: AstId) -> AstNode[DefConstant]:
    return AstNode.create_with_id(
        DefConstant(data["name"], translate_expr(data["value"])),
        id
    )

def translate_def_enum(data: dict, id: AstId) -> AstNode[DefEnum]:
    constants = []
    for c in data["constants"]:
        const = c[1]
        const_data, const_id = read_ast_node(const)
        node = AstNode.create_with_id(
            DefEnumConstant(
                const_data["name"],
                translate_optional(const_data["value"], translate_expr),
            ),
            const_id,
        )
    constants.append(annotate(c[0], node, c[2]))
    return AstNode.create_with_id(
        DefEnum(
            data["name"],
            translate_optional(data["typeName"], translate_type_name),
            constants,
        ),
        id,
    )

def translate_def_struct(data: dict, id: AstId) -> AstNode[DefStruct]:
    struct_members = []
    for m in data["members"]:
        member_data, member_id = read_ast_node(m[1])
        node = AstNode.create_with_id(
            StructTypeMember(
                member_data["name"],
                translate_optional(member_data["size"], translate_expr),
                translate_type_name(member_data["typeName"]),
                translate_optional(member_data["format"], translate_string),
            ),
            member_id,
        )
        struct_members.append(annotate(m[0], node, m[2]))
    return AstNode.create_with_id(
        DefStruct(
            data["name"],
            struct_members,
            translate_optional(data["default"], translate_expr),
        ),
        id,
    )

def translate_component_members(l: list) -> List[ComponentMember]:
    members = []
    for m in l:
        m_key = list(m[1].keys())[0]
        member = None
        node = m[1][m_key]
        data, id = read_ast_node(node["node"])
        match m_key:
            case "DefAbsType":
                member = ComponentMemberDefAbsType(translate_def_abs_type(data, id))
            case "DefAliasType":
                member = ComponentMemberDefAliasType(translate_def_alias_type(data, id))
            case "DefArray":
                member = ComponentMemberDefArray(translate_def_array(data, id))
            case "DefConstant":
                member = ComponentMemberDefConstant(translate_def_constant(data, id))
            case "DefEnum":
                member = ComponentMemberDefEnum(translate_def_enum(data, id))
            case "SpecCommand":
                member = ComponentMemberSpecCommand(
                    AstNode.create_with_id(
                        SpecCommand(
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
            case "DefStruct":
                member = ComponentMemberDefStruct(translate_def_struct(data, id))
            case "SpecTlmChannel":
                member = ComponentMemberSpecTlmChannel(
                    AstNode.create_with_id(
                        SpecTlmChannel(
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
                member = ComponentMemberSpecEvent(
                    AstNode.create_with_id(
                        SpecEvent(
                            data["name"],
                            translate_formal_params(data["params"]),
                            translate_severity(data["severity"]),
                        ),
                        id,
                    )
                )
            case "SpecRecord":
                member = ComponentMemberSpecRecord(
                    AstNode.create_with_id(
                        SpecRecord(
                            data["name"],
                            translate_type_name(data["recordType"]),
                            data["isArray"],
                            translate_optional(data["id"], translate_expr),
                        ),
                        id,
                    )
                )
            case "SpecContainer":
                member = ComponentMemberSpecContainer(
                    AstNode.create_with_id(
                        SpecContainer(
                            data["name"],
                            translate_optional(data["id"], translate_expr),
                            translate_optional(data["defaultPriority"], translate_expr),
                        ),
                        id,
                    )
                )
            case "SpecParam":
                member = ComponentMemberSpecParam(
                    AstNode.create_with_id(
                        SpecParam(
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
                member = ComponentMemberSpecPortMatching(
                    AstNode.create_with_id(
                        SpecPortMatching(
                            translate_ident(data["port1"]),
                            translate_ident(data["port2"]),
                        ),
                        id,
                    )
                )
            case "SpecInternalPort":
                member = ComponentMemberSpecInternalPort(
                    AstNode.create_with_id(
                        SpecInternalPort(
                            data["name"],
                            translate_formal_params(data["params"]),
                            translate_optional(data["priority"], translate_expr),
                            translate_optional(data["queueFull"], translate_queue_full),
                        ),
                        id,
                    )
                )
            case "SpecPortInstance":
                member = ComponentMemberSpecPortInstance(
                    AstNode.create_with_id(translate_port_instance(node["node"]), id)
                )
            case "SpecImportInterface":
                member = ComponentMemberSpecImportInterface(
                    AstNode.create_with_id(
                        SpecImport(translate_qual_ident(data["sym"])), id
                    )
                )
            case _:
                raise InvalidFppToJsonField(m_key)
        members.append(annotate(m[0], member, m[2]))
    return members


def translate_state_members(l: List) -> List[StateMember]:
    members = []
    for m in l:
        m_dict: dict = m[1]
        m_key = list(m_dict.keys())[0]
        data, id = read_ast_node(m_dict[m_key]["node"])
        member = None
        match m_key:
            case "DefChoice":
                member = StateMemberDefChoice(
                    AstNode.create_with_id(
                        DefChoice(
                            data["name"],
                            translate_ident(data["guard"]),
                            translate_transition_expr(data["ifTransition"]),
                            translate_transition_expr(data["elseTransition"]),
                        ),
                        id,
                    )
                )
            case "DefState":
                member = StateMemberDefState(
                    AstNode.create_with_id(
                        DefState(
                            data["name"], translate_state_members(data["members"])
                        ),
                        id,
                    )
                )
            case "SpecStateEntry":
                member = StateMemberSpecStateEntry(
                    AstNode.create_with_id(
                        SpecStateEntry(translate_actions(data["actions"])), id
                    )
                )
            case "SpecStateExit":
                member = StateMemberSpecStateExit(
                    AstNode.create_with_id(
                        SpecStateExit(translate_actions(data["actions"])), id
                    )
                )
            case "SpecInitialTransition":
                member = StateMemberSpecInitialTransition(
                    AstNode.create_with_id(
                        SpecInitialTransition(
                            translate_transition_expr(data["transition"])
                        ),
                        id,
                    )
                )
            case "SpecStateTransition":
                signal = translate_ident(data["signal"])
                transition_or_do = translate_transition_or_do(data["transitionOrDo"])
                member = StateMemberSpecStateTransition(
                    AstNode.create_with_id(
                        SpecStateTransition(
                            signal,
                            translate_optional(data["guard"], translate_ident),
                            transition_or_do,
                        ),
                        id,
                    )
                )
            case _:
                raise InvalidFppToJsonField(m_key)
        members.append(annotate(m[0], member, m[2]))
    return members


def translate_port_instance_identifier(d: dict) -> PortInstanceIdentifier:
    data, _ = read_ast_node(d)
    return PortInstanceIdentifier(
        translate_qual_ident(data["componentInstance"]),
        translate_ident(data["portName"]),
    )


def translate_pattern_kind(d: dict) -> PatternKind:
    kind = list(d.keys())[0]
    match kind:
        case "Command":
            return PatternKind.COMMAND
        case "Event":
            return PatternKind.EVENT
        case "Health":
            return PatternKind.HEALTH
        case "Param":
            return PatternKind.PARAM
        case "Telemetry":
            return PatternKind.TELEMETRY
        case "TextEvent":
            return PatternKind.TEXT_EVENT
        case "Time":
            return PatternKind.TIME
        case _:
            raise InvalidFppToJsonField(kind)


def translate_tlm_channel_identifier(d: dict) -> AstNode[TlmChannelIdentifier]:
    data, id = read_ast_node(d)
    return AstNode.create_with_id(
        TlmChannelIdentifier(
            translate_qual_ident(data["componentInstance"]),
            translate_ident(data["channelName"]),
        ),
        id,
    )


def translate_special_input_kind(d: dict) -> SpecialInputKind:
    if "Async" in d:
        return SpecialInputKind.ASYNC
    elif "Sync" in d:
        return SpecialInputKind.SYNC
    elif "Guarded" in d:
        return SpecialInputKind.GUARDED
    else:
        raise Exception(f"Invalid special input kind dictionary {d}")


def translate_special_kind(d: dict) -> SpecialKind:
    if "CommandRecv" in d:
        return SpecialKind.COMMAND_RECV
    elif "CommandReg" in d:
        return SpecialKind.COMMAND_REG
    elif "CommandResp" in d:
        return SpecialKind.COMMAND_RESP
    elif "Event" in d:
        return SpecialKind.EVENT
    elif "ParamGet" in d:
        return SpecialKind.PARAM_GET
    elif "ParamSet" in d:
        return SpecialKind.PARAM_SET
    elif "ProductGet" in d:
        return SpecialKind.PRODUCT_GET
    elif "ProductRecv" in d:
        return SpecialKind.PRODUCT_RECV
    elif "ProductRequest" in d:
        return SpecialKind.PRODUCT_REQUEST
    elif "ProductSend" in d:
        return SpecialKind.PRODUCT_SEND
    elif "Telemetry" in d:
        return SpecialKind.TELEMETRY
    elif "TextEvent" in d:
        return SpecialKind.TEXT_EVENT
    elif "TimeGet" in d:
        return SpecialKind.TIME_GET
    else:
        raise Exception(f"Invalid special kind dictionary {d}")


def translate_general_kind(d: dict) -> GeneralKind:
    if "AsyncInput" in d:
        return GeneralKind.ASYNC_INPUT
    elif "GuardedInput" in d:
        return GeneralKind.GUARDED_INPUT
    elif "Output" in d:
        return GeneralKind.OUTPUT
    elif "SyncInput" in d:
        return GeneralKind.SYNC_INPUT
    else:
        raise Exception(f"Invalid general kind dictionary {d}")


def translate_optional(d: dict, func: Callable[[Any], T]) -> Optional[T]:
    if "Some" in d:
        return func(d["Some"])
    else:
        return None


def translate_queue_full(d: dict) -> QueueFull:
    if "Assert" in d:
        return QueueFull.ASSERT
    elif "Block" in d:
        return QueueFull.BLOCK
    elif "Drop" in d:
        return QueueFull.DROP
    else:
        return QueueFull.HOOK


def translate_port_instance(d: dict) -> SpecPortInstance:
    if "Special" in d["AstNode"]["data"]:
        special_node = d["AstNode"]["data"]["Special"]
        return Special(
            translate_optional(special_node["inputKind"], translate_special_input_kind),
            translate_special_kind(special_node["kind"]),
            special_node["name"],
            translate_optional(special_node["priority"], translate_expr),
            translate_optional(special_node["queueFull"], translate_queue_full),
        )
    elif "General" in d["AstNode"]["data"]:
        general_node = d["AstNode"]["data"]["General"]
        return General(
            translate_general_kind(general_node["kind"]),
            general_node["name"],
            translate_optional(general_node["size"], translate_expr),
            translate_optional(general_node["port"], translate_qual_ident),
            translate_optional(general_node["priority"], translate_expr),
            translate_optional(general_node["queueFull"], translate_queue_full),
        )
    else:
        raise Exception(f"Invalid port instance dictionary {d}")


def translate_init_specs(l: list) -> List[Annotated[AstNode[SpecInit]]]:
    specs = []
    for e in l:
        spec_node = e[1]
        data = spec_node["AstNode"]["data"]
        id = spec_node["AstNode"]["id"]
        spec = AstNode.create_with_id(
            SpecInit(translate_expr(data["phase"]), data["code"]), id
        )
        specs.append(annotate(e[0], spec, e[2]))
    return specs


def translate_interface_members(l: List) -> List[InterfaceMember]:
    members = []
    for m in l:
        m_dict: dict = m["node"][1]
        m_key = list(m_dict.keys())[0]
        id = m_dict[m_key]["node"]["AstNode"]["id"]
        data: dict = m_dict[m_key]["node"]["AstNode"]["data"]
        member = None
        match m_key:
            case "SpecPortInstance":
                member = InterfaceMemberSpecPortInstance(
                    AstNode.create_with_id(
                        translate_port_instance(m_dict[m_key]["node"]), id
                    )
                )
            case "SpecImportInterface":
                member = InterfaceMemberSpecImportInterface(
                    AstNode.create_with_id(
                        SpecImport(translate_qual_ident(data["sym"])), id
                    )
                )
            case _:
                raise InvalidFppToJsonField(m_key)
        members.append(annotate(m["node"][0], member, m["node"][2]))
    return members


def translate_tlm_packet_set_members(d: dict) -> List[TlmPacketSetMember]:
    members = []
    for member in d:
        node = member["node"][1]
        if "SpecTlmPacket" in node:
            spec_tlm_pkt_data, spec_tlm_pkt_id = read_ast_node(
                node["SpecTlmPacket"]["node"]
            )
            tlm_pkt_members = []
            for m in spec_tlm_pkt_data["members"]:
                if "TlmChannelIdentifier" in m:
                    chan_ident_node = m["TlmChannelIdentifier"]["node"]
                    tlm_pkt_members.append(
                        TlmPacketMemberTlmChannelIdentifier(
                            AstNode.create_with_id(
                                translate_tlm_channel_identifier(chan_ident_node),
                                chan_ident_node["AstNode"]["id"],
                            )
                        )
                    )
            pkt = TlmPacketSetMemberSpecTlmPacket(
                AstNode.create_with_id(
                    SpecTlmPacket(
                        spec_tlm_pkt_data["name"],
                        translate_optional(spec_tlm_pkt_data["id"], translate_expr),
                        spec_tlm_pkt_data["group"],
                        tlm_pkt_members,
                    ),
                    spec_tlm_pkt_id,
                )
            )
            members.append(annotate(member["node"][0], pkt, member["node"][2]))
        elif "SpecInclude" in node:
            raise NotSupportedInFppToJsonException("SpecInclude")


def translate_topology_members(l: List) -> List[TopologyMember]:
    members = []
    for m in l:
        m_dict: dict = m[1]
        m_key = list(m_dict.keys())[0]
        id = m_dict[m_key]["node"]["AstNode"]["id"]
        data: dict = m_dict[m_key]["node"]["AstNode"]["data"]
        member = None
        match m_key:
            case "SpecCompInstance":
                visibility = Visibility.PRIVATE
                if "Public" in data["visibility"]:
                    visibility = Visibility.PUBLIC
                member = TopologyMemberSpecCompInstance(
                    AstNode.create_with_id(
                        SpecCompInstance(
                            visibility, translate_qual_ident(data["instance"])
                        ),
                        id,
                    )
                )
            case "SpecConnectionGraph":
                if "Direct" in data:
                    connections = []
                    for c in data["Direct"]["connections"]:
                        from_index = None
                        if c["fromIndex"] != "None":
                            from_index = translate_expr(c["fromIndex"]["Some"])
                        to_index = None
                        if c["toIndex"] != "None":
                            to_index = translate_expr(c["toIndex"]["Some"])
                        connections.append(
                            Connection(
                                c["isUnmatched"],
                                translate_port_instance_identifier(c["fromPort"]),
                                from_index,
                                translate_port_instance_identifier(c["toPort"]),
                                to_index,
                            )
                        )
                    connection_graph = Direct(data["Direct"]["name"], connections)
                elif "Pattern" in data:
                    targets = []
                    for t in data["Pattern"]["targets"]:
                        targets.append(translate_qual_ident(t))
                    connection_graph = Pattern(
                        translate_pattern_kind(data["Pattern"]["kind"]),
                        translate_qual_ident(data["Pattern"]["source"]),
                        targets,
                    )
                else:
                    raise Exception(f"Invalid SpecConnectionGraph dictionary {data}")

                member = TopologyMemberSpecConnectionGraph(
                    AstNode.create_with_id(connection_graph, id)
                )
            case "SpecInclude":
                raise Exception("SpecInclude translation not implemented")
            case "SpecTlmPacketSet":
                omitted = []
                for o in data["omitted"]:
                    omitted.append(translate_tlm_channel_identifier(o))
                member = TopologyMemberSpecTlmPacketSet(
                    AstNode.create_with_id(
                        SpecTlmPacketSet(
                            data["name"],
                            translate_tlm_packet_set_members(data["members"]),
                            omitted,
                        ),
                        id,
                    )
                )
            case "SpecTopImport":
                member = TopologyMemberSpecTopImport(
                    AstNode.create_with_id(
                        SpecImport(translate_qual_ident(data["sym"])), id
                    )
                )
            case _:
                raise InvalidFppToJsonField(m_key)
        members.append(member)
    return members


def translate_module_members(l: List) -> List[ModuleMember]:
    members = []
    for m in l:
        for k, v in m[1].items():
            data, id = read_ast_node(v["node"])
            name = data["name"]
            member = None
            match k:
                case "DefAbsType":
                    member = ModuleMemberDefAbsType(translate_def_abs_type(data, id))
                case "DefAliasType":
                    member = ModuleMemberDefAliasType(translate_def_alias_type(data, id))
                case "DefArray":
                    member = ModuleMemberDefArray(translate_def_array(data, id))
                case "DefComponent":
                    if "Active" in data["kind"]:
                        kind = ComponentKind.ACTIVE
                    elif "Passive" in data["kind"]:
                        kind = ComponentKind.PASSIVE
                    elif "Queued" in data["kind"]:
                        kind = ComponentKind.QUEUED
                    else:
                        raise Exception(f"Invalid component kind dictionary {data}")
                    member = ModuleMemberDefComponent(
                        AstNode.create_with_id(
                            DefComponent(
                                kind,
                                name,
                                translate_component_members(data["members"]),
                            ),
                            id,
                        )
                    )
                case "DefComponentInstance":
                    member = ModuleMemberDefComponentInstance(
                        AstNode.create_with_id(
                            DefComponentInstance(
                                name,
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
                    member = ModuleMemberDefConstant(translate_def_constant(data, id))
                case "DefEnum":
                    member = ModuleMemberDefEnum(translate_def_enum(data, id))
                case "DefInterface":
                    member = ModuleMemberDefInterface(
                        AstNode.create_with_id(
                            DefInterface(
                                name, translate_interface_members(data["members"])
                            ),
                            id,
                        )
                    )
                case "DefModule":
                    member = ModuleMemberDefModule(
                        AstNode.create_with_id(
                            DefModule(name, translate_module_members(data["members"])),
                            id,
                        )
                    )
                case "DefPort":
                    params = translate_formal_params(data["params"])
                    member = ModuleMemberDefPort(
                        AstNode.create_with_id(
                            DefPort(
                                name,
                                params,
                                translate_optional(
                                    data["returnType"], translate_type_name
                                ),
                            ),
                            id,
                        )
                    )
                case "DefStateMachine":
                    member = ModuleMemberDefStateMachine(
                        AstNode.create_with_id(
                            DefStateMachine(
                                name, translate_state_machine_members(data["members"])
                            ),
                            id,
                        )
                    )
                case "DefStruct":
                    member = ModuleMemberDefStruct(translate_def_struct(data, id))
                case "DefTopology":
                    member = ModuleMemberDefTopology(
                        AstNode.create_with_id(
                            DefTopology(
                                name, translate_topology_members(data["members"])
                            ),
                            id,
                        )
                    )
                case "SpecInclude":
                    raise NotSupportedInFppToJsonException(k)
                case "SpecLoc":
                    raise NotSupportedInFppToJsonException(k)
                case _:
                    raise InvalidFppToJsonField(k)
            members.append(annotate(m[0], member, m[2]))
    return members


def translate_state_machine_members(d: Dict[str, List]) -> List[StateMachineMember]:
    members = []
    if d.get("Some"):
        for l in d["Some"]:
            for k, v in l[1].items():
                data, id = read_ast_node(v["node"])
                member = None
                match k:
                    case "DefAction":
                        member = StateMachineMemberDefAction(
                            AstNode.create_with_id(
                                DefAction(
                                    data["name"],
                                    translate_optional(
                                        data["typeName"], translate_type_name
                                    ),
                                ),
                                id,
                            )
                        )
                    case "DefChoice":
                        member = StateMachineMemberDefChoice(
                            AstNode.create_with_id(
                                DefChoice(
                                    data["name"],
                                    translate_ident(data["guard"]),
                                    translate_transition_expr(data["ifTransition"]),
                                    translate_transition_expr(data["elseTransition"]),
                                ),
                                id,
                            )
                        )
                    case "DefGuard":
                        member = StateMachineMemberDefGuard(
                            AstNode.create_with_id(
                                DefGuard(
                                    data["name"],
                                    translate_optional(
                                        data["typeName"], translate_type_name
                                    ),
                                ),
                                id,
                            )
                        )
                    case "DefSignal":
                        member = StateMachineMemberDefSignal(
                            AstNode.create_with_id(
                                DefSignal(
                                    data["name"],
                                    translate_optional(
                                        data["typeName"], translate_type_name
                                    ),
                                ),
                                id,
                            )
                        )
                    case "DefState":
                        member = StateMachineMemberDefState(
                            AstNode.create_with_id(
                                DefState(
                                    data["name"],
                                    translate_state_members(data["members"]),
                                ),
                                id,
                            )
                        )
                    case "SpecInitialTransition":
                        member = StateMachineMemberDefSpecInitialTransition(
                            AstNode.create_with_id(
                                SpecInitialTransition(
                                    translate_transition_expr(data["transition"])
                                ),
                                id,
                            )
                        )
                    case _:
                        raise InvalidFppToJsonField(k)
                members.append(annotate(l[0], member, l[2]))
    return members


def translate_ast_json(file: str):
    if not os.path.exists(file):
        raise FileNotFoundError(f'File "{file}" not found')
    with open(file, "r") as f:
        data: List[Dict] = json.load(f)
        for d in data:
            if isinstance(d, dict):
                for k, v in d.items():
                    m = translate_module_members(v)
                    print(m)


def translate_location_map_json(file: str) -> dict[AstId, Location]:
    if not os.path.exists(file):
        raise FileNotFoundError(f'File "{file}" not found')
    with open(file, "r") as f:
        data: Dict[str, dict] = json.load(f)
        for k, v in data.items():
            try:
                Locations.put(
                    int(k), Location(Path(v["file"]), v["pos"], v["includingLoc"])
                )
            except KeyError as e:
                raise KeyError(f"Location map for ID {k} is missing required field {e}")
    return Locations.get_map()
