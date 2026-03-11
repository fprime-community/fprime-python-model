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
from fprime_python_model.fpp_ast.fpp_ast_node import AstNode, AstId, T
from pathlib import Path
from fprime_python_model.semantics.analysis import Analysis
from fprime_python_model.semantics.scope import Scope
from fprime_python_model.semantics.symbol import (
    Symbol,
    EnumConstantSymbol,
    EnumSymbol,
    StructSymbol,
    TopologySymbol,
    InterfaceSymbol,
    ArraySymbol,
    StateMachineSymbol,
    PortSymbol,
    ModuleSymbol,
    ComponentInstanceSymbol,
    ComponentSymbol,
    ConstantSymbol,
    AliasTypeSymbol,
    AbsTypeSymbol,
)
from fprime_python_model.semantics.name_group import NameGroup
from fprime_python_model.semantics.types_values import (
    Type,
    Value,
    BooleanType,
    FloatType,
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
    AliasType,
)
from fprime_python_model.utils.error import InvalidFppToJsonField
from fprime_python_model.semantics.format import (
    Format,
    DefaultField,
    IntegerField,
    RationalField,
    RationalFieldType,
    IntegerFieldType,
    Field,
)
from fprime_python_model.semantics.component import Component, PortMatching
from fprime_python_model.semantics.component_instance import ComponentInstance
from fprime_python_model.semantics.init_specifier import InitSpecifier
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
    translate_general_kind,
    translate_special_kind,
    translate_spec_tlm_channel_update,
    translate_spec_loc_kind,
    translate_pattern_kind,
)
from fprime_python_model.semantics.tlm_channel import TlmChannel, TlmChannelId, Limits
from fprime_python_model.semantics.event import Event, EventId, Throttle, TimeInterval
from fprime_python_model.semantics.param import Param, ParamId
from fprime_python_model.semantics.state_machine_instance import StateMachineInstance
from fprime_python_model.semantics.container import Container, ContainerId
from fprime_python_model.semantics.record import Record, RecordId
from fprime_python_model.utils.error import InternalError
from fprime_python_model.semantics.name import QualifiedName, UnqualifiedName
from fprime_python_model.semantics.topology import Topology
from fprime_python_model.fpp_ast.fpp_locations import Location
from fprime_python_model.semantics.connection import Connection, Endpoint
from fprime_python_model.semantics.connection_pattern import ConnectionPattern
from fprime_python_model.semantics.port_instance_identifier import (
    PortInstanceIdentifier,
)
from fprime_python_model.semantics.interface import Interface
from fprime_python_model.semantics.state_machine import StateMachine
from fprime_python_model.semantics.state_machine_analysis import (
    StateMachineAnalysis,
    SignalStateTransitionMap,
    StateTransitionMap,
    TransitionExprMap,
)
from fprime_python_model.semantics.state_machine_scope import StateMachineScope
from fprime_python_model.semantics.state_machine_name_group import StateMachineNameGroup
from fprime_python_model.semantics.state_machine_symbol import (
    StateMachineSymbolInterface,
    StateSymbol,
    ChoiceSymbol,
    GuardSymbol,
    SignalSymbol,
    ActionSymbol,
)
from fprime_python_model.semantics.transition_graph import (
    TransitionGraph,
    TransitionGraphNode,
    ArcMap,
    Arc,
    InitialArc,
    StateArc,
    ChoiceArc,
)
from fprime_python_model.semantics.state_or_junction import State, Choice, StateOrChoice
from fprime_python_model.semantics.state_machine_typed_element import (
    StateMachineTypedElement,
    StateEntryTypedElement,
    StateExitTypedElement,
    StateTransitionTypedElement,
    InitialTransitionTypedElement,
    ChoiceTypedElement,
)
from fprime_python_model.semantics.transition import (
    Transition,
    ExternalTransition,
    InternalTransition,
    GuardedTransition,
)
from fprime_python_model.semantics.framework_definitions import FrameworkDefinitions

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
        location_map: Dict[AstId, Location],
    ):
        self.ast_map: Dict[AstId, AstNode] = ast_map
        self.annotated_ast_map: Dict[AstId, fpp_ast.Annotated[AstNode]] = (
            annotated_ast_map
        )
        self.analysis_json_file: str = analysis_json_file
        self.location_map = location_map

        self.component_map: Dict[AstId, Component] = dict()
        self.component_instance_map: Dict[AstId, ComponentInstance] = dict()

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

    def translate_qualified_name(self, d: dict) -> QualifiedName:
        return QualifiedName(d["qualifier"], d["base"])

    def translate_file_set(self, l: List[str]) -> Set[Path]:
        out_set: Set[Path] = set()
        for i in l:
            out_set.add(Path(str(i)))
        return out_set

    def translate_location_specifier_map(
        self, l: List[Tuple[Tuple, Dict]]
    ) -> Dict[Tuple[fpp_ast.SpecLocKind, QualifiedName], fpp_ast.SpecLoc]:
        out_dict: Dict[Tuple[fpp_ast.SpecLocKind, QualifiedName], fpp_ast.SpecLoc] = (
            dict()
        )
        for ls in l:
            kind_json: Dict = ls[0][0]
            qual_name_json: Dict = ls[0][1]
            spec_loc_kind = translate_spec_loc_kind(kind_json)
            spec_loc_qualified_name = self.translate_qualified_name(qual_name_json)
            spec_loc_a_node = self.get_annotated_ast_node_by_id(ls[1]["astNodeId"])
            out_dict[(spec_loc_kind, spec_loc_qualified_name)] = spec_loc_a_node[1].data
        return out_dict

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
                raise InvalidFppToJsonField(
                    symbol_type, self.location_map.get(node_id, None)
                )

    def translate_state_machine_symbol(
        self, symbol_type: str, node_id: AstId
    ) -> StateMachineSymbolInterface:
        a_node = self.get_annotated_ast_node_by_id(node_id)
        match symbol_type:
            case "Choice":
                return ChoiceSymbol(a_node)
            case "State":
                return StateSymbol(a_node)
            case "Signal":
                return SignalSymbol(a_node)
            case "Action":
                return ActionSymbol(a_node)
            case "Guard":
                return GuardSymbol(a_node)
            case _:
                raise InvalidFppToJsonField(
                    symbol_type, self.location_map.get(node_id, None)
                )

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

    def translate_state_machine_use_def_map(
        self, d: Dict[str, dict]
    ) -> Dict[AstId, StateMachineSymbolInterface]:
        out_dict: Dict[AstId, StateMachineSymbolInterface] = dict()
        for use_id, inner_dict in d.items():
            def_symbol_type = next(iter(inner_dict))
            def_id = AstId(inner_dict[def_symbol_type]["nodeId"])
            def_symbol: StateMachineSymbolInterface = (
                self.translate_state_machine_symbol(def_symbol_type, def_id)
            )
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
                raise InternalError(f"Encountered invalid name group {ng}.")

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

    def translate_symbol_scope_map(self, d: Dict[str, dict]) -> Dict[AstId, Scope]:
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
                    integer_type = IntegerFieldType.CHARACTER
                elif it == "Decimal":
                    integer_type = IntegerFieldType.DECIMAL
                elif it == "Hexadecimal":
                    integer_type = IntegerFieldType.HEXADECIMAL
                elif it == "Octal":
                    integer_type = IntegerFieldType.OCTAL
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
                raise InvalidFppToJsonField(
                    p_type, self.location_map.get(a_node[1].get_id(), None)
                )

    def translate_special_port_instance(
        self, d: Dict[str, dict]
    ) -> SpecialPortInstance:
        a_node = self.get_annotated_ast_node_by_id(int(d["aNode"]["astNodeId"]))
        specifier = a_node[1].data
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
        specifier = a_node[1].data
        kind = translate_general_kind(d["kind"])
        size = d["size"]
        if not isinstance(size, int):
            raise TypeError(
                f"{d['size']} has an invalid type; expected int, actual {type(d['size'])}"
            )
        ty = self.translate_port_instance_type(d["ty"])
        import_node_ids = [AstId(i) for i in d["importNodeIds"]]
        return GeneralPortInstance(a_node, specifier, kind, size, ty, import_node_ids)

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

    def translate_time_interval(self, d: Dict[str, int]) -> TimeInterval:
        return TimeInterval(d["seconds"], d["useconds"])

    def translate_throttle(self, d: Dict[str, dict]) -> Throttle:
        return Throttle(
            self.require_type(d["count"], int),
            self.translate_optional(d["every"], self.translate_time_interval),
        )

    def translate_event(self, d: Dict[str, dict]) -> Event:
        a_node = self.get_annotated_ast_node_by_id(int(d["aNode"]["astNodeId"]))
        format = self.translate_format(d["format"])
        throttle = self.translate_optional(d["throttle"], self.translate_throttle)
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
    ) -> Dict[UnqualifiedName, PortInstance]:
        port_map: Dict[UnqualifiedName, PortInstance] = dict()
        for port_name, port_value in d.items():
            port_map[UnqualifiedName(port_name)] = self.translate_port_instance(
                port_value
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
    ) -> Dict[UnqualifiedName, TlmChannel]:
        tlm_channel_name_map: Dict[UnqualifiedName, TlmChannel] = dict()
        for tlm_channel_name, tlm_channel_value in d.items():
            tlm_channel_name_map[UnqualifiedName(tlm_channel_name)] = (
                self.translate_tlm_channel(tlm_channel_value)
            )
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
    ) -> Dict[UnqualifiedName, StateMachineInstance]:
        state_machine_instance_map: Dict[UnqualifiedName, StateMachineInstance] = dict()
        for sm_name, sm_inst_value in d.items():
            state_machine_instance_map[UnqualifiedName(sm_name)] = (
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

    def translate_spec_port_matching_list(
        self, l: List[Dict]
    ) -> List[fpp_ast.Annotated[AstNode[fpp_ast.SpecPortMatching]]]:
        out_list: List[fpp_ast.Annotated[AstNode[fpp_ast.SpecPortMatching]]] = []
        for sp in l:
            spm: fpp_ast.Annotated[AstNode[fpp_ast.SpecPortMatching]] = (
                self.get_annotated_ast_node_by_id(sp["astNodeId"])
            )
            out_list.append(spm)
        return out_list

    def translate_port_matching_list(self, l: List[Dict]) -> List[PortMatching]:
        out_list: List[PortMatching] = []
        for pm in l:
            out_list.append(
                PortMatching(
                    self.get_annotated_ast_node_by_id(pm["aNode"]["astNodeId"]),
                    self.translate_general_port_instance(pm["instance1"]),
                    self.translate_general_port_instance(pm["instance2"]),
                )
            )
        return out_list

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
            spec_port_matching_list=self.translate_spec_port_matching_list(
                self.require_type(d["specPortMatchingList"], list)
            ),
            state_machine_instance_map=self.translate_state_machine_instance_map(
                d["stateMachineInstanceMap"]
            ),
            port_matching_list=self.translate_port_matching_list(
                self.require_type(d["portMatchingList"], list)
            ),
            container_map=self.translate_container_map(d["containerMap"]),
            record_map=self.translate_record_map(d["recordMap"]),
        )

    def translate_direct_import_map(self, d: Dict) -> Dict[AstId, Location]:
        out_dict: Dict[AstId, Location] = dict()
        for k, v in d.items():
            out_dict[AstId(k)] = Location(Path(v["file"]), v["pos"], v["includingLoc"])
        return out_dict

    def translate_instance_map(
        self, l: list
    ) -> Dict[ComponentInstance, Tuple[fpp_ast.Visibility, Location]]:
        out_dict: Dict[ComponentInstance, Tuple[fpp_ast.Visibility, Location]] = dict()
        for i in l:
            location_json = i[1][1]
            ci = self.component_instance_map[i[0]["aNode"]["astNodeId"]]
            visibility = fpp_ast.Visibility.PRIVATE
            if "Public" in i[1][0]:
                visibility = fpp_ast.Visibility.PUBLIC
            location = Location(
                Path(location_json["file"]),
                location_json["pos"],
                location_json["includingLoc"],
            )

            out_dict[ci] = (visibility, location)
        return out_dict

    def translate_connection_pattern(self, d: Dict) -> ConnectionPattern:
        target_ident_nodes: List[AstNode[fpp_ast.QualIdent]] = []
        for t in d["targets"]:
            target_ident_nodes.append(
                self.get_annotated_ast_node_by_id(t[0]["aNode"]["astNodeId"])[1]
            )
        ast = fpp_ast.Pattern(
            translate_pattern_kind(d["ast"]["kind"]),
            self.ast_map[d["ast"]["source"]["astNodeId"]],
            target_ident_nodes,
        )
        source: Tuple[ComponentInstance, Location] = (
            self.component_instance_map[d["source"][0]["aNode"]["astNodeId"]],
            Location(
                Path(d["source"][1]["file"]),
                d["source"][1]["pos"],
                d["source"][1]["includingLoc"],
            ),
        )
        targets: Set[Tuple[ComponentInstance, Location]] = set()
        for t in d["targets"]:
            loc_dict = t[1]
            targets.add(
                (
                    self.component_instance_map[t[0]["aNode"]["astNodeId"]],
                    Location(
                        Path(loc_dict["file"]),
                        loc_dict["pos"],
                        loc_dict["includingLoc"],
                    ),
                )
            )
        return ConnectionPattern(
            a_node=self.get_annotated_ast_node_by_id(d["aNode"]["astNodeId"]),
            ast=ast,
            source=source,
            targets=targets,
        )

    def translate_pattern_map(
        self, d: Dict
    ) -> Dict[fpp_ast.PatternKind, ConnectionPattern]:
        out_dict: Dict[fpp_ast.PatternKind, ConnectionPattern] = dict()
        for k, v in d.items():
            out_dict[translate_pattern_kind(d)] = self.translate_connection_pattern(v)
        return out_dict

    def translate_port_instance_identifier(self, d: Dict) -> PortInstanceIdentifier:
        return PortInstanceIdentifier(
            component_instance=self.component_instance_map[
                d["componentInstance"]["aNode"]["astNodeId"]
            ],
            port_instance=self.translate_port_instance(d["portInstance"]),
        )

    def translate_endpoint(self, d: Dict) -> Endpoint:
        return Endpoint(
            loc=Location(
                Path(d["loc"]["file"]), d["loc"]["pos"], d["loc"]["includingLoc"]
            ),
            port=self.translate_port_instance_identifier(d["port"]),
            port_number=self.translate_optional(d["portNumber"], int),
        )

    def translate_connection(self, d: Dict) -> Connection:
        return Connection(
            from_endpoint=self.translate_endpoint(d["from"]),
            to_endpoint=self.translate_endpoint(d["to"]),
            is_unmatched=d["isUnmatched"],
        )

    def translate_connection_map(
        self, d: Dict
    ) -> Dict[UnqualifiedName, List[Connection]]:
        out_dict: Dict[UnqualifiedName, List[Connection]] = dict()
        for k, v in d.items():
            out_dict[UnqualifiedName(k)] = [self.translate_connection(c) for c in v]
        return out_dict

    def translate_input_output_connection_map(
        self, l: List
    ) -> Dict[PortInstanceIdentifier, Set[Connection]]:
        out_dict: Dict[PortInstanceIdentifier, Set[Connection]] = dict()
        for i in l:
            connections = set()
            for c in i[1]:
                connections.add(self.translate_connection(c))
            out_dict[self.translate_port_instance_identifier(i[0])] = connections
        return out_dict

    def translate_port_number_map(self, l: List) -> Dict[Connection, int]:
        out_dict: Dict[Connection, int] = dict()
        for i in l:
            out_dict[self.translate_connection(i[0])] = i[1]
        return out_dict

    def translate_unconnected_port_set(self, l: List) -> Set[PortInstanceIdentifier]:
        out_set: Set[PortInstanceIdentifier] = set()
        for pii in l:
            out_set.add(self.translate_port_instance_identifier(pii))
        return out_set

    def translate_topology(self, d: Dict) -> Topology:
        a_node = self.get_annotated_ast_node_by_id(int(d["aNode"]["astNodeId"]))
        return Topology(
            a_node=a_node,
            direct_import_map=self.translate_direct_import_map(d["directImportMap"]),
            transitive_import_set=set(
                [AstId(i["node"]["astNodeId"]) for i in d["transitiveImportSet"]]
            ),
            instance_map=self.translate_instance_map(d["instanceMap"]),
            pattern_map=self.translate_pattern_map(d["patternMap"]),
            connection_map=self.translate_connection_map(d["connectionMap"]),
            local_connection_map=self.translate_connection_map(d["localConnectionMap"]),
            output_connection_map=self.translate_input_output_connection_map(
                d["outputConnectionMap"]
            ),
            input_connection_map=self.translate_input_output_connection_map(
                d["inputConnectionMap"]
            ),
            from_port_number_map=self.translate_port_number_map(d["fromPortNumberMap"]),
            to_port_number_map=self.translate_port_number_map(d["toPortNumberMap"]),
            unconnected_port_set=self.translate_unconnected_port_set(
                d["unconnectedPortSet"]
            ),
        )

    def translate_init_specifier_map(
        self, d: Dict[str, dict]
    ) -> Dict[int, InitSpecifier]:
        out_dict: Dict[int, InitSpecifier] = dict()
        for id, inner_dict in d.items():
            out_dict[int(id)] = InitSpecifier(
                self.get_annotated_ast_node_by_id(inner_dict["aNode"]["astNodeId"]),
                inner_dict["phase"],
            )
        return out_dict

    def translate_component_instance(self, d: Dict[str, dict]) -> ComponentInstance:
        a_node = self.get_annotated_ast_node_by_id(int(d["aNode"]["astNodeId"]))
        return ComponentInstance(
            a_node=a_node,
            qualified_name=self.translate_qualified_name(d["qualifiedName"]),
            component=self.component_map[AstId(d["component"]["astNodeId"])],
            base_id=self.require_type(d["baseId"], int),
            max_id=self.require_type(d["maxId"], int),
            file=self.translate_optional(d["file"], str),
            queue_size=self.translate_optional(d["queueSize"], int),
            stack_size=self.translate_optional(d["stackSize"], int),
            priority=self.translate_optional(d["priority"], int),
            cpu=self.translate_optional(d["cpu"], int),
            init_specifier_map=self.translate_init_specifier_map(d["initSpecifierMap"]),
        )

    def translate_interface(self, d: Dict[str, dict]) -> Interface:
        a_node = self.get_annotated_ast_node_by_id(int(d["aNode"]["astNodeId"]))
        return Interface(
            a_node=a_node,
            port_map=self.translate_port_map(d["portMap"]),
            special_port_map=self.translate_spec_port_map(d["specialPortMap"]),
        )

    def translate_state_machine_name_group(self, ng: str) -> StateMachineNameGroup:
        match ng:
            case "Action":
                return StateMachineNameGroup.ACTION
            case "Guard":
                return StateMachineNameGroup.GUARD
            case "Signal":
                return StateMachineNameGroup.SIGNAL
            case "State":
                return StateMachineNameGroup.STATE
            case _:
                raise InternalError("Encountered invalid state machine name group.")

    def translate_state_machine_scope(self, d: Dict[str, dict]) -> StateMachineScope:
        scope = StateMachineScope()
        for name_group_str, scope_map in d.items():
            name_group = self.translate_state_machine_name_group(name_group_str)
            inner_map: Dict[str, dict] = scope_map["map"]
            for name, inner_dict in inner_map.items():
                symbol_type = next(iter(inner_dict))
                symbol_id = inner_dict[symbol_type]["nodeId"]
                symbol = self.translate_state_machine_symbol(symbol_type, symbol_id)
                scope = scope.put(name_group, symbol.get_unqualified_name(), symbol)
        return scope

    def translate_state_machine_scope_map(
        self, d: Dict[str, dict]
    ) -> Dict[AstId, StateMachineScope]:
        symbol_scope_map: Dict[AstId, StateMachineScope] = dict()
        for id, inner_dict in d.items():
            symbol_scope_map[AstId(id)] = self.translate_state_machine_scope(
                inner_dict["map"]
            )

        return symbol_scope_map

    def translate_state_or_choice(self, d: Dict[str, dict]) -> StateOrChoice:
        soc = next(iter(d))
        if soc == "Choice":
            choice_a_node = self.get_annotated_ast_node_by_id(
                d[soc]["symbol"]["node"]["astNodeId"]
            )
            return Choice(ChoiceSymbol(choice_a_node))
        elif soc == "State":
            state_a_node = self.get_annotated_ast_node_by_id(
                d[soc]["symbol"]["node"]["astNodeId"]
            )
            return State(StateSymbol(state_a_node))
        else:
            raise InternalError("Invalid state or choice JSON")

    def translate_transition_graph_node(
        self, d: Dict[str, dict]
    ) -> TransitionGraphNode:
        return TransitionGraphNode(self.translate_state_or_choice(d["soc"]))

    def translate_arc_set(self, l: List[Dict]) -> Set[Arc]:
        arc_set: Set[Arc] = set()
        for a in l:
            key = next(iter(a))
            if key == "State":
                arc_set.add(
                    StateArc(
                        self.require_type(
                            self.translate_state_machine_symbol(
                                "State", a[key]["startState"]["node"]["astNodeId"]
                            ),
                            StateSymbol,
                        ),
                        self.get_annotated_ast_node_by_id(a[key]["aNode"]["astNodeId"]),
                        self.translate_transition_graph_node(a[key]["endNode"]),
                    )
                )
            elif key == "Choice":
                arc_set.add(
                    ChoiceArc(
                        self.require_type(
                            self.translate_state_machine_symbol(
                                "Choice", a[key]["startChoice"]["node"]["astNodeId"]
                            ),
                            ChoiceSymbol,
                        ),
                        self.get_annotated_ast_node_by_id(a[key]["aNode"]["astNodeId"])[
                            1
                        ],
                        self.translate_transition_graph_node(a[key]["endNode"]),
                    )
                )
            elif key == "Initial":
                arc_set.add(
                    InitialArc(
                        self.require_type(
                            self.translate_state_machine_symbol(
                                "State", a[key]["startState"]["node"]["astNodeId"]
                            ),
                            StateSymbol,
                        ),
                        self.get_annotated_ast_node_by_id(a[key]["aNode"]["astNodeId"]),
                        self.translate_transition_graph_node(a[key]["endNode"]),
                    )
                )
            else:
                raise InvalidFppToJsonField(key)

        return arc_set

    def translate_arc_map(self, d: Dict[str, list]) -> ArcMap:
        arc_map: ArcMap = dict()
        for name, inner_list in d.items():
            arc_map[name] = self.translate_arc_set(inner_list)

        return arc_map

    def translate_transition_graph(self, d: Dict[str, dict]) -> TransitionGraph:
        return TransitionGraph(
            self.translate_optional(
                d["initialNode"], self.translate_transition_graph_node
            ),
            self.translate_arc_map(d["arcMap"]),
        )

    def translate_type_option_map(
        self, d: Dict[str, dict]
    ) -> Dict[StateMachineTypedElement, Optional[Type]]:
        out_dict: Dict[StateMachineTypedElement, Optional[Type]] = dict()
        for id, inner_dict in d.items():
            a_node = self.get_annotated_ast_node_by_id(AstId(id))
            data = a_node[1].data
            translated_type = self.translate_optional(inner_dict, self.translate_type)
            if isinstance(data, fpp_ast.SpecStateEntry):
                out_dict[StateEntryTypedElement(a_node)] = translated_type
            elif isinstance(data, fpp_ast.SpecStateExit):
                out_dict[StateExitTypedElement(a_node)] = translated_type
            elif isinstance(data, fpp_ast.SpecInitialTransition):
                out_dict[InitialTransitionTypedElement(a_node)] = translated_type
            elif isinstance(data, fpp_ast.SpecStateTransition):
                out_dict[StateTransitionTypedElement(a_node)] = translated_type
            elif isinstance(data, fpp_ast.DefChoice):
                out_dict[ChoiceTypedElement(a_node)] = translated_type
            else:
                raise InternalError("Invalid type option JSON")
        return out_dict

    def translate_action_symbol_list(
        self, l: List[Dict[str, dict]]
    ) -> List[ActionSymbol]:
        out_list: List[ActionSymbol] = []
        for i in l:
            a_node = self.get_annotated_ast_node_by_id(i["node"]["astNodeId"])
            out_list.append(ActionSymbol(a_node))
        return out_list

    def translate_transition(self, d: Dict[str, dict]) -> Transition:
        transition_kind = next(iter(d))
        if transition_kind == "External":
            return ExternalTransition(
                actions=self.translate_action_symbol_list(
                    d[transition_kind]["actions"]
                ),
                target=self.translate_state_or_choice(d[transition_kind]["target"]),
            )
        elif transition_kind == "Internal":
            return InternalTransition(
                actions=self.translate_action_symbol_list(
                    d[transition_kind]["actions"]
                ),
            )
        elif transition_kind == "Guarded":
            guard_opt: Optional[GuardSymbol] = None
            if "Some" in d[transition_kind]["guardOpt"]:
                guard_a_node = self.get_annotated_ast_node_by_id(
                    d[transition_kind]["guardOpt"]["Some"]["node"]["astNodeId"]
                )
                guard_opt = GuardSymbol(guard_a_node)
            return GuardedTransition(
                guard_opt=guard_opt,
                transition=self.translate_transition(d[transition_kind]["transition"]),
            )
        else:
            raise InvalidFppToJsonField(transition_kind)

    def translate_flattened_state_transition_map(
        self, d: Dict[str, dict]
    ) -> SignalStateTransitionMap:
        out_dict: SignalStateTransitionMap = dict()
        for id, inner_dict in d.items():
            a_node = self.get_annotated_ast_node_by_id(AstId(id))
            signal_symbol = SignalSymbol(a_node)
            state_transition_map: StateTransitionMap = dict()
            for state_id, guarded_transition_dict in inner_dict.items():
                guard_opt: Optional[GuardSymbol] = None
                if "Some" in guarded_transition_dict["guardOpt"]:
                    guard_a_node = self.get_annotated_ast_node_by_id(
                        guarded_transition_dict["guardOpt"]["Some"]["node"]["astNodeId"]
                    )
                    guard_opt = GuardSymbol(guard_a_node)
                transition = self.translate_transition(
                    guarded_transition_dict["transition"]
                )
                state_transition_map[AstId(state_id)] = GuardedTransition(
                    guard_opt, transition
                )
            out_dict[signal_symbol.get_node_id()] = state_transition_map
        return out_dict

    def translate_flattened_choice_transition_map(
        self, d: Dict[str, dict]
    ) -> TransitionExprMap:
        out_dict: TransitionExprMap = dict()
        for id, inner_dict in d.items():
            a_node = self.get_annotated_ast_node_by_id(AstId(id))
            out_dict[a_node[1].get_id()] = self.translate_transition(inner_dict)
        return out_dict

    def translate_state_machine_analysis(
        self, d: Dict[str, dict]
    ) -> StateMachineAnalysis:
        sm_a_node = self.get_annotated_ast_node_by_id(
            int(d["symbol"]["node"]["astNodeId"])
        )
        return StateMachineAnalysis(
            symbol=StateMachineSymbol(sm_a_node),
            symbol_scope_map=self.translate_state_machine_scope_map(
                d["symbolScopeMap"]
            ),
            use_def_map=self.translate_state_machine_use_def_map(d["useDefMap"]),
            transition_graph=self.translate_transition_graph(d["transitionGraph"]),
            reverse_transition_graph=self.translate_transition_graph(
                d["reverseTransitionGraph"]
            ),
            type_option_map=self.translate_type_option_map(d["typeOptionMap"]),
            flattened_state_transition_map=self.translate_flattened_state_transition_map(
                d["flattenedStateTransitionMap"]
            ),
            flattened_choice_transition_map=self.translate_flattened_choice_transition_map(
                d["flattenedChoiceTransitionMap"]
            ),
        )

    def translate_state_machine(self, d: Dict[str, dict]) -> StateMachine:
        a_node = self.get_annotated_ast_node_by_id(int(d["aNode"]["astNodeId"]))
        return StateMachine(
            a_node=a_node,
            sma=self.translate_state_machine_analysis(d["sma"]),
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

    def translate_component_instance_map(
        self, d: Dict[str, dict]
    ) -> Dict[AstId, ComponentInstance]:
        out_dict: Dict[AstId, ComponentInstance] = dict()
        for id, inner_dict in d.items():
            out_dict[AstId(id)] = self.translate_component_instance(inner_dict)
        return out_dict

    def translate_topology_map(self, d: Dict[str, dict]) -> Dict[AstId, Topology]:
        out_dict: Dict[AstId, Topology] = dict()
        for id, inner_dict in d.items():
            out_dict[AstId(id)] = self.translate_topology(inner_dict)
        return out_dict

    def translate_interface_map(self, d: Dict) -> Dict[AstId, Interface]:
        out_dict: Dict[AstId, Interface] = dict()
        for id, inner_dict in d.items():
            out_dict[AstId(id)] = self.translate_interface(inner_dict)
        return out_dict

    def translate_state_machine_map(self, d: Dict) -> Dict[AstId, StateMachine]:
        out_dict: Dict[AstId, StateMachine] = dict()
        for id, inner_dict in d.items():
            out_dict[AstId(id)] = self.translate_state_machine(inner_dict)
        return out_dict

    def translate_framework_definitions(self, d: Dict) -> FrameworkDefinitions:
        return FrameworkDefinitions()

    def translate_analysis_json(self) -> Analysis:
        if not os.path.exists(self.analysis_json_file):
            raise FileNotFoundError(f'File "{self.analysis_json_file}" not found')
        with open(self.analysis_json_file, "r") as f:
            data: Dict = json.load(f)
            data = data["analysis"]
            self.component_map = self.translate_component_map(
                self.require_type(data.get("componentMap"), dict)
            )
            self.component_instance_map = self.translate_component_instance_map(
                self.require_type(data.get("componentInstanceMap"), dict)
            )
            return Analysis(
                input_file_set=self.translate_file_set(
                    self.require_type(data.get("inputFileSet"), list)
                ),
                included_file_set=self.translate_file_set(
                    self.require_type(data.get("includedFileSet"), list)
                ),
                location_specifier_map=self.translate_location_specifier_map(
                    self.require_type(data.get("locationSpecifierMap"), list)
                ),
                parent_symbol_map=self.translate_parent_symbol_map(
                    self.require_type(data.get("parentSymbolMap"), dict)
                ),
                use_def_map=self.translate_use_def_map(
                    self.require_type(data.get("useDefMap"), dict)
                ),
                symbol_scope_map=self.translate_symbol_scope_map(
                    self.require_type(data.get("symbolScopeMap"), dict)
                ),
                type_map=self.translate_type_map(
                    self.require_type(data.get("typeMap"), dict)
                ),
                value_map=self.translate_value_map(
                    self.require_type(data.get("valueMap"), dict)
                ),
                component_map=self.component_map,
                component_instance_map=self.component_instance_map,
                topology_map=self.translate_topology_map(
                    self.require_type(data.get("topologyMap"), dict)
                ),
                interface_map=self.translate_interface_map(
                    self.require_type(data.get("interfaceMap"), dict)
                ),
                state_machine_map=self.translate_state_machine_map(
                    self.require_type(data.get("stateMachineMap"), dict)
                ),
                # framework_definitions=self.translate_framework_definitions(
                #     self.require_type(data.get("frameworkDefinitions"), dict)
                # )
            )
