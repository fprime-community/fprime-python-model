from fpp_locations import Locations, Location
import json
from typing import Dict, List, Callable, Any
import os
from fpp_ast import *
from fpp_ast_node import AstId
from pathlib import Path

def translate_string(d: dict) -> AstNode[str]:
    return AstNode.create_with_id(d["AstNode"]["data"], d["AstNode"]["id"])

def translate_ident(d: dict) -> AstNode[Ident]:
    return AstNode.create_with_id(
        Ident(d["AstNode"]["data"]), 
        d["AstNode"]["id"]
    )

def translate_qual_ident(d: dict) -> AstNode[QualIdent]:
    if d["AstNode"]["data"].get("Unqualified"):
        return AstNode.create_with_id(
            Unqualified(d["AstNode"]["data"]["Unqualified"]["name"]), d["AstNode"]["id"]
        )
    elif d["AstNode"]["data"].get("Qualified"):
        qualified = d["AstNode"]["data"]["Qualified"]
        qualifier_dict = qualified["qualifier"]
        return AstNode.create_with_id(
            Qualified(
                translate_qual_ident(qualifier_dict), 
                translate_ident(qualified["name"])
            ),
            d["AstNode"]["id"],
        )
    # TODO: raise error
    
def translate_formal_params(params_list: List) -> List[Annotated[FormalParam]]:
    params = []
    for p in params_list:
        node = p[1]
        id = node["AstNode"]["id"]
        data = node["AstNode"]["data"]
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
    id = tn["AstNode"]["id"]
    data: dict = tn["AstNode"]["data"]
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
        raise Exception(f"Invalid Binop dictionary {d}")

def translate_expr(expr_dict: dict) -> AstNode[Expr]:
    data = expr_dict["AstNode"]["data"]
    id = expr_dict["AstNode"]["id"]
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
                translate_expr(data["ExprBinop"]["e2"])
            ),
            id
        )
    elif "ExprDot" in data:
        return AstNode.create_with_id(
            ExprDot(
                translate_expr(data["ExprDot"]["e"]),
                translate_ident(data["ExprDot"]["id"])
            ),
            id
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
            ExprUnop(
                Unop.MINUS,
                translate_expr(data["ExprUnop"]["e"])
            ),
            id
        )
    else:
        raise Exception(f"Invalid expression dictionary {expr_dict}")

def translate_transition_expr(te: dict) -> AstNode[TransitionExpr]:
    data = te["AstNode"]["data"]
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
        raise Exception(f"Invalid transition or do dictionary {t}")

def translate_actions(l: List) -> List[AstNode[Ident]]:
    actions = []
    for a in l:
        actions.append(translate_ident(a))
    return actions

def annotate(l1: List[str], d: T, l2: List[str]) -> Annotated:
    return [(l1, d, l2)]

def translate_component_members(l: list) -> List[ComponentMember]:
    members = []
    for m in l:
        m_key = list(m[1].keys())[0]
        member = None
        node = m[1][m_key]
        id = node["node"]["AstNode"]["id"]
        match m_key:
            case "DefAbsType":
                name = node["node"]["AstNode"]["name"]
                member = ComponentMemberDefAbsType(AstNode.create_with_id(DefAbsType(name), id))
            case "DefAliasType":
                name = node["node"]["AstNode"]["data"]["name"]
                member = ComponentMemberDefAliasType(
                    AstNode.create_with_id(
                        DefAliasType(
                            name,
                            translate_type_name(
                                node["node"]["AstNode"]["data"]["typeName"]
                            ),
                        ),
                        id,
                    )
                )
            case "DefArray":
                name = node["node"]["AstNode"]["data"]["name"]
                data = node["node"]["AstNode"]["data"]
                default = None
                if data["default"] != "None":
                    default = translate_expr(data["default"]["Some"])
                format = None
                if data["format"] != "None":
                    format_node = data["format"]["Some"]["AstNode"]
                    format = AstNode.create_with_id(format_node["data"], format_node["id"])
                member = ComponentMemberDefArray(
                    AstNode.create_with_id(
                        DefArray(
                            name,
                            translate_expr(data["size"]),
                            translate_type_name(data["eltType"]),
                            default,
                            format,
                        ),
                        id,
                    )
                )
            case "DefConstant":
                name = node["node"]["AstNode"]["name"]
                member = ComponentMemberDefConstant(
                    AstNode.create_with_id(
                        DefConstant(
                            name,
                            translate_expr(node["node"]["AstNode"]["data"]["value"])
                        ),
                        id,
                    )
                )
            case "DefEnum":
                name = node["node"]["AstNode"]["data"]["name"]
                data = node["node"]["AstNode"]["data"]
                type_name = None
                if data["typeName"] != "None":
                    type_name = translate_type_name(data["typeName"]["Some"])
                constants = []
                for c in data["constants"]:
                    const = c[1]
                    value = None
                    if const["AstNode"]["data"]["value"] != "None":
                        value = translate_expr(const["AstNode"]["data"]["value"]["Some"])
                    node = AstNode.create_with_id(
                        DefEnumConstant(
                            const["AstNode"]["data"]["name"],
                            value
                        ),
                        const["AstNode"]["id"]
                    )
                    constants.append(annotate(c[0], node, c[2]))
                member = ComponentMemberDefEnum(
                    AstNode.create_with_id(
                        DefEnum(
                            name,
                            type_name,
                            constants
                        ),
                        id
                    )
                )
        if member:
            members.append(annotate(m[0], member, m[2]))
    return members

def translate_state_members(l: List) -> List[StateMember]:
    members = []
    for m in l:
        m_dict: dict = m[1]
        m_key = list(m_dict.keys())[0]
        id = m_dict[m_key]["node"]["AstNode"]["id"]
        data: dict = m_dict[m_key]["node"]["AstNode"]["data"]
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
                guard = None
                if "Some" in data["guard"]:
                    guard = translate_ident(data["guard"]["Some"])
                transition_or_do = translate_transition_or_do(data["transitionOrDo"])
                member = StateMemberSpecStateTransition(
                    AstNode.create_with_id(
                        SpecStateTransition(signal, guard, transition_or_do), id
                    )
                )
        if member:
            members.append(annotate(m[0], member, m[2]))
        else:
            raise Exception("Member not defined!")
    return members

def translate_port_instance_identifier(d: dict) -> PortInstanceIdentifier:
    return PortInstanceIdentifier(
        translate_qual_ident(d["AstNode"]["data"]["componentInstance"]),
        translate_ident(d["AstNode"]["data"]["portName"])
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
            raise (f"Invalid pattern kind dictionary {d}")

def translate_tlm_channel_identifier(d: dict) -> AstNode[TlmChannelIdentifier]:
    node = d["AstNode"]
    return AstNode.create_with_id(
        TlmChannelIdentifier(
            translate_qual_ident(node["data"]["componentInstance"]),
            translate_ident(node["data"]["channelName"])
        ),
        node["id"]
    )

def translate_tlm_packet_set_members(d: dict) -> List[TlmPacketSetMember]:
    members = []
    for member in d:
        node = member["node"][1]
        if "SpecTlmPacket" in node:
            spec_tlm_pkt = node["SpecTlmPacket"]["node"]
            id = None
            if "Some" in spec_tlm_pkt["AstNode"]["data"]["id"]:
                id = translate_expr(spec_tlm_pkt["AstNode"]["data"]["id"]["Some"])
            tlm_pkt_members = []
            for m in spec_tlm_pkt["AstNode"]["data"]["members"]:
                if "TlmChannelIdentifier" in m:
                    chan_ident_node = m["TlmChannelIdentifier"]["node"]
                    tlm_pkt_members.append(
                        TlmPacketMemberTlmChannelIdentifier(
                            AstNode.create_with_id(
                                translate_tlm_channel_identifier(chan_ident_node),
                                chan_ident_node["AstNode"]["id"]
                            )
                        )
                    )
            pkt = TlmPacketSetMemberSpecTlmPacket(
                AstNode.create_with_id(
                    SpecTlmPacket(
                        spec_tlm_pkt["AstNode"]["data"]["name"],
                        id,
                        spec_tlm_pkt["AstNode"]["data"]["group"],
                        tlm_pkt_members
                    ),
                    spec_tlm_pkt["AstNode"]["data"]["id"]
                )
            )
            members.append(annotate(member["node"][0], pkt, member["node"][2]))
        elif "SpecInclude" in node:
            raise Exception("SpecInclude translation not implemented")

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
                        SpecCompInstance(visibility, translate_qual_ident(data["instance"])),
                        id
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
                        connections.append(Connection(
                            c["isUnmatched"],
                            translate_port_instance_identifier(c["fromPort"]),
                            from_index,
                            translate_port_instance_identifier(c["toPort"]),
                            to_index

                        ))
                    connection_graph = Direct(data["Direct"]["name"], connections)
                elif "Pattern" in data:
                    targets = []
                    for t in data["Pattern"]["targets"]:
                        targets.append(translate_qual_ident(t))
                    connection_graph = Pattern(
                        translate_pattern_kind(data["Pattern"]["kind"]),
                        translate_qual_ident(data["Pattern"]["source"]),
                        targets
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
                            omitted
                        ),
                        id
                    )
                )
            case "SpecTopImport":
                member = TopologyMemberSpecTopImport(
                    AstNode.create_with_id(
                        SpecImport(translate_qual_ident(data["sym"])),
                        id
                    )
                )
        if member:
            members.append(member)
        else:
            raise Exception(f"Could not translate topology member {m_key}")
    return members

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

def translate_port_instance(d: dict) -> SpecPortInstance:
    if "Special" in d["AstNode"]["data"]:
        special_node = d["AstNode"]["data"]["Special"]       
        return Special(
            translate_optional(special_node["inputKind"], translate_special_input_kind),
            translate_special_kind(special_node["kind"]),
            special_node["name"],
            translate_optional(special_node["priority"], translate_expr),
            translate_optional(special_node["queueFull"], translate_expr)
        )
    elif "General" in d["AstNode"]["data"]:
        general_node = d["AstNode"]["data"]["General"]
        return General(
            translate_general_kind(general_node["kind"]),
            general_node["name"],
            translate_optional(general_node["size"], translate_expr),
            translate_optional(general_node["port"], translate_qual_ident),
            translate_optional(general_node["priority"], translate_expr), 
            translate_optional(general_node["queueFull"], translate_expr)
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
            SpecInit(translate_expr(data["phase"]), data["code"]),
            id
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
                        translate_port_instance(m_dict[m_key]["node"]),
                        id
                    )
                )
            case "SpecImportInterface":
                member = InterfaceMemberSpecImportInterface(
                    AstNode.create_with_id(
                        SpecImport(translate_qual_ident(data["sym"])),
                        id
                    )
                )
        if member:
            members.append(annotate(m["node"][0], member, m["node"][2]))
        else:
            raise Exception(f"Could not translate interface member {m_key}")
    return members

def translate_module_members(l: List) -> List[ModuleMember]:
    members = []
    for m in l:
        for k, v in m[1].items():
            id = v["node"]["AstNode"]["id"]
            name = v["node"]["AstNode"]["data"]["name"]
            member = None
            match k:
                case "DefAbsType":
                    member = ModuleMemberDefAbsType(AstNode.create_with_id(DefAbsType(name), id))
                case "DefAliasType":
                    member = ModuleMemberDefAliasType(
                        AstNode.create_with_id(
                            DefAliasType(
                                name,
                                translate_type_name(
                                    v["node"]["AstNode"]["data"]["typeName"]
                                ),
                            ),
                            id,
                        )
                    )
                case "DefArray":
                    data = v["node"]["AstNode"]["data"]
                    member = ModuleMemberDefArray(
                        AstNode.create_with_id(
                            DefArray(
                                name,
                                translate_expr(data["size"]),
                                translate_type_name(data["eltType"]),
                                translate_optional(data["default"], translate_expr),
                                translate_optional(
                                    data["format"],
                                    translate_string 
                                ),
                            ),
                            id,
                        )
                    )
                case "DefComponent":
                    data = v["node"]["AstNode"]["data"]
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
                    data = v["node"]["AstNode"]["data"]
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
                                translate_init_specs(data["initSpecs"])
                            ),
                            id
                        )
                    )
                case "DefConstant":
                    member = ModuleMemberDefConstant(
                        AstNode.create_with_id(
                            DefConstant(
                                name,
                                translate_expr(v["node"]["AstNode"]["data"]["value"])
                            ),
                            id,
                        )
                    )
                case "DefEnum":
                    data = v["node"]["AstNode"]["data"]
                    constants = []
                    for c in data["constants"]:
                        const = c[1]
                        node = AstNode.create_with_id(
                            DefEnumConstant(
                                const["AstNode"]["data"]["name"],
                                translate_optional(const["AstNode"]["data"]["value"], translate_expr)
                            ),
                            const["AstNode"]["id"]
                        )
                        constants.append(annotate(c[0], node, c[2]))
                    member = ModuleMemberDefEnum(
                        AstNode.create_with_id(
                            DefEnum(
                                name,
                                translate_optional(data["typeName"], translate_type_name),
                                constants
                            ),
                            id
                        )
                    )
                case "DefInterface":
                    member = ModuleMemberDefInterface(
                        AstNode.create_with_id(
                            DefInterface(
                                name, 
                                translate_interface_members(v["node"]["AstNode"]["data"]["members"])
                            ), 
                            id
                        )
                    )
                case "DefModule":
                    sub_dict = v["node"]["AstNode"]["data"]["members"]
                    member = ModuleMemberDefModule(
                        AstNode.create_with_id(
                            DefModule(name, translate_module_members(sub_dict)), id
                        )
                    )
                case "DefPort":
                    data = v["node"]["AstNode"]["data"]
                    params = translate_formal_params(data["params"])
                    member = ModuleMemberDefPort(
                        AstNode.create_with_id(
                            DefPort(name, params, translate_optional(data["returnType"], translate_type_name)), 
                            id
                        )
                    )
                case "DefStateMachine":
                    sub_dict = v["node"]["AstNode"]["data"]["members"]
                    member = ModuleMemberDefStateMachine(
                        AstNode.create_with_id(
                            DefStateMachine(
                                name, translate_state_machine_members(sub_dict)
                            ),
                            id,
                        )
                    )
                case "DefStruct":
                    data = v["node"]["AstNode"]["data"]
                    struct_members = []
                    for m in data["members"]:
                        member_data = m[1]["AstNode"]["data"]
                        node = AstNode.create_with_id(
                            StructTypeMember(
                                member_data["name"],
                                translate_optional(member_data["size"], translate_expr),
                                translate_type_name(member_data["typeName"]),
                                translate_optional(member_data["format"], translate_string)
                            ),
                            m[1]["AstNode"]["data"],
                        )
                        struct_members.append(annotate(m[0], node, m[2]))
                    member = ModuleMemberDefStruct(
                        AstNode.create_with_id(
                            DefStruct(
                                data["name"], 
                                struct_members, 
                                translate_optional(data["default"], translate_expr)
                            ),
                            id,
                        )
                    )
                case "DefTopology":
                    data = v["node"]["AstNode"]["data"]
                    member = ModuleMemberDefTopology(
                        AstNode.create_with_id(
                            DefTopology(name, translate_topology_members(data["members"])), 
                            id
                        )
                    )
                case "SpecInclude": # TODO delete these cases (or handle as special case "not supported in fpp-to-json?")
                    # ModuleMemberSpecInclude()
                    raise Exception("SpecInclude translation not implemented")
                case "SpecLoc":
                    raise Exception("SpecLoc translation not implemented")
                    # ModuleMemberSpecLoc()
        if member:
            members.append(annotate(m[0], member, m[2]))
        else:
            raise Exception(f'Member "{k}" not defined!')
    return members

def translate_state_machine_members(d: Dict[str, List]) -> List[StateMachineMember]:
    members = []
    if d.get("Some"):
        for l in d["Some"]:
            for k, v in l[1].items():
                id = v["node"]["AstNode"]["id"]
                data: dict = v["node"]["AstNode"]["data"]
                member = None
                match k:
                    case "DefAction":
                        member = StateMachineMemberDefAction(
                            AstNode.create_with_id(
                                DefAction(
                                    data["name"],
                                    translate_optional(data["typeName"], translate_type_name)
                                ), 
                                id
                            )
                        )
                    case "DefChoice":
                        member = StateMachineMemberDefChoice(
                            AstNode.create_with_id(
                                DefChoice(
                                    data["name"],
                                    translate_ident(data["guard"]),
                                    translate_transition_expr(data["ifTransition"]),
                                    translate_transition_expr(
                                        data["elseTransition"]
                                    ),
                                ),
                                id,
                            )
                        )
                    case "DefGuard":
                        type_name = None
                        if "Some" in data.get("typeName"):
                            type_name = translate_type_name(
                                data.get("typeName").get("Some")
                            )
                        member = StateMachineMemberDefGuard(
                            AstNode.create_with_id(
                                DefGuard(data["name"], type_name), id
                            )
                        )
                    case "DefSignal":
                        type_name = None
                        if "Some" in data.get("typeName"):
                            type_name = translate_type_name(
                                data.get("typeName").get("Some")
                            )
                        member = StateMachineMemberDefSignal(
                            AstNode.create_with_id(
                                DefSignal(data["name"], type_name), id
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
        if member:
            members.append(annotate(l[0], member, l[2]))
        else:
            raise Exception("Member not defined!")
    return members

def translate_ast_json(file: str):
    if not os.path.exists(file):
        raise FileNotFoundError(f'File "{file}" not found')
    with open(file, "r") as f:
        data: List[Dict] = json.load(f)
        for d in data:
            # tu = TransUnit([])
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
                Locations.put(int(k), Location(Path(v["file"]), v["pos"], v["includingLoc"]))
            except KeyError as e:
                raise KeyError(f"Location map for ID {k} is missing required field {e}")
    return Locations.get_map()
