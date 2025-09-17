import json
from typing import (
    Dict,
    List,
    Set,
    Callable,
    Any,
    Optional,
    Tuple,
    TypeVar,
    cast,
    Type as TypingType,
)
import os
from fprime_python_model.fpp_ast import fpp_ast
from fprime_python_model.fpp_ast.fpp_ast_node import AstId, T
from pathlib import Path
from fprime_python_model.semantics.analysis import Analysis
from fprime_python_model.semantics.symbol import *
from fprime_python_model.semantics.scope import Scope
from fprime_python_model.semantics.name_group import NameGroup
from fprime_python_model.semantics.types_values import (
    Type,
    Value,
    BooleanType,
    FloatType,
    IntType,
    StringType,
    FloatKind,
    IntegerType,
    PrimitiveIntType,
    PrimitiveIntKind,
    EnumType,
    EnumConstantValue,
    ArrayType,
    AnonArrayType,
    ArrayValue,
    AnonArrayValue,
    FloatValue,
    StringValue,
    IntegerValue,
    PrimitiveIntValue,
    StructValue,
    BooleanValue,
    AbsTypeValue,
    AbsType,
    StructType,
    AnonStructType,
    AnonStructValue,
    StructMembersValue,
    StructMembersType,
    AliasType,
)
from fprime_python_model.utils.error import InvalidFppToJsonField
from fprime_python_model.semantics.format import (
    Format,
    DefaultField,
    IntegerField,
    RationalField,
    RationalFieldType,
    IntegeFieldType,
    Field,
)
from fprime_python_model.semantics.component import Component
from fprime_python_model.semantics.command import (
    Command,
    CommandParam,
    CommandNonParam,
    NonParamKind,
    ParamKind,
    NonParamKindAsync,
    NonParamKindGuarded,
    NonParamKindSync,
    ParamKindSet,
    ParamKindSave,
)
from fprime_python_model.semantics.port_instance import (
    PortInstance,
    SpecialPortInstance,
    GeneralPortInstance,
    InternalPortInstance,
    PortInstanceType,
    DefPortPortInstanceType,
    SerialPortInstanceType,
)
from fprime_python_model.translators.ast_translator import (
    get_queue_full,
    translate_special_port_instance,
    translate_general_kind,
    translate_special_kind,
    translate_spec_tlm_channel_update,
)
from fprime_python_model.semantics.tlm_channel import TlmChannel, TlmChannelId, Limits
from fprime_python_model.semantics.event import Event, EventId
from fprime_python_model.semantics.param import Param, ParamId
from fprime_python_model.semantics.state_machine_instance import StateMachineInstance
from fprime_python_model.semantics.container import Container, ContainerId
from fprime_python_model.semantics.record import Record, RecordId
from fprime_python_model.utils.error import InternalError

RT = TypeVar("RT")


class AnalysisTranslator:
    """
    Translates the JSON representation of an FPP analysis to an Analysis Python data structure.
    """

    def __init__(
        self,
        ast_map: Dict[AstId, AstNode],
        annotated_ast_map: Dict[AstId, fpp_ast.Annotated[AstNode]],
        analysis_json_file: str,
    ):
        self.ast_map: Dict[AstId, AstNode] = ast_map
        self.annotated_ast_map: Dict[AstId, fpp_ast.Annotated[AstNode]] = (
            annotated_ast_map
        )
        self.analysis_json_file: str = analysis_json_file

    def get_annotated_ast_node_by_id(
        self, node_id: AstId
    ) -> fpp_ast.Annotated[AstNode]:
        if node_id in self.annotated_ast_map:
            return self.annotated_ast_map[node_id]
        elif node_id in self.ast_map:
            return (list(), self.ast_map[node_id], list())
        else:
            raise InternalError(f"Could not find AST node with ID {node_id}")

    def translate_optional(self, d: dict, func: Callable[[Any], T]) -> Optional[T]:
        if "Some" in d:
            return func(d["Some"])
        else:
            return None

    def translate_input_file_set(self, l: List[str]) -> Set[Path]:
        out_set: Set[Path] = set()
        for i in l:
            out_set.add(Path(str(i)))
        return out_set

    def translate_symbol(self, symbol_type: str, node_id: AstId) -> Symbol:
        a_node = self.get_annotated_ast_node_by_id(node_id)
        match symbol_type:
            case "AbsType":
                return AbsTypeSymbol(a_node)
            case "AliasType":
                return AliasTypeSymbol(a_node)
            case "Array":
                return ArraySymbol(a_node)
            case "Component":
                return ComponentSymbol(a_node)
            case "ComponentInstance":
                return ComponentInstanceSymbol(a_node)
            case "Constant":
                return ConstantSymbol(a_node)
            case "Enum":
                return EnumSymbol(a_node)
            case "EnumConstant":
                return EnumConstantSymbol(a_node)
            case "Interface":
                return InterfaceSymbol(a_node)
            case "Module":
                return ModuleSymbol(a_node)
            case "Port":
                return PortSymbol(a_node)
            case "StateMachine":
                return StateMachineSymbol(a_node)
            case "Struct":
                return StructSymbol(a_node)
            case "Topology":
                return TopologySymbol(a_node)
            case _:
                raise InvalidFppToJsonField(symbol_type)

    def get_symbol_type_from_node(self, a_node: fpp_ast.Annotated[AstNode[T]]) -> str:
        _, node, _ = a_node
        data = node.data
        match data:
            case fpp_ast.DefAbsType():
                return "AbsType"
            case fpp_ast.DefAliasType():
                return "AliasType"
            case fpp_ast.DefArray():
                return "Array"
            case fpp_ast.DefComponent():
                return "Component"
            case fpp_ast.DefComponentInstance():
                return "ComponentInstance"
            case fpp_ast.DefConstant():
                return "Constant"
            case fpp_ast.DefEnum():
                return "Enum"
            case fpp_ast.DefEnumConstant():
                return "EnumConstant"
            case fpp_ast.DefInterface():
                return "Interface"
            case fpp_ast.DefModule():
                return "Module"
            case fpp_ast.DefPort():
                return "Port"
            case fpp_ast.DefStateMachine():
                return "StateMachine"
            case fpp_ast.DefStruct():
                return "Struct"
            case fpp_ast.DefTopology():
                return "Topology"
            case _:
                raise InternalError("Could not determine symbol for AST node")

    def translate_parent_symbol_map(self, d: Dict[str, dict]) -> Dict[AstId, Symbol]:
        out_dict: Dict[AstId, Symbol] = dict()
        for child_id, inner_dict in d.items():
            parent_symbol_type = next(iter(inner_dict))
            parent_id = AstId(inner_dict[parent_symbol_type]["nodeId"])
            parent_symbol: Symbol = self.translate_symbol(parent_symbol_type, parent_id)
            out_dict[AstId(child_id)] = parent_symbol
        return out_dict

    def translate_use_def_map(self, d: Dict[str, dict]) -> Dict[AstId, Symbol]:
        out_dict: Dict[AstId, Symbol] = dict()
        for use_id, inner_dict in d.items():
            def_symbol_type = next(iter(inner_dict))
            def_id = AstId(inner_dict[def_symbol_type]["nodeId"])
            def_symbol: Symbol = self.translate_symbol(def_symbol_type, def_id)
            out_dict[AstId(use_id)] = def_symbol
        return out_dict

    def translate_name_group(self, ng: str) -> NameGroup:
        match ng:
            case "ComponentInstance":
                return NameGroup.COMPONENT_INSTANCE
            case "Component":
                return NameGroup.COMPONENT
            case "Port":
                return NameGroup.PORT
            case "StateMachine":
                return NameGroup.STATE_MACHINE
            case "Topology":
                return NameGroup.TOPOLOGY
            case "Interface":
                return NameGroup.INTERFACE
            case "Type":
                return NameGroup.TYPE
            case "Value":
                return NameGroup.VALUE
            case _:
                raise InternalError("Encountered invalid name group.")

    def translate_scope(self, d: Dict[str, dict]) -> Scope:
        scope = Scope()
        for name_group_str, scope_map in d.items():
            name_group = self.translate_name_group(name_group_str)
            inner_map: Dict[str, dict] = scope_map["map"]
            for name, inner_dict in inner_map.items():
                symbol_type = next(iter(inner_dict))
                symbol_id = inner_dict[symbol_type]["nodeId"]
                symbol = self.translate_symbol(symbol_type, symbol_id)
                scope = scope.put(name_group, symbol.get_unqualified_name(), symbol)
        return scope

    def symbol_scope_translator(self, d: Dict[str, dict]) -> Dict[AstId, Scope]:
        out_dict: Dict[AstId, Scope] = dict()
        for id, scope_map in d.items():
            out_dict[AstId(id)] = self.translate_scope(scope_map["map"])
        return out_dict

    def translate_primitive_type(self, d: Dict[str, dict]) -> Type:
        t_type = next(iter(d))
        match t_type:
            case "Boolean":
                return self.translate_boolean_type()
            case "Float":
                kind = self.translate_float_kind(next(iter(d[t_type]["kind"])))
                return FloatType(kind)
            case _:
                raise InternalError(f"Translation not implemented for {t_type}")

    def translate_float_kind(self, kind_str: str) -> FloatKind:
        if kind_str == "F32":
            kind = FloatKind.F32
        elif kind_str == "F64":
            kind = FloatKind.F64
        else:
            raise InvalidFppToJsonField(kind_str)
        return kind

    def translate_primitive_int_kind(self, kind_str: str) -> PrimitiveIntKind:
        if kind_str == "U8":
            kind = PrimitiveIntKind.U8
        elif kind_str == "U16":
            kind = PrimitiveIntKind.U16
        elif kind_str == "U32":
            kind = PrimitiveIntKind.U32
        elif kind_str == "U64":
            kind = PrimitiveIntKind.U64
        elif kind_str == "I8":
            kind = PrimitiveIntKind.I8
        elif kind_str == "I16":
            kind = PrimitiveIntKind.I16
        elif kind_str == "I32":
            kind = PrimitiveIntKind.I32
        elif kind_str == "I64":
            kind = PrimitiveIntKind.I64
        else:
            raise InvalidFppToJsonField(kind_str)
        return kind

    def translate_int_type(self, d: Dict[str, dict]) -> Type:
        t_type = next(iter(d))
        match t_type:
            case "PrimitiveInt":
                kind = self.translate_primitive_int_kind(next(iter(d[t_type]["kind"])))
                return PrimitiveIntType(kind)
            case "Integer":
                return IntegerType()
            case _:
                raise InternalError(f"Translation not implemented for {t_type}")

    def translate_enum_type(self, d: Dict) -> EnumType:
        a_node = self.get_annotated_ast_node_by_id(AstId(d["node"]["astNodeId"]))
        kind = self.translate_primitive_int_kind(next(iter(d["repType"]["kind"])))
        rep_type = PrimitiveIntType(kind)
        default = self.translate_optional(
            d["default"], self.translate_enum_constant_value
        )
        return EnumType(a_node, rep_type, default)

    def translate_abs_type(self, d: Dict[str, dict]) -> AbsType:
        a_node = self.get_annotated_ast_node_by_id(AstId(d["node"]["astNodeId"]))
        return AbsType(a_node)

    def translate_anon_array_type(self, d: Dict[str, dict]) -> AnonArrayType:
        size = self.translate_optional(d["size"], int)
        elt_type = self.translate_type(d["eltType"])
        return AnonArrayType(size, elt_type)

    def translate_anon_array_value(self, d: Dict[str, dict]) -> AnonArrayValue:
        element_values = []
        for elem in d["elements"]:
            element_values.append(self.translate_value(elem))
        return AnonArrayValue(element_values)

    def translate_array_value(self, d: Dict[str, dict]) -> ArrayValue:
        return ArrayValue(
            self.translate_anon_array_value(d["anonArray"]),
            self.translate_array_type(d["t"]),
        )

    def translate_array_type(self, d: Dict[str, dict]) -> ArrayType:
        a_node = self.get_annotated_ast_node_by_id(AstId(d["node"]["astNodeId"]))
        anon_array = self.translate_anon_array_type(d["anonArray"])
        default = self.translate_optional(d["default"], self.translate_array_value)
        format = self.translate_optional(d["format"], self.translate_format)
        return ArrayType(a_node, anon_array, default, format)

    def translate_string_type(self, d: Dict[str, dict]) -> StringType:
        size = None
        if "Some" in d["size"]:
            _, size, _ = self.get_annotated_ast_node_by_id(
                AstId(d["size"]["Some"]["astNodeId"])
            )
        return StringType(size)

    def translate_anon_struct_type(self, d: Dict[str, dict]) -> AnonStructType:
        out_dict: Dict[fpp_ast.Unqualified, Type] = dict()
        for member_unqual_name, t in d["members"].items():
            member_type = self.translate_type(t)
            out_dict[member_unqual_name] = member_type
        return AnonStructType(out_dict)

    def translate_anon_struct_value(self, d: Dict[str, dict]) -> AnonStructValue:
        out_dict: Dict[fpp_ast.Unqualified, Value] = dict()
        for member_unqual_name, t in d["members"].items():
            member_type = self.translate_value(t)
            out_dict[member_unqual_name] = member_type
        return AnonStructValue(out_dict)

    def translate_struct_value(self, d: Dict[str, dict]) -> StructValue:
        return StructValue(
            self.translate_anon_struct_value(d["anonStruct"]),
            self.translate_struct_type(d["t"]),
        )

    def translate_format(self, d: Dict[str, dict]) -> Format:
        prefix: str = str(d["prefix"])
        fields = d["fields"]
        field_list: List[Tuple[Field, str]] = []
        for f in fields:
            field_type = next(iter(f[0]))
            field_string = f[1]
            field: Optional[Field] = None
            if field_type == "Default":
                field = DefaultField()
            elif field_type == "Rational":
                precision = self.translate_optional(f[0][field_type]["precision"], int)
                rt = next(iter(f[0][field_type]["t"]))
                if rt == "Fixed":
                    rational_type = RationalFieldType.FIXED
                elif rt == "Exponent":
                    rational_type = RationalFieldType.EXPONENT
                elif rt == "General":
                    rational_type = RationalFieldType.GENERAL
                else:
                    raise InvalidFppToJsonField(rt)
                field = RationalField(precision, rational_type)
            elif field_type == "Integer":
                it = next(iter(f[0][field_type]["t"]))
                if it == "Character":
                    integer_type = IntegeFieldType.CHARACTER
                elif it == "Decimal":
                    integer_type = IntegeFieldType.DECIMAL
                elif it == "Hexadecimal":
                    integer_type = IntegeFieldType.HEXADECIMAL
                elif it == "Octal":
                    integer_type = IntegeFieldType.OCTAL
                else:
                    raise InvalidFppToJsonField(it)
                field = IntegerField(integer_type)
            else:
                raise InvalidFppToJsonField(field_type)

            field_list.append((field, field_string))
        return Format(prefix, field_list)

    def translate_sizes(self, d: Dict[str, int]) -> Dict[fpp_ast.Unqualified, int]:
        out_dict: Dict[fpp_ast.Unqualified, int] = dict()
        for name, size in d.items():
            out_dict[fpp_ast.Unqualified(name)] = self.require_type(size, int)
        return out_dict

    def translate_struct_type(self, d: Dict[str, dict]) -> StructType:
        a_node = self.get_annotated_ast_node_by_id(AstId(d["node"]["astNodeId"]))
        anon_struct_type = self.translate_anon_struct_type(d["anonStruct"])
        default = self.translate_optional(d["default"], self.translate_struct_value)
        sizes: Dict[fpp_ast.Unqualified, int] = self.translate_sizes(d["sizes"])
        formats: Dict[fpp_ast.Unqualified, Format] = dict()
        for name, format_dict in d["formats"].items():
            formats[name] = self.translate_format(format_dict)
        return StructType(a_node, anon_struct_type, default, sizes, formats)

    def translate_alias_type(self, d: Dict[str, dict]) -> AliasType:
        a_node = self.get_annotated_ast_node_by_id(AstId(d["node"]["astNodeId"]))
        return AliasType(a_node, self.translate_type(d["aliasType"]))

    def translate_boolean_type(self) -> BooleanType:
        return BooleanType()

    def require_type(self, var: object, expected_type: TypingType[RT]) -> RT:
        if not isinstance(var, expected_type):
            raise TypeError(
                f"{var} must be of type {expected_type.__name__}, not {type(var).__name__}"
            )
        return cast(RT, var)

    def translate_primitive_int_value(self, d: Dict[str, dict]) -> PrimitiveIntValue:
        value: int = self.require_type(d["value"], int)
        kind = self.translate_primitive_int_kind(next(iter(d["kind"])))
        return PrimitiveIntValue(value, kind)

    def translate_string_value(self, d: Dict[str, dict]) -> StringValue:
        value: str = self.require_type(d["value"], str)
        return StringValue(value)

    def translate_float_value(self, d: Dict[str, dict]) -> FloatValue:
        value: float = self.require_type(d["value"], float)
        kind = self.translate_float_kind(next(iter(d["kind"])))
        return FloatValue(value, kind)

    def translate_abs_type_value(self, d: Dict[str, dict]) -> AbsTypeValue:
        return AbsTypeValue(self.translate_abs_type(d["t"]))

    def translate_enum_constant_value(self, d: Dict[str, dict]) -> EnumConstantValue:
        value: Tuple[fpp_ast.Unqualified, int] = d["value"][0], d["value"][1]
        t: EnumType = self.translate_enum_type(d["t"])
        return EnumConstantValue(value, t)

    def translate_integer_value(self, d: Dict[str, int]) -> IntegerValue:
        return IntegerValue(int(d["value"]))

    def translate_boolean_value(self, d: Dict[str, int]) -> BooleanValue:
        return BooleanValue(bool(d["value"]))

    def translate_value(self, d: Dict[str, dict]) -> Value:
        v_type = next(iter(d))
        match v_type:
            case "Integer":
                return self.translate_integer_value(d[v_type])
            case "PrimitiveInt":
                return self.translate_primitive_int_value(d[v_type])
            case "Boolean":
                return self.translate_boolean_value(d[v_type])
            case "Float":
                return self.translate_float_value(d[v_type])
            case "String":
                return self.translate_string_value(d[v_type])
            case "Array":
                return self.translate_array_value(d[v_type])
            case "Struct":
                return self.translate_struct_value(d[v_type])
            case "EnumConstant":
                return self.translate_enum_constant_value(d[v_type])
            case "AbsType":
                return self.translate_abs_type_value(d[v_type])
            case "AnonStruct":
                return self.translate_anon_struct_value(d[v_type])
            case "AnonArray":
                return self.translate_anon_array_value(d[v_type])
            case _:
                raise InternalError(f"Translation not implemented for {v_type}")

    def translate_type(self, d: Dict[str, dict]) -> Type:
        t_type = next(iter(d))
        match t_type:
            case "Primitive":
                return self.translate_primitive_type(d[t_type])
            case "Int":
                return self.translate_int_type(d[t_type])
            case "Boolean":
                return self.translate_boolean_type()
            case "Enum":
                return self.translate_enum_type(d[t_type])
            case "Array":
                return self.translate_array_type(d[t_type])
            case "Struct":
                return self.translate_struct_type(d[t_type])
            case "String":
                return self.translate_string_type(d[t_type])
            case "AnonStruct":
                return self.translate_anon_struct_type(d[t_type])
            case "AnonArray":
                return self.translate_anon_array_type(d[t_type])
            case "AbsType":
                return self.translate_abs_type(d[t_type])
            case "AliasType":
                return self.translate_alias_type(d[t_type])
            case _:
                raise InternalError(f"Translation not implemented for type {t_type}")

    def translate_command_non_param_kind(self, d: Dict[str, dict]) -> NonParamKind:
        kind = next(iter(d))
        match kind:
            case "Async":
                priority = self.translate_optional(d[kind]["priority"], int)
                queue_full = get_queue_full(d[kind]["queueFull"])
                return NonParamKindAsync(priority, queue_full)
            case "Sync":
                return NonParamKindSync()
            case "Guarded":
                return NonParamKindGuarded()
            case _:
                raise InvalidFppToJsonField(kind)

    def translate_command_param_kind(self, d: Dict[str, dict]) -> ParamKind:
        kind = next(iter(d))
        match kind:
            case "Set":
                return ParamKindSet()
            case "Save":
                return ParamKindSave()
            case _:
                raise InvalidFppToJsonField(kind)

    def translate_command(self, d: Dict[str, dict]) -> Command:
        c_type = next(iter(d))
        a_node = self.get_annotated_ast_node_by_id(int(d[c_type]["aNode"]["astNodeId"]))
        match c_type:
            case "NonParam":
                return CommandNonParam(
                    a_node, self.translate_command_non_param_kind(d[c_type]["kind"])
                )
            case "Param":
                return CommandParam(
                    a_node, self.translate_command_param_kind(d[c_type]["kind"])
                )
            case _:
                raise InvalidFppToJsonField(c_type)

    def translate_port_instance_type(self, d: Dict[str, dict]) -> PortInstanceType:
        ty = next(iter(d))
        match ty:
            case "DefPort":
                symbol: PortSymbol = self.require_type(
                    self.translate_symbol("Port", d[ty]["symbol"]["Port"]["nodeId"]),
                    PortSymbol,
                )
                return DefPortPortInstanceType(symbol)
            case "Serial":
                return SerialPortInstanceType()
            case _:
                raise InvalidFppToJsonField(ty)

    def translate_port_instance(self, d: Dict[str, dict]) -> PortInstance:
        p_type = next(iter(d))
        a_node = self.get_annotated_ast_node_by_id(int(d[p_type]["aNode"]["astNodeId"]))
        match p_type:
            case "Special":
                return self.translate_special_port_instance(d[p_type])
            case "General":
                return self.translate_general_port_instance(d[p_type])
            case "Internal":
                priority = self.translate_optional(d[p_type]["priority"], int)
                queue_full = self.translate_optional(
                    d[p_type]["queueFull"], get_queue_full
                )
                return InternalPortInstance(a_node, priority, queue_full)
            case _:
                raise InvalidFppToJsonField(p_type)

    def translate_special_port_instance(
        self, d: Dict[str, dict]
    ) -> SpecialPortInstance:
        a_node = self.get_annotated_ast_node_by_id(int(d["aNode"]["astNodeId"]))
        specifier = translate_special_port_instance(d["specifier"])
        symbol: PortSymbol = self.require_type(
            self.translate_symbol("Port", d["symbol"]["Port"]["nodeId"]), PortSymbol
        )
        priority = self.translate_optional(d["priority"], int)
        queue_full = self.translate_optional(d["queueFull"], get_queue_full)
        import_node_ids = [AstId(i) for i in d["importNodeIds"]]
        return SpecialPortInstance(
            a_node, specifier, symbol, priority, queue_full, import_node_ids
        )

    def translate_general_port_instance(
        self, d: Dict[str, dict]
    ) -> GeneralPortInstance:
        a_node = self.get_annotated_ast_node_by_id(int(d["aNode"]["astNodeId"]))
        kind = translate_general_kind(d["kind"])
        size = d["size"]
        if not isinstance(size, int):
            raise TypeError(
                f"{d['size']} has an invalid type; expected int, actual {type(d['size'])}"
            )
        ty = self.translate_port_instance_type(d["ty"])
        import_node_ids = [AstId(i) for i in d["importNodeIds"]]
        return GeneralPortInstance(a_node, None, kind, size, ty, import_node_ids)

    def translate_limit_kind(self, kind_str: str) -> fpp_ast.LimitKind:
        match kind_str:
            case "red":
                return fpp_ast.LimitKind.RED
            case "orange":
                return fpp_ast.LimitKind.ORANGE
            case "yellow":
                return fpp_ast.LimitKind.YELLOW
            case _:
                raise InvalidFppToJsonField(kind_str)

    def translate_limits(self, d: Dict[str, dict]) -> Limits:
        out_dict: Limits = dict()
        for limit_key, limit_value in d.items():
            limit_kind = self.translate_limit_kind(limit_key)
            channel_id = int(limit_value[0])
            value = self.translate_value(limit_value[1])
            out_dict[limit_kind] = (channel_id, value)
        return out_dict

    def translate_tlm_channel(self, d: Dict[str, dict]) -> TlmChannel:
        a_node = self.get_annotated_ast_node_by_id(int(d["aNode"]["astNodeId"]))
        c_type = self.translate_type(d["channelType"])
        update = translate_spec_tlm_channel_update(d["update"])
        format = self.translate_optional(d["format"], self.translate_format)
        low_limits = self.translate_limits(d["lowLimits"])
        high_limits = self.translate_limits(d["highLimits"])
        return TlmChannel(a_node, c_type, update, format, low_limits, high_limits)

    def translate_event(self, d: Dict[str, dict]) -> Event:
        a_node = self.get_annotated_ast_node_by_id(int(d["aNode"]["astNodeId"]))
        format = self.translate_format(d["format"])
        throttle = self.translate_optional(d["throttle"], int)
        return Event(a_node, format, throttle)

    def translate_param(self, d: Dict[str, dict]) -> Param:
        a_node = self.get_annotated_ast_node_by_id(int(d["aNode"]["astNodeId"]))
        param_type = self.translate_type(d["paramType"])
        default = self.translate_optional(d["default"], self.translate_value)
        set_opcode: int = self.require_type(d["setOpcode"], int)
        save_opcode: int = self.require_type(d["saveOpcode"], int)
        is_external: bool = self.require_type(d["isExternal"], bool)
        return Param(a_node, param_type, default, set_opcode, save_opcode, is_external)

    # def translate_spec_port_matching(self, d: Dict[str, dict]) -> fpp_ast.SpecPortMatching:
    #     return fpp_ast.SpecPortMatching()

    def translate_state_machine_instance(
        self, d: Dict[str, dict]
    ) -> StateMachineInstance:
        a_node = self.get_annotated_ast_node_by_id(int(d["aNode"]["astNodeId"]))
        symbol: StateMachineSymbol = self.require_type(
            self.translate_symbol("StateMachine", d["symbol"]["node"]["astNodeId"]),
            StateMachineSymbol,
        )
        priority = self.translate_optional(d["priority"], int)
        queue_full = get_queue_full(d["queueFull"])
        return StateMachineInstance(a_node, symbol, priority, queue_full)

    def translate_container(self, d: Dict[str, dict]) -> Container:
        a_node = self.get_annotated_ast_node_by_id(int(d["aNode"]["astNodeId"]))
        default_priority = self.translate_optional(d["defaultPriority"], int)
        return Container(a_node, default_priority)

    def translate_record(self, d: Dict[str, dict]) -> Record:
        a_node = self.get_annotated_ast_node_by_id(int(d["aNode"]["astNodeId"]))
        record_type = self.translate_type(d["recordType"])
        is_array = bool(d["isArray"])
        return Record(a_node, record_type, is_array)

    def translate_port_map(
        self, d: Dict[str, dict]
    ) -> Dict[fpp_ast.Unqualified, PortInstance]:
        port_map: Dict[fpp_ast.Unqualified, PortInstance] = dict()
        for port_name, port_value in d.items():
            port_map[fpp_ast.Unqualified(fpp_ast.Ident(port_name))] = (
                self.translate_port_instance(port_value)
            )
        return port_map

    def translate_spec_port_map(
        self, d: Dict[str, dict]
    ) -> Dict[fpp_ast.SpecialKind, SpecialPortInstance]:
        special_port_map: Dict[fpp_ast.SpecialKind, SpecialPortInstance] = dict()
        for special_port_value in d.values():
            special_port_kind = translate_special_kind(
                special_port_value["specifier"]["kind"]
            )
            special_port_map[special_port_kind] = self.translate_special_port_instance(
                special_port_value
            )
        return special_port_map

    def translate_command_map(self, d: Dict[str, dict]) -> Dict[AstId, Command]:
        command_map: Dict[AstId, Command] = dict()
        for command_id, command_value in d.items():
            command_map[AstId(command_id)] = self.translate_command(command_value)
        return command_map

    def translate_tlm_channel_map(
        self, d: Dict[str, dict]
    ) -> Dict[TlmChannelId, TlmChannel]:
        tlm_channel_map: Dict[TlmChannelId, TlmChannel] = dict()
        for tlm_channel_id, tlm_channel_value in d.items():
            tlm_channel_map[TlmChannelId(tlm_channel_id)] = self.translate_tlm_channel(
                tlm_channel_value
            )
        return tlm_channel_map

    def translate_tlm_channel_name_map(
        self, d: Dict[str, dict]
    ) -> Dict[fpp_ast.Unqualified, TlmChannel]:
        tlm_channel_name_map: Dict[fpp_ast.Unqualified, TlmChannel] = dict()
        for tlm_channel_name, tlm_channel_value in d.items():
            tlm_channel_name_map[
                fpp_ast.Unqualified(fpp_ast.Ident(tlm_channel_name))
            ] = self.translate_tlm_channel(tlm_channel_value)
        return tlm_channel_name_map

    def translate_event_map(self, d: Dict[str, dict]) -> Dict[EventId, Event]:
        event_map: Dict[EventId, Event] = dict()
        for event_id, event_value in d.items():
            event_map[EventId(event_id)] = self.translate_event(event_value)
        return event_map

    def translate_param_map(self, d: Dict[str, dict]) -> Dict[ParamId, Param]:
        param_map: Dict[ParamId, Param] = dict()
        for param_id, param_value in d.items():
            param_map[ParamId(param_id)] = self.translate_param(param_value)
        return param_map

    def translate_state_machine_instance_map(
        self, d: Dict[str, dict]
    ) -> Dict[fpp_ast.Unqualified, StateMachineInstance]:
        state_machine_instance_map: Dict[fpp_ast.Unqualified, StateMachineInstance] = (
            dict()
        )
        for sm_name, sm_inst_value in d.items():
            state_machine_instance_map[fpp_ast.Unqualified(fpp_ast.Ident(sm_name))] = (
                self.translate_state_machine_instance(sm_inst_value)
            )
        return state_machine_instance_map

    def translate_container_map(
        self, d: Dict[str, dict]
    ) -> Dict[ContainerId, Container]:
        container_map: Dict[ContainerId, Container] = dict()
        for container_id, container_value in d.items():
            container_map[ContainerId(container_id)] = self.translate_container(
                container_value
            )
        return container_map

    def translate_record_map(self, d: Dict[str, dict]) -> Dict[RecordId, Record]:
        record_map: Dict[RecordId, Record] = dict()
        for record_id, record_value in d.items():
            record_map[ContainerId(record_id)] = self.translate_record(record_value)
        return record_map

    def translate_component(self, d: Dict[str, dict]) -> Component:
        a_node = self.get_annotated_ast_node_by_id(int(d["aNode"]["astNodeId"]))
        return Component(
            a_node=a_node,
            port_map=self.translate_port_map(d["portMap"]),
            special_port_map=self.translate_spec_port_map(d["specialPortMap"]),
            command_map=self.translate_command_map(d["commandMap"]),
            tlm_channel_map=self.translate_tlm_channel_map(d["tlmChannelMap"]),
            tlm_channel_name_map=self.translate_tlm_channel_name_map(
                d["tlmChannelNameMap"]
            ),
            event_map=self.translate_event_map(d["eventMap"]),
            param_map=self.translate_param_map(d["paramMap"]),
            state_machine_instance_map=self.translate_state_machine_instance_map(
                d["stateMachineInstanceMap"]
            ),
            container_map=self.translate_container_map(d["containerMap"]),
            record_map=self.translate_record_map(d["recordMap"]),
        )

    def translate_type_map(self, d: Dict[str, dict]) -> Dict[AstId, Type]:
        out_dict: Dict[AstId, Type] = dict()
        for id, inner_dict in d.items():
            out_dict[AstId(id)] = self.translate_type(inner_dict)
        return out_dict

    def translate_value_map(self, d: Dict[str, dict]) -> Dict[AstId, Value]:
        out_dict: Dict[AstId, Value] = dict()
        for id, inner_dict in d.items():
            out_dict[AstId(id)] = self.translate_value(inner_dict)
        return out_dict

    def translate_component_map(self, d: Dict[str, dict]) -> Dict[AstId, Component]:
        out_dict: Dict[AstId, Component] = dict()
        for id, inner_dict in d.items():
            out_dict[AstId(id)] = self.translate_component(inner_dict)
        return out_dict

    def translate_analysis_json(self) -> Analysis:
        if not os.path.exists(self.analysis_json_file):
            raise FileNotFoundError(f'File "{self.analysis_json_file}" not found')
        with open(self.analysis_json_file, "r") as f:
            data: Dict = json.load(f)
            return Analysis(
                included_file_set=self.translate_input_file_set(
                    self.require_type(data.get("inputFileSet"), list)
                ),
                parent_symbol_map=self.translate_parent_symbol_map(
                    self.require_type(data.get("parentSymbolMap"), dict)
                ),
                use_def_map=self.translate_use_def_map(
                    self.require_type(data.get("useDefMap"), dict)
                ),
                symbol_scope_map=self.symbol_scope_translator(
                    self.require_type(data.get("symbolScopeMap"), dict)
                ),
                type_map=self.translate_type_map(
                    self.require_type(data.get("typeMap"), dict)
                ),
                value_map=self.translate_value_map(
                    self.require_type(data.get("valueMap"), dict)
                ),
                component_map=self.translate_component_map(
                    self.require_type(data.get("componentMap"), dict)
                ),
            )
