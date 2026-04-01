from typing import Optional, List, Dict, Generic, TypeVar, Tuple, TypeAlias, Callable
from abc import ABC, abstractmethod
from enum import Enum
from fprime_python_model.utils.error import InternalError
from fprime_python_model.fpp_ast.fpp_ast_node import AstNode, AstId
from fprime_python_model.fpp_ast import fpp_ast
from fprime_python_model.semantics.symbol import (
    TypeSymbol,
    AbsTypeSymbol,
    AliasTypeSymbol,
    ArraySymbol,
    EnumSymbol,
    StructSymbol,
)
from dataclasses import dataclass
from fprime_python_model.semantics.format import Format
import math


class Type(ABC):
    """An FPP Type"""

    @abstractmethod
    def get_default_value(self) -> Optional["Value"]:
        """Get the default value"""
        pass

    def get_array_size(self) -> Optional[int]:
        """Get the array size"""
        return None

    def get_def_node_id(self) -> Optional[AstId]:
        """Get the definition node identifier, if any"""
        symbol: Optional[TypeSymbol] = self.get_def_symbol()
        return symbol.get_node_id() if symbol is not None else None

    def get_def_symbol(self) -> Optional[TypeSymbol]:
        """Get the definition symbol, if any"""
        return None

    def get_underlying_type(self) -> "Type":
        """Get the underlying type"""
        return self

    def has_numeric_members(self) -> bool:
        """Does this type have numeric members?"""
        return self.is_numeric()

    def is_convertible_to_numeric(self) -> bool:
        """Is this type convertible to a numeric type?"""
        return self.is_numeric()

    def is_promotable_to_array(self) -> bool:
        """Is this type promotable to an array type?"""
        return self.is_numeric()

    def is_displayable(self) -> bool:
        """Is this type displayable?"""
        return False

    def is_float(self) -> bool:
        """Is this type a float type?"""
        return False

    def is_int(self) -> bool:
        """Is this type an int type?"""
        return False

    def is_primitive(self) -> bool:
        """Is this type a primitive type?"""
        return False

    def is_canonical(self) -> bool:
        """Is this type a canonical (non-aliased) type?"""
        return True

    def is_promotable_to_struct(self) -> bool:
        """Is this type promotable to a struct type?"""
        return self.is_promotable_to_array()

    def is_numeric(self) -> bool:
        """Is this type numeric?"""
        return self.is_int() or self.is_float()


class Signedness(Enum):
    SIGNED = "signed"
    UNSIGNED = "unsigned"


class PrimitiveIntKind(Enum):
    I8 = "I8"
    I16 = "I16"
    I32 = "I32"
    I64 = "I64"
    U8 = "U8"
    U16 = "U16"
    U32 = "U32"
    U64 = "U64"


class IntType(Type):
    """Integer types"""

    def is_int(self) -> bool:
        return True


class PrimitiveType(Type):
    """Primitive types"""

    def is_primitive(self) -> bool:
        return True

    def bit_width(self) -> int:
        raise NotImplementedError("Subclasses must implement bit_width")


@dataclass
class PrimitiveIntType(PrimitiveType, IntType):
    """Primitive integer types"""

    def __init__(self, kind: PrimitiveIntKind):
        self.kind = kind

    def get_default_value(self) -> Optional["PrimitiveIntValue"]:
        return PrimitiveIntValue(0, self.kind)

    def is_displayable(self) -> bool:
        return True

    def bit_width(self) -> int:
        return {
            PrimitiveIntKind.I8: 8,
            PrimitiveIntKind.I16: 16,
            PrimitiveIntKind.I32: 32,
            PrimitiveIntKind.I64: 64,
            PrimitiveIntKind.U8: 8,
            PrimitiveIntKind.U16: 16,
            PrimitiveIntKind.U32: 32,
            PrimitiveIntKind.U64: 64,
        }[self.kind]

    def signedness(self) -> Signedness:
        if self.kind in {
            PrimitiveIntKind.I8,
            PrimitiveIntKind.I16,
            PrimitiveIntKind.I32,
            PrimitiveIntKind.I64,
        }:
            return Signedness.SIGNED
        else:
            return Signedness.UNSIGNED

    def __str__(self) -> str:
        return self.kind.name


class FloatKind(Enum):
    F32 = "F32"
    F64 = "F64"

    def __str__(self):
        return self.value


@dataclass
class FloatType(PrimitiveType):
    def __init__(self, kind: FloatKind):
        self.kind = kind

    def get_default_value(self):
        return FloatValue(0, self.kind)

    def is_float(self):
        return True

    def is_displayable(self):
        return True

    def __str__(self):
        return str(self.kind)

    def bit_width(self):
        if self.kind == FloatKind.F32:
            return 32
        elif self.kind == FloatKind.F64:
            return 64
        else:
            raise InternalError("Invalid float kind")


@dataclass
class BooleanType(PrimitiveType):
    def bit_width(self):
        return 1

    def get_default_value(self):
        return BooleanValue(False)

    def __str__(self):
        return "bool"

    def is_promotable_to_array(self):
        return True

    def is_displayable(self):
        return True


@dataclass
class StringType(Type):
    def __init__(self, size: Optional[AstNode[fpp_ast.Expr]] = None):
        self.size = size

    def get_default_value(self):
        return StringValue("")

    def __str__(self):
        return "string"

    def is_promotable_to_array(self):
        return True

    def is_displayable(self):
        return True


@dataclass
class IntegerType(IntType):
    def get_default_value(self):
        return IntegerValue(0)

    def __str__(self):
        return "Integer"


@dataclass
class AbsType(Type):
    def __init__(self, node: fpp_ast.Annotated[AstNode[fpp_ast.DefAbsType]]):
        self.node = node

    def get_default_value(self):
        return AbsTypeValue(self)

    def get_def_node_id(self):
        return self.node[1]._id

    def get_def_symbol(self):
        return AbsTypeSymbol(self.node)

    def __str__(self):
        return str(self.node[1].data.name)


class AliasType(Type):
    def __init__(
        self, node: fpp_ast.Annotated[AstNode[fpp_ast.DefAliasType]], alias_type: Type
    ):
        self.node = node
        self.alias_type = alias_type

    def get_default_value(self):
        return self.alias_type.get_default_value()

    def get_def_node_id(self):
        return self.node[1]._id

    def get_def_symbol(self):
        return AliasTypeSymbol(self.node)

    def __str__(self):
        return str(self.node[1].data.name)

    def is_canonical(self):
        return False

    def is_displayable(self):
        return self.get_underlying_type().is_displayable()

    def get_underlying_type(self):
        return self.alias_type.get_underlying_type()


class ArrayType(Type):
    def __init__(
        self,
        node: fpp_ast.Annotated[AstNode[fpp_ast.DefArray]],
        anon_array: "AnonArrayType",
        default: Optional["ArrayValue"] = None,
        format: Optional[Format] = None,
    ):
        self.node = node
        self.anon_array = anon_array
        self.default = default
        self.format = format

    __match_args__ = ("node", "anon_array", "default", "format")

    def get_default_value(self) -> Optional["ArrayValue"]:
        return self.default

    def get_array_size(self) -> Optional[int]:
        return self.anon_array.get_array_size()

    def get_def_node_id(self) -> Optional[AstId]:
        return self.node[1]._id

    def get_def_symbol(self):
        return ArraySymbol(self.node)

    def has_numeric_members(self) -> bool:
        return self.anon_array.has_numeric_members()

    def is_displayable(self) -> bool:
        return self.anon_array.elt_type.is_displayable()

    def __str__(self) -> str:
        return f"array {self.node[1].data.name}"


class EnumType(Type):
    def __init__(
        self,
        node: fpp_ast.Annotated[AstNode[fpp_ast.DefEnum]],
        rep_type: PrimitiveIntType,
        default: Optional["EnumConstantValue"] = None,
    ):
        self.node = node
        self.rep_type = rep_type
        self.default = default

    def get_default_value(self) -> Optional["EnumConstantValue"]:
        return self.default

    def get_def_node_id(self) -> Optional[AstId]:
        return self.node[1]._id

    def get_def_symbol(self):
        return EnumSymbol(self.node)

    def is_convertible_to_numeric(self) -> bool:
        return True

    def is_promotable_to_array(self) -> bool:
        return True

    def is_displayable(self) -> bool:
        return True

    def __str__(self) -> str:
        return f"enum {self.node[1].data.name}"


StructMembersType: TypeAlias = Dict[fpp_ast.Unqualified, Type]


class StructType(Type):
    def __init__(
        self,
        node: fpp_ast.Annotated[AstNode[fpp_ast.DefStruct]],
        anon_struct: "AnonStructType",
        default: Optional["StructValue"] = None,
        sizes: Dict[fpp_ast.Unqualified, int] = dict(),
        formats: Dict[fpp_ast.Unqualified, Format] = dict(),
    ):
        self.node = node
        self.anon_struct = anon_struct
        self.default = default
        self.sizes = sizes if sizes is not None else {}
        self.formats = formats if formats is not None else {}

    __match_args__ = ("node", "anon_struct", "default", "sizes", "formats")

    def get_default_value(self) -> Optional["StructValue"]:
        return self.default

    def get_def_node_id(self) -> Optional[AstId]:
        return self.node[1]._id

    def get_def_symbol(self):
        return StructSymbol(self.node)

    def has_numeric_members(self) -> bool:
        return self.anon_struct.has_numeric_members()

    def is_displayable(self) -> bool:
        return all(
            member.is_displayable() for member in self.anon_struct.members.values()
        )

    def __str__(self) -> str:
        return f"struct {self.node[1].data.name}"


class AnonArrayType(Type):
    def __init__(self, size: Optional[int], elt_type: Type):
        self.size = size
        self.elt_type = elt_type

    __match_args__ = ("size", "elt_type")

    def set_size(self, size: int) -> "AnonArrayType":
        return AnonArrayType(size=size, elt_type=self.elt_type)

    def get_default_value(self) -> Optional["AnonArrayValue"]:
        default_value = self.elt_type.get_default_value()
        if self.size is not None and default_value is not None:
            elts: List[Value] = [default_value] * self.size
            return AnonArrayValue(elts)
        return None

    def get_array_size(self) -> Optional[int]:
        return self.size

    def has_numeric_members(self) -> bool:
        return self.elt_type.has_numeric_members()

    def __str__(self) -> str:
        if self.size is not None:
            return f"[{self.size}] {self.elt_type}"
        else:
            return f"array of {self.elt_type}"


class AnonStructType(Type):
    def __init__(self, members: StructMembersType):
        self.members: StructMembersType = members

    __match_args__ = "members"

    def get_default_value(self) -> Optional["AnonStructValue"]:
        out: StructMembersValue = {}
        for member_name, member_type in self.members.items():
            value = member_type.get_default_value()
            if value is None:
                return None
            out[member_name] = value
        return AnonStructValue(out)

    def has_numeric_members(self) -> bool:
        return all(member.has_numeric_members() for member in self.members.values())

    def __str__(self) -> str:
        if not self.members:
            return "{ }"
        member_strs = [f"{name}: {typ}" for name, typ in self.members.items()]
        return f"{{ {', '.join(member_strs)} }}"


T = TypeVar("T")


class Value(ABC):
    def __init__(self):
        pass

    def __add__(self, other: "Value") -> Optional["Value"]:
        def int_op(v1: int, v2: int) -> int:
            return v1 + v2

        def double_op(v1: float, v2: float) -> float:
            return v1 + v2

        return self.binop(Binop(int_op, double_op), other)

    def __truediv__(self, other: "Value") -> Optional["Value"]:
        def int_op(v1: int, v2: int) -> int:
            return v1 // v2

        def double_op(v1: float, v2: float) -> float:
            return v1 / v2

        return self.binop(Binop(int_op, double_op), other)

    def __mul__(self, other: "Value") -> Optional["Value"]:
        def int_op(v1: int, v2: int) -> int:
            return v1 * v2

        def double_op(v1: float, v2: float) -> float:
            return v1 * v2

        return self.binop(Binop(int_op, double_op), other)

    def __neg__(self) -> Optional["Value"]:
        return None

    def is_zero(self) -> bool:
        return False

    def binop(self, op: "Binop", other: "Value") -> Optional["Value"]:
        return None

    @abstractmethod
    def get_type(self) -> Type:
        pass


class PrimitiveIntValue(Value):
    def __init__(self, value: int, kind: PrimitiveIntKind):
        self.value = value
        self.kind = kind

    def get_type(self) -> "Type":
        return PrimitiveIntType(self.kind)

    def is_zero(self) -> bool:
        return self.value == 0

    def __str__(self):
        return f"{self.value}: {self.kind}"

    def __neg__(self) -> "PrimitiveIntValue":
        return PrimitiveIntValue(-self.value, self.kind)


class IntegerValue(Value):
    def __init__(self, value: int):
        self.value = value

    def fits_in_u64_width(self) -> bool:
        u64_bound = 1 << 64
        return (-(u64_bound // 2)) <= self.value < u64_bound

    def get_type(self) -> "Type":
        return IntegerType()

    def is_zero(self) -> bool:
        return self.value == 0

    def __str__(self):
        return str(self.value)

    def __neg__(self) -> Optional["IntegerValue"]:
        return IntegerValue(-self.value)


class FloatValue(Value):

    def __init__(self, value: float, kind: FloatKind):
        self.value = value
        self.kind = kind

    def is_zero(self) -> bool:
        return math.fabs(self.value) <= 0

    def get_type(self) -> "Type":
        return FloatType(self.kind)

    def __str__(self) -> str:
        return f"{self.value}: {self.kind}"

    def __neg__(self) -> "FloatValue":
        return FloatValue(-self.value, self.kind)


class BooleanValue(Value):
    def __init__(self, value: bool):
        self.value = value

    def get_type(self) -> "Type":
        return BooleanType()

    def __str__(self) -> str:
        return str(self.value)


class StringValue(Value):
    def __init__(self, value: str):
        self.value = value

    def get_type(self) -> "Type":
        return StringType(None)

    def __str__(self) -> str:
        return f'"{self.value}"'


class AnonArrayValue(Value):
    def __init__(self, elements: List[Value]):
        self.elements = elements

    def get_type(self) -> "Type":
        size = len(self.elements)
        elt_type = self.elements[0].get_type()
        return AnonArrayType(size, elt_type)

    def __str__(self) -> str:
        return "[ " + ", ".join(str(e) for e in self.elements) + " ]"


class AbsTypeValue(Value):
    def __init__(self, t: AbsType):
        self.t = t

    def get_type(self) -> AbsType:
        return self.t

    def __str__(self) -> str:
        return f"value of type {self.t}"


class ArrayValue(Value):
    def __init__(self, anon_array: AnonArrayValue, t: ArrayType):
        self.anon_array = anon_array
        self.t = t

    def get_type(self) -> ArrayType:
        return self.t

    def __str__(self) -> str:
        return f"{self.anon_array}: {self.t.node[1].data.name}"


class EnumConstantValue(Value):
    def __init__(self, value: Tuple[fpp_ast.Unqualified, int], t: EnumType):
        self.value = value
        self.t = t

    def get_type(self) -> "EnumType":
        return self.t

    def __str__(self) -> str:
        return f"{self.value}: {self.t.node[1].data.name}"


StructMembersValue: TypeAlias = Dict[fpp_ast.Unqualified, Value]


class AnonStructValue(Value):
    def __init__(self, members: StructMembersValue):
        self.members = members

    def get_type(self) -> AnonStructType:
        type_members: Dict[fpp_ast.Unqualified, Type] = dict()
        for name, val in self.members.items():
            type_members[name] = val.get_type()
        return AnonStructType(type_members)

    def __str__(self) -> str:
        if not self.members:
            return "{ }"
        else:
            member_strs = [f"{name} = {val}" for name, val in self.members.items()]
            return "{ " + ", ".join(member_strs) + " }"


class StructValue(Value):
    def __init__(self, anon_struct: AnonStructValue, t: StructType):
        self.anon_struct = anon_struct
        self.t = t

    def get_type(self) -> StructType:
        return self.t

    def __str__(self) -> str:
        type_name = (
            getattr(self.t.node[1].data, "name", "unknown")
            if hasattr(self.t, "node")
            else "unknown"
        )
        return f"{str(self.anon_struct)}: {type_name}"


class Binop(Generic[T]):
    def __init__(
        self,
        int_op: Callable[[int, int], int],
        double_op: Callable[[float, float], float],
    ):
        self.int_op = int_op
        self.double_op = double_op
