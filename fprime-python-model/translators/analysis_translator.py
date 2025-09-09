import json
from typing import Dict, List, Set
import os
from fpp_ast import *
from fpp_ast_node import AstId
from pathlib import Path
from semantics.analysis import Analysis
from semantics.symbol import *
from semantics.scope import Scope
from semantics.name_group import NameGroup
from semantics.types_values import Type, Value, BooleanType, FloatType, IntType, StringType, \
    FloatKind, IntegerType, PrimitiveIntType, PrimitiveIntKind, EnumType, EnumConstantValue, \
    ArrayType, AnonArrayType, ArrayValue, AnonArrayValue, FloatValue, StringValue, IntegerValue, \
    PrimitiveIntValue, StructValue, BooleanValue, AbsTypeValue, AbsType, StructType, AnonStructType, \
    AnonStructValue, StructMembersValue, StructMembersType
from error import InvalidFppToJsonField

class AnalysisTranslator:    
    """
    Translates the JSON representation of an FPP analysis to an Analysis Python data structure.
    """

    def __init__(self, ast_map: Dict[AstId, Annotated[AstNode]], analysis_json_file: str):
        self.ast_map: Dict[AstId, Annotated[AstNode]] = ast_map
        self.analysis_json_file: str = analysis_json_file

    def translate_input_file_set(self, l: List[str]) -> Set[Path]:
        out_set: Set[Path] = set()
        for i in l:
            out_set.add(Path(str(i)))
        return out_set
    
    def translate_symbol(self, symbol_type: str, node_id: AstId) -> Symbol:
        match symbol_type:
            case "AbsType":
                return AbsTypeSymbol(self.ast_map[node_id])
            case "AliasType":
                return AliasTypeSymbol(self.ast_map[node_id])
            case "Array":
                return ArraySymbol(self.ast_map[node_id])
            case "Component":
                return ComponentSymbol(self.ast_map[node_id])
            case "ComponentInstance":
                return ComponentInstanceSymbol(self.ast_map[node_id])
            case "Constant":
                return ConstantSymbol(self.ast_map[node_id])
            case "Enum":
                return EnumSymbol(self.ast_map[node_id])
            case "EnumConstant":
                return EnumConstantSymbol(self.ast_map[node_id])
            case "Interface":
                return InterfaceSymbol(self.ast_map[node_id])
            case "Module":
                return ModuleSymbol(self.ast_map[node_id])
            case "Port":
                return PortSymbol(self.ast_map[node_id])
            case "StateMachine":
                return StateMachineSymbol(self.ast_map[node_id])
            case "Struct":
                return StructSymbol(self.ast_map[node_id])
            case "Topology":
                return TopologySymbol(self.ast_map[node_id])
            case _:
                raise InvalidFppToJsonField(symbol_type)
            
    def get_symbol_type_from_node(self, a_node: Annotated[AstNode[T]]) -> str:
        _, node, _ = a_node
        data = node.data
        match data:
            case DefAbsType():
                return "AbsType"
            case DefAliasType():
                return "AliasType"
            case DefArray():
                return "Array"
            case DefComponent():
                return "Component"
            case DefComponentInstance():
                return "ComponentInstance"
            case DefConstant():
                return "Constant"
            case DefEnum():
                return "Enum"
            case DefEnumConstant():
                return "EnumConstant"
            case DefInterface():
                return "Interface"
            case DefModule():
                return "Module"
            case DefPort():
                return "Port"
            case DefStateMachine():
                return "StateMachine"
            case DefStruct():
                return "Struct"
            case DefTopology():
                return "Topology"
            case _:
                raise InternalError("Could not determine symbol for AST node")

    def translate_parent_symbol_map(self, d: Dict[str, dict]) -> Dict[AstId, Symbol]:
        out_dict: Dict[AstId, Symbol] = dict()
        for child_id, inner_dict in d.items():
            parent_symbol_type = next(iter(inner_dict))
            parent_id = AstId(inner_dict[parent_symbol_type]["nodeId"])
            parent_symbol: Symbol = self.translate_symbol(parent_symbol_type, parent_id)
            child_symbol: Symbol = self.translate_symbol(self.get_symbol_type_from_node(self.ast_map[AstId(child_id)]), AstId(child_id))
            out_dict[child_symbol.get_node_id()] = parent_symbol # TODO update so the symbol can be the key in the dictionary
        return out_dict
    
    def translate_use_def_map(self, d: Dict[str, dict]) -> Dict[AstId, Symbol]:
        out_dict: Dict[AstId, Symbol] = dict()
        for use_id, inner_dict in d.items():
            def_symbol_type = next(iter(inner_dict))
            def_id = AstId(inner_dict[def_symbol_type]["nodeId"])
            def_symbol: Symbol = self.translate_symbol(def_symbol_type, def_id)
            out_dict[AstId(use_id)] = def_symbol # TODO update so the symbol can be the key in the dictionary
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
            case "Bool":
                return BooleanType()
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
            
    def translate_enum_constant_value(self, d: Dict) -> EnumConstantValue:
        unqual_name, val = d["value"][0], d["value"][1]
        return EnumConstantValue((unqual_name, val), self.translate_enum_type(d["t"]))
            
    def translate_enum_type(self, d: Dict) -> EnumType:
        node = self.ast_map[AstId(d["node"]["astNodeId"])]
        kind = self.translate_primitive_int_kind(next(iter(d["repType"]["kind"])))
        rep_type = PrimitiveIntType(kind)
        default = None
        if "Some" in d["default"]:
            default = self.translate_enum_constant_value(d["default"]["Some"])
        return EnumType(node, rep_type, default)
    
    def translate_abs_type(self, d: Dict[str, dict]) -> AbsType:
        node = self.ast_map[AstId(d["node"]["astNodeId"])]
        return AbsType(node)
    
    def translate_anon_array_type(self, d: Dict[str, dict]) -> AnonArrayType:
        size = None
        if "Some" in d["size"]:
            size = int(d["size"]["Some"])
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
            self.translate_array_type(d["t"])
        )
    
    def translate_array_type(self, d: Dict[str, dict]) -> ArrayType:
        node = self.ast_map[AstId(d["node"]["astNodeId"])]
        anon_array = self.translate_anon_array_type(d["anonArray"])
        default = None
        if "Some" in d["default"]:
            default = self.translate_array_value(d["default"]["Some"])
        return ArrayType(node, anon_array, default)
    
    def translate_string_type(self, d: Dict[str, dict]) -> StringType:
        size = None
        if "Some" in d["size"]:
            size = fpp_ast.ExprLiteralInt(d["size"]["Some"]) # TODO verify this
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
            self.translate_struct_type(d["t"])
        )

    def translate_struct_type(self, d: Dict[str, dict]) -> StructType:
        node = self.ast_map[AstId(d["node"]["astNodeId"])]
        anon_struct_type = self.translate_anon_struct_type(d["anonStruct"])
        default = None
        if "Some" in d["default"]:
            default = self.translate_struct_value(d["default"]["Some"])
        sizes = None
        if "Some" in d["sizes"]:
            sizes = None
            # sizes = fpp_ast.ExprLiteralInt(d["sizes"]["Some"]) # TODO verify this
        formats = None
        if "Some" in d["formats"]:
            formats = None
            # formats = d["formats"]["Some"] # TODO verify this
        return StructType(node, anon_struct_type, default, sizes, formats)
    
    def translate_primitive_int_value(self, d: Dict[str, dict]) -> PrimitiveIntValue:
        if not isinstance(d["value"], int):
            raise TypeError(f"{d['value']} has an invalid type; expected int, actual {type(d['value'])}")
        value = d["value"]
        kind = self.translate_primitive_int_kind(next(iter(d["kind"])))
        return PrimitiveIntValue(value, kind)

    def translate_string_value(self, d: Dict[str, dict]) -> StringValue:
        if not isinstance(d["value"], str):
            raise TypeError(f"{d['value']} has an invalid type; expected string, actual {type(d['value'])}")
        return StringValue(d["value"])
    
    def translate_float_value(self, d: Dict[str, dict]) -> FloatValue:
        if not isinstance(d["value"], float):
            raise TypeError(f"{d['value']} has an invalid type; expected float, actual {type(d['value'])}")
        value = float(d["value"])
        kind = self.translate_float_kind(next(iter(d["kind"])))
        return FloatValue(value, kind)
    
    def translate_abs_type_value(self, d: Dict[str, dict]) -> AbsTypeValue:
        return AbsTypeValue(self.translate_abs_type(d["t"]))

    def translate_value(self, d: Dict[str, dict]) -> Value:
        v_type = next(iter(d))
        match v_type:
            case "Int":
                return self.translate_primitive_int_value(d[v_type]["PrimitiveInt"])
            case "PrimitiveInt":
                return self.translate_primitive_int_value(d[v_type])
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
            case _:
                raise InternalError(f"Translation not implemented for {v_type}")
    
    def translate_type(self, d: Dict[str, dict]) -> Type:
        t_type = next(iter(d))
        match t_type:
            case "Primitive":
                return self.translate_primitive_type(d[t_type])
            case "Int":
                return self.translate_int_type(d[t_type])
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
            case _:
                raise InternalError(f"Translation not implemented for type {t_type}")

    def translate_type_map(self, d: Dict[str, dict]) -> Dict[AstId, Type]:
        out_dict: Dict[AstId, Type] = dict()
        for id, inner_dict in d.items():
            out_dict[AstId(id)] = self.translate_type(inner_dict)
        return out_dict


    def translate_analysis_json(self) -> Analysis:
        if not os.path.exists(self.analysis_json_file):
            raise FileNotFoundError(f'File "{self.analysis_json_file}" not found')
        with open(self.analysis_json_file, "r") as f:
            data: Dict = json.load(f)
            return Analysis(
                included_file_set=self.translate_input_file_set(data.get("inputFileSet")),
                parent_symbol_map=self.translate_parent_symbol_map(data.get("parentSymbolMap")),
                use_def_map=self.translate_use_def_map(data.get("useDefMap")),
                symbol_scope_map=self.symbol_scope_translator(data.get("symbolScopeMap")),
                type_map=self.translate_type_map(data.get("typeMap"))
            )
            
