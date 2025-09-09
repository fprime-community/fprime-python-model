from typing import Optional, Union, List, Dict, Generic, TypeVar, Tuple, TypeAlias, Callable
from abc import ABC, abstractmethod
from enum import Enum
from error import InternalError
from fpp_ast_node import AstNode, AstId
import fpp_ast
from dataclasses import dataclass
import math

class Type(ABC):
    """An FPP Type"""

    @abstractmethod
    def get_default_value(self) -> Optional['Value']:
        """Get the default value"""
        pass

    def get_array_size(self) -> Optional[int]:
        """Get the array size"""
        return None

    def get_def_node_id(self) -> Optional[AstId]:
        """Get the definition node identifier, if any"""
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

    def is_convertible_to(self, other: "Type") -> bool:
        """Is this type convertible to another type?"""
        return may_be_converted((self, other))

    @staticmethod
    def may_be_converted(type_pair: tuple["Type", "Type"]) -> bool:
        """
        Determine whether a type may be converted to another.
        This is a placeholder implementation — override or replace as needed.
        """
        # Implement conversion rules here
        source, target = type_pair
        return source.is_numeric() and target.is_numeric()


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

    def get_default_value(self) -> Optional['PrimitiveIntValue']:
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

    def __str__(self):
        return str(self.node[1].data.name)


class AliasType(Type):
    def __init__(
        self,
        node: fpp_ast.Annotated[AstNode[fpp_ast.DefAliasType]],
        alias_type: Type
    ):
        self.node = node
        self.alias_type = alias_type

    def get_default_value(self):
        return self.alias_type.get_default_value()

    def get_def_node_id(self):
        return self.node[1]._id

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
        anon_array: 'AnonArrayType',
        default: Optional['ArrayValue'] = None,
        # format_: Optional['Format'] = None,
        format = None
    ):
        self.node = node
        self.anon_array = anon_array
        self.default = default
        self.format = format

    __match_args__ = ('node', 'anon_array', 'default', 'format')

    def get_default_value(self) -> Optional['ArrayValue']:
        return self.default

    def set_size(self, size: int) -> 'ArrayType':
        new_anon_array = self.anon_array.set_size(size)
        return ArrayType(
            node=self.node,
            anon_array=new_anon_array,
            default=self.default,
            format=self.format,
        )

    def get_array_size(self) -> Optional[int]:
        return self.anon_array.get_array_size()

    def get_def_node_id(self) -> Optional[AstId]:
        return self.node[1]._id

    def has_numeric_members(self) -> bool:
        return self.anon_array.has_numeric_members()

    def is_displayable(self) -> bool:
        return self.anon_array.elt_type.is_displayable()

    def __str__(self) -> str:
        return f"array {self.node[1].data.name}"


def array_sizes_match(size1: Optional[int], size2: Optional[int]) -> bool:
    return (
        size1 is None or
        size2 is None or
        size1 == size2
    )


def common_array_size(size1: Optional[int], size2: Optional[int]) -> Optional[int]:
    if size1 is not None and size2 is not None and size1 == size2:
        return size1
    return None


class EnumType(Type):
    def __init__(
        self,
        node: fpp_ast.Annotated[AstNode[fpp_ast.DefEnum]],
        rep_type: PrimitiveIntType,
        default: Optional['EnumConstantValue'] = None
    ):
        self.node = node
        self.rep_type = rep_type
        self.default = default

    def get_default_value(self) -> Optional['EnumConstantValue']:
        return self.default

    def get_def_node_id(self) -> Optional[AstId]:
        return self.node[1]._id

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
        anon_struct: 'AnonStructType',
        default: Optional['StructValue'] = None,
        sizes: Dict[fpp_ast.Unqualified, int] = dict(),
        # formats: Dict[fpp_ast.Unqualified, 'Format'] = None
        formats = None
    ):
        self.node = node
        self.anon_struct = anon_struct
        self.default = default
        self.sizes = sizes if sizes is not None else {}
        self.formats = formats if formats is not None else {}

    __match_args__ = ('node', 'anon_struct', 'default', 'sizes', 'formats')


    def get_default_value(self) -> Optional['StructValue']:
        return self.default

    def get_def_node_id(self) -> Optional[AstId]:
        return self.node[1]._id

    def has_numeric_members(self) -> bool:
        return self.anon_struct.has_numeric_members()

    def is_displayable(self) -> bool:
        return all(member.is_displayable() for member in self.anon_struct.members.values())

    def __str__(self) -> str:
        return f"struct {self.node[1].data.name}"


class AnonArrayType(Type):
    def __init__(self, size: Optional[int], elt_type: Type):
        self.size = size
        self.elt_type = elt_type
    
    __match_args__ = ('size', 'elt_type')

    def set_size(self, size: int) -> 'AnonArrayType':
        return AnonArrayType(size=size, elt_type=self.elt_type)

    def get_default_value(self) -> Optional['AnonArrayValue']:
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

    __match_args__ = ('members')

    def get_default_value(self) -> Optional['AnonStructValue']:
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


def are_identical(t1: Type, t2: Type) -> bool:
    """Check for type identity."""
    def numeric():
        return (
            isinstance(t1, PrimitiveIntType) and isinstance(t2, PrimitiveIntType) and t1.kind == t2.kind or
            isinstance(t1, FloatType) and isinstance(t2, FloatType) and t1.kind == t2.kind or
            isinstance(t1, IntegerType) and isinstance(t2, IntegerType)
        )

    def boolean():
        return isinstance(t1, BooleanType) and isinstance(t2, BooleanType)

    def string():
        return (
            isinstance(t1, StringType) and isinstance(t2, StringType) and
            t1.size == t2.size
        )

    def same_def():
        return (
            t1.get_def_node_id() is not None and
            t2.get_def_node_id() is not None and
            t1.get_def_node_id() == t2.get_def_node_id()
        )

    return numeric() or boolean() or string() or same_def()


def may_be_converted(alias_pair: tuple[Type, Type]) -> bool:
    """Check for type convertibility."""
    t1 = alias_pair[0].get_underlying_type()
    t2 = alias_pair[1].get_underlying_type()

    assert t1.is_canonical()
    assert t2.is_canonical()

    def numeric():
        return t1.is_convertible_to_numeric() and t2.is_numeric()

    def string():
        return isinstance(t1, StringType) and isinstance(t2, StringType)

    def array():
        if isinstance(t1, ArrayType):
            return t1.anon_array.is_convertible_to(t2)
        elif isinstance(t2, ArrayType):
            return t1.is_convertible_to(t2.anon_array)
        elif isinstance(t1, AnonArrayType) and isinstance(t2, AnonArrayType):
            return (
                array_sizes_match(t1.size, t2.size) and
                t1.elt_type.is_convertible_to(t2.elt_type)
            )
        elif isinstance(t2, AnonArrayType):
            return t1.is_promotable_to_array() and t1.is_convertible_to(t2.elt_type)
        return False

    def struct():
        def member_exists_in(members: dict, member: tuple):
            name, member_type = member
            return name in members and member_type.is_convertible_to(members[name])

        if isinstance(t1, StructType):
            return t1.anon_struct.is_convertible_to(t2)
        elif isinstance(t2, StructType):
            return t1.is_convertible_to(t2.anon_struct)
        elif isinstance(t1, AnonStructType) and isinstance(t2, AnonStructType):
            return all(member_exists_in(t2.members, m) for m in t1.members.items())
        elif isinstance(t2, AnonStructType):
            return t1.is_promotable_to_struct and all(
                t1.is_convertible_to(t) for t in t2.members.values()
            )
        return False

    return (
        are_identical(t1, t2) or
        numeric() or
        string() or
        array() or
        struct()
    )

T = TypeVar('T')
Rule: TypeAlias = Callable[[], Optional[Type]]

def common_type(t1: Type, t2: Type) -> Optional[Type]:
    """Compute the common type for a pair of types."""
    pair = (t1, t2)

    def select_first_match_in(rules: List['Rule']) -> Optional[Type]:
        for rule in rules:
            result = rule()
            if result is not None:
                return result
        return None

    def identical() -> Optional[Type]:
        return t1 if are_identical(t1, t2) else None

    def alias() -> Optional[Type]:
        def get_ancestors(t: Type, ancs: List[Type] = []) -> List[Type]:
            if isinstance(t, AliasType):
                return get_ancestors(t.alias_type, [t] + ancs)
            else:
                return [t] + ancs

        def lca(a: Type, b: Type) -> Optional[Type]:
            ancestors_a = list(reversed(get_ancestors(a)))
            ancestors_b = list(reversed(get_ancestors(b)))
            for bi in ancestors_b:
                if any(are_identical(ai, bi) for ai in ancestors_a):
                    return bi
            return None

        if not t1.is_canonical() or not t2.is_canonical():
            lca_result = lca(t1, t2)
            if lca_result:
                return lca_result
            return common_type(t1.get_underlying_type(), t2.get_underlying_type())
        return None

    def numeric() -> Optional[Type]:
        if t1.is_float() and t2.is_numeric():
            return FloatType(FloatKind.F64)
        if t1.is_numeric() and t2.is_float():
            return FloatType(FloatKind.F64)
        if t1.is_numeric() and t2.is_numeric():
            return IntegerType()
        return None

    def string() -> Optional[Type]:
        if isinstance(t1, StringType) and isinstance(t2, StringType):
            return StringType(None)
        return None

    def enumeration() -> Optional[Type]:
        if isinstance(t1, EnumType):
            return common_type(t1.rep_type, t2)
        if isinstance(t2, EnumType):
            return common_type(t1, t2.rep_type)
        return None

    def array() -> Optional[Type]:
        def single_anon_array(anon_array: AnonArrayType, other: Type) -> Optional[Type]:
            if other.is_promotable_to_array():
                elt_type = common_type(other, anon_array.elt_type)
                if elt_type:
                    return AnonArrayType(size=anon_array.size, elt_type=elt_type)
            return None

        match pair:
            case (_, ArrayType(_, anon_array2, _, _)):
                return common_type(t1, anon_array2)
            case (ArrayType(_, anon_array1, _, _), _):
                return common_type(anon_array1, t2)
            case (AnonArrayType(size1, elt_type1), AnonArrayType(size2, elt_type2)):
                if array_sizes_match(size1, size2):
                    size = common_array_size(size1, size2)
                    elt_type = common_type(elt_type1, elt_type2)
                    if elt_type:
                        return AnonArrayType(size=size, elt_type=elt_type)
                return None
            case (_, anon_array) if isinstance(anon_array, AnonArrayType):
                return single_anon_array(anon_array, t1)
            case (anon_array, _) if isinstance(anon_array, AnonArrayType):
                return single_anon_array(anon_array, t2)
            case _:
                return None

    def struct() -> Optional[Type]:
        def two_anon_structs(members1: Dict, members2: Dict) -> Optional[Type]:
            def resolve_t1_member(member: tuple) -> Optional[tuple]:
                name1, ty1 = member
                if name1 in members2:
                    ty2 = members2[name1]
                    ty = common_type(ty1, ty2)
                    if ty:
                        return (name1, ty)
                else:
                    return member
                return None

            # TODO
            #resolved1 = StructType.resolve_members(resolve_t1_member)(members1)
            resolved1 = None
            if resolved1 is None:
                return None

            extra_members = {k: v for k, v in members2.items() if k not in members1}
            return AnonStructType({**resolved1, **extra_members})

        def single_anon_struct(members: Dict, other: Type) -> Optional[Type]:
            if not other.is_promotable_to_struct():
                return None

            def resolve_member(member: tuple) -> Optional[tuple]:
                name, ty = member
                resolved_ty = common_type(other, ty)
                return (name, resolved_ty) if resolved_ty else None

            # TODO
            #resolved = StructType.resolve_members(resolve_member)(members)
            resolved = None
            if resolved is not None:
                return AnonStructType(resolved)
            return None

        match pair:
            case (_, StructType(_, anon_struct2, _, _, _)):
                return common_type(t1, anon_struct2)
            case (StructType(_, anon_struct1, _, _, _), _):
                return common_type(anon_struct1, t2)
            case (AnonStructType(members1), AnonStructType(members2)):
                return two_anon_structs(members1, members2)
            case (_, AnonStructType(members)):
                return single_anon_struct(members, t1)
            case (AnonStructType(members), _):
                return single_anon_struct(members, t2)
            case _:
                return None

    rules: List['Rule'] = [
        identical,
        alias,
        numeric,
        string,
        enumeration,
        array,
        struct
    ]

    return select_first_match_in(rules)



class Value(ABC):
    def __init__(self):
        pass

    def __add__(self, other: 'Value') -> Optional['Value']:
        def int_op(v1: int, v2: int) -> int:
            return v1 + v2
        
        def double_op(v1: float, v2: float) -> float:
            return v1 + v2

        return self.binop(Binop(int_op, double_op), other)

    def __truediv__(self, other: 'Value') -> Optional['Value']:
        def int_op(v1: int, v2: int) -> int:
            return v1 // v2  # integer division

        def double_op(v1: float, v2: float) -> float:
            return v1 / v2
        
        return self.binop(Binop(int_op, double_op), other)

    def __mul__(self, other: 'Value') -> Optional['Value']:
        def int_op(v1: int, v2: int) -> int:
            return v1 * v2

        def double_op(v1: float, v2: float) -> float:
            return v1 * v2

        return self.binop(Binop(int_op, double_op), other)

    def __neg__(self) -> Optional['Value']:
        # Unary minus
        return None

    def is_zero(self) -> bool:
        return False

    def convert_to_distinct_type(self, t: Type) -> Optional['Value']:
        return None

    def convert_to_type(self, t: Type) -> Optional['Value']:
        if are_identical(self.get_type(), t.get_underlying_type()):
            return self
        else:
            return self.convert_to_distinct_type(t)

    def binop(self, op: 'Binop', other: 'Value') -> Optional['Value']:
        # To be overridden by subclasses
        return None

    @abstractmethod
    def get_type(self) -> Type:
        pass

    def promote_to_aggregate(self, t: Type) -> Optional['Value']:
        def promote_to_anon_array(anon_array: AnonArrayType) -> Optional[AnonArrayValue]:
            if self.get_type().is_promotable_to_array():
                size = anon_array.size
                if size is not None:
                    elt = self.convert_to_type(anon_array.elt_type)
                    if elt is not None:
                        return AnonArrayValue([elt] * size)
            return None

        def promote_to_array(array: ArrayType) -> Optional[ArrayValue]:
            anon_array = promote_to_anon_array(array.anon_array)
            if anon_array is not None:
                return ArrayValue(anon_array, array)
            return None

        def promote_to_anon_struct(anon_struct: AnonStructType) -> Optional[AnonStructValue]:
            if not self.get_type().is_promotable_to_struct():
                return None

            out: StructMembersValue = {}
            for member_name, member_type in anon_struct.members.items():
                v = self.convert_to_type(member_type)
                if v is None:
                    return None
                out[member_name] = v
            return AnonStructValue(out)

        def promote_to_struct(struct: StructType) -> Optional[StructValue]:
            anon_struct = promote_to_anon_struct(struct.anon_struct)
            if anon_struct is not None:
                return StructValue(anon_struct, struct)
            return None

        if isinstance(t, AnonArrayType):
            return promote_to_anon_array(t)
        elif isinstance(t, ArrayType):
            return promote_to_array(t)
        elif isinstance(t, AnonStructType):
            return promote_to_anon_struct(t)
        elif isinstance(t, StructType):
            return promote_to_struct(t)
        else:
            return None
        
    def truncate(self) -> 'Value':
        return self


class PrimitiveIntValue(Value):
    def __init__(self, value: int, kind: PrimitiveIntKind):
        self.value = value
        self.kind = kind

    def binop(self, op: 'Binop', v: Value) -> Optional[Value]:
        if isinstance(v, PrimitiveIntValue):
            result1 = op.int_op(self.value, v.value)
            result2: Value = IntegerValue(result1)
            if v.kind == self.kind:
                result2 = PrimitiveIntValue(result1, self.kind)
            return result2
        elif isinstance(v, IntegerValue):
            return IntegerValue(op.int_op(self.value, v.value))
        elif isinstance(v, FloatValue):
            result = op.double_op(float(self.value), v.value)
            return FloatValue(float(result), FloatKind.F64)
        elif isinstance(v, EnumConstantValue):
            rep_type_val = v.convert_to_rep_type()
            return self.binop(op, rep_type_val)
        else:
            return None

    def convert_to_distinct_type(self, t: 'Type') -> Optional[Value]:
        underlying = t.get_underlying_type()
        if isinstance(underlying, PrimitiveIntType):
            return PrimitiveIntValue(self.value, underlying.kind)
        elif isinstance(underlying, IntegerType):
            return IntegerValue(self.value)
        elif isinstance(underlying, FloatType):
            return FloatValue(float(self.value), underlying.kind)
        else:
            return self.promote_to_aggregate(t)

    def get_type(self) -> 'Type':
        return PrimitiveIntType(self.kind)

    def is_zero(self) -> bool:
        return self.value == 0

    def __str__(self):
        return f"{self.value}: {self.kind}"

    def truncate(self) -> 'PrimitiveIntValue':
        def truncate_unsigned(v: int, shift_amt: int) -> int:
            modulus = 1 << shift_amt
            truncated = v % modulus
            return truncated + modulus if truncated < 0 else truncated

        if self.kind == PrimitiveIntKind.I8:
            v = (self.value & 0xFF) if self.value >= 0 else (self.value | ~0xFF)
        elif self.kind == PrimitiveIntKind.I16:
            v = (self.value & 0xFFFF) if self.value >= 0 else (self.value | ~0xFFFF)
        elif self.kind == PrimitiveIntKind.I32:
            v = (self.value & 0xFFFFFFFF) if self.value >= 0 else (self.value | ~0xFFFFFFFF)
        elif self.kind == PrimitiveIntKind.I64:
            v = self.value  # Python int is unbounded, no need to truncate for 64-bit
        elif self.kind == PrimitiveIntKind.U8:
            v = truncate_unsigned(self.value, 8)
        elif self.kind == PrimitiveIntKind.U16:
            v = truncate_unsigned(self.value, 16)
        elif self.kind == PrimitiveIntKind.U32:
            v = truncate_unsigned(self.value, 32)
        elif self.kind == PrimitiveIntKind.U64:
            v = truncate_unsigned(self.value, 64)
        else:
            v = self.value

        return PrimitiveIntValue(v, self.kind)

    def __neg__(self) -> 'PrimitiveIntValue':
        return PrimitiveIntValue(-self.value, self.kind)

class IntegerValue(Value):
    def __init__(self, value: int):
        self.value = value

    def fits_in_u64_width(self) -> bool:
        u64_bound = 1 << 64
        return (- (u64_bound // 2)) <= self.value < u64_bound

    def binop(self, op: 'Binop', v: Value) -> Optional[Value]:
        if isinstance(v, PrimitiveIntValue):
            return IntegerValue(op.int_op(self.value, v.value))
        elif isinstance(v, IntegerValue):
            return IntegerValue(op.int_op(self.value, v.value))
        elif isinstance(v, FloatValue):
            return FloatValue(op.double_op(float(self.value), v.value), FloatKind.F64)
        elif isinstance(v, EnumConstantValue):
            return self.binop(op, v.convert_to_rep_type())
        else:
            return None

    def convert_to_distinct_type(self, t: 'Type') -> Optional[Value]:
        underlying = t.get_underlying_type()
        if isinstance(underlying, PrimitiveIntType):
            return PrimitiveIntValue(self.value, underlying.kind)
        elif isinstance(underlying, IntegerType):
            return IntegerValue(self.value)
        elif isinstance(underlying, FloatType):
            return FloatValue(float(self.value), underlying.kind)
        else:
            return self.promote_to_aggregate(t)

    def get_type(self) -> 'Type':
        return IntegerType()

    def is_zero(self) -> bool:
        return self.value == 0

    def __str__(self):
        return str(self.value)

    def __neg__(self) -> Optional['IntegerValue']:
        return IntegerValue(-self.value)


class FloatValue(Value):
    EPSILON = 1e-7  # Epsilon for near zero comparison

    def __init__(self, value: float, kind: FloatKind):
        self.value = value
        self.kind = kind

    def binop(self, op: 'Binop', v: Value) -> Optional[Value]:
        if isinstance(v, PrimitiveIntValue):
            result = op.double_op(self.value, float(v.value))
            return FloatValue(float(result), FloatKind.F64)
        elif isinstance(v, IntegerValue):
            result = op.double_op(self.value, float(v.value))
            return FloatValue(float(result), FloatKind.F64)
        elif isinstance(v, FloatValue):
            result1 = op.double_op(self.value, v.value)
            if v.kind == self.kind:
                result2 = FloatValue(result1, self.kind)
            else:
                result2 = FloatValue(result1, FloatKind.F64)
            return result2
        elif isinstance(v, EnumConstantValue):
            rep_type_val = v.convert_to_rep_type()
            return self.binop(op, rep_type_val)
        else:
            return None

    def is_zero(self) -> bool:
        return math.fabs(self.value) < self.EPSILON

    def convert_to_distinct_type(self, t: 'Type') -> Optional[Value]:
        underlying = t.get_underlying_type()
        if isinstance(underlying, PrimitiveIntType):
            return PrimitiveIntValue(int(self.value), underlying.kind)
        elif isinstance(underlying, IntegerType):
            return IntegerValue(int(self.value))
        elif isinstance(underlying, FloatType):
            return FloatValue(self.value, underlying.kind)
        else:
            return self.promote_to_aggregate(t)

    def get_type(self) -> 'Type':
        return FloatType(self.kind)

    def __str__(self) -> str:
        return f"{self.value}: {self.kind}"

    def truncate(self) -> 'FloatValue':
        if self.kind == FloatKind.F32:
            return FloatValue(float(self.value), self.kind)
        elif self.kind == FloatKind.F64:
            return self
        else:
            # Optional: handle other float kinds if exist
            return self

    def __neg__(self) -> 'FloatValue':
        return FloatValue(-self.value, self.kind)


class BooleanValue(Value):
    def __init__(self, value: bool):
        self.value = value

    def convert_to_distinct_type(self, t: 'Type') -> Optional[Value]:
        return self.promote_to_aggregate(t.get_underlying_type())

    def get_type(self) -> 'Type':
        return BooleanType()

    def __str__(self) -> str:
        return str(self.value)


class StringValue(Value):
    def __init__(self, value: str):
        self.value = value

    def convert_to_distinct_type(self, t: 'Type') -> Optional[Value]:
        underlying = t.get_underlying_type()
        if isinstance(underlying, StringType):
            return self
        else:
            return self.promote_to_aggregate(t)

    def get_type(self) -> 'Type':
        return StringType(None)

    def __str__(self) -> str:
        return f"\"{self.value}\""


class AnonArrayValue(Value):
    def __init__(self, elements: List[Value]):
        self.elements = elements

    def convert_to_anon_array(self, anon_array_type: AnonArrayType) -> Optional['AnonArrayValue']:
        def convert_elements(in_list: List[Value], t: 'Type', out: List[Value]) -> Optional[List[Value]]:
            if not in_list:
                return out[::-1]
            head, *tail = in_list
            converted = head.convert_to_type(t.get_underlying_type())
            if converted is not None:
                return convert_elements(tail, t.get_underlying_type(), [converted] + out)
            else:
                return None

        size = anon_array_type.size
        elt_type = anon_array_type.elt_type

        if array_sizes_match(len(self.elements), size):
            converted_elements = convert_elements(self.elements, elt_type, [])
            if converted_elements is not None:
                return AnonArrayValue(converted_elements)
        return None

    def convert_to_array(self, array_type: 'ArrayType') -> Optional['ArrayValue']:
        anon_array = self.convert_to_anon_array(array_type.anon_array)
        if anon_array is not None:
            return ArrayValue(anon_array, array_type)
        return None

    def convert_to_distinct_type(self, t: 'Type') -> Optional['Value']:
        underlying = t.get_underlying_type()
        if isinstance(underlying, AnonArrayType):
            return self.convert_to_anon_array(underlying)
        elif isinstance(underlying, ArrayType):
            return self.convert_to_array(underlying)
        else:
            return None

    def get_type(self) -> 'Type':
        size = len(self.elements)
        elt_type = self.elements[0].get_type()
        return AnonArrayType(size, elt_type)

    def __str__(self) -> str:
        return "[ " + ", ".join(str(e) for e in self.elements) + " ]"

    def truncate(self) -> 'AnonArrayValue':
        truncated_elements = [e.truncate() for e in self.elements]
        return AnonArrayValue(truncated_elements)

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

    def convert_to_anon_array(self, anon_array_type: AnonArrayType) -> 'Optional[AnonArrayValue]':
        return self.anon_array.convert_to_anon_array(anon_array_type)

    def convert_to_array(self, array_type: ArrayType) -> 'Optional[ArrayValue]':
        return self.anon_array.convert_to_array(array_type)

    def convert_to_distinct_type(self, t: 'Type') -> 'Optional[Value]':
        underlying = t.get_underlying_type()
        if isinstance(underlying, AnonArrayType):
            return self.convert_to_anon_array(underlying)
        elif isinstance(underlying, ArrayType):
            return self.convert_to_array(underlying)
        else:
            return None

    def get_type(self) -> ArrayType:
        return self.t

    def __str__(self) -> str:
        # Assuming t.node is a tuple (some_value, some_data), where some_data has attribute 'name'
        return f"{self.anon_array}: {self.t.node[1].data.name}"

    def truncate(self) -> 'ArrayValue':
        return ArrayValue(self.anon_array.truncate(), self.t)


class EnumConstantValue(Value):
    def __init__(self, value: Tuple[fpp_ast.Unqualified, int], t: EnumType):
        self.value = value
        self.t = t

    def binop(self, op: 'Binop', v: 'Value') -> 'Optional[Value]':
        return self.convert_to_rep_type().binop(op, v)

    def convert_to_rep_type(self) -> PrimitiveIntValue:
        return PrimitiveIntValue(self.value[1], self.t.rep_type.kind)

    def convert_to_distinct_type(self, t: 'Type') -> 'Optional[Value]':
        converted = self.convert_to_rep_type().convert_to_distinct_type(t.get_underlying_type())
        if converted is not None:
            return converted
        else:
            return self.promote_to_aggregate(t)

    def get_type(self) -> 'EnumType':
        return self.t

    def is_zero(self) -> bool:
        return self.convert_to_rep_type().is_zero()

    def __str__(self) -> str:
        # assuming t.node is tuple and second element has data.name
        return f"{self.value}: {self.t.node[1].data.name}"

    def __neg__(self) -> 'Value':
        return -self.convert_to_rep_type()


StructMembersValue: TypeAlias = Dict[fpp_ast.Unqualified, Value]

class AnonStructValue(Value):
    def __init__(self, members: StructMembersValue):
        # members: dict mapping member names to Values
        self.members = members

    def convert_to_anon_struct(self, anon_struct_type: AnonStructType) -> Optional['AnonStructValue']:
        def convert_members(in_members: List[Tuple[fpp_ast.Unqualified, Type]], out: StructMembersValue) -> Optional[StructMembersValue]:
            if not in_members:
                return out
            else:
                m, t = in_members[0]
                v_opt = self.members[m].convert_to_type(t) if m in self.members else t.get_default_value()
                if v_opt is not None:
                    out[m] = v_opt
                    return convert_members(in_members[1:], out)
                else:
                    return None
        
        anon_struct_members_list = []
        for unqual_name, value in anon_struct_type.members.items():
            anon_struct_members_list.append((unqual_name, value))
        
        members_converted = convert_members(anon_struct_members_list, {})
        if members_converted is not None:
            return AnonStructValue(members_converted)
        else:
            return None

    def convert_to_struct(self, struct_type: 'StructType') -> Optional['StructValue']:
        anon_struct = self.convert_to_anon_struct(struct_type.anon_struct)
        if anon_struct is not None:
            return StructValue(anon_struct, struct_type)
        else:
            return None

    def convert_to_distinct_type(self, t: 'Type') -> Optional['Value']:
        underlying = t.get_underlying_type()
        if isinstance(underlying, AnonStructType):
            return self.convert_to_anon_struct(underlying)
        elif isinstance(underlying, StructType):
            return self.convert_to_struct(underlying)
        else:
            return None

    def get_type(self) -> AnonStructType:
        # members is dict of name -> Value
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

    def truncate(self) -> 'AnonStructValue':
        truncated_members = {m: v.truncate() for m, v in self.members.items()}
        return AnonStructValue(truncated_members)


class StructValue(Value):
    def __init__(self, anon_struct: AnonStructValue, t: StructType):
        self.anon_struct = anon_struct
        self.t = t

    def convert_to_anon_struct(self, anon_struct_type: AnonStructType) -> Optional[AnonStructValue]:
        return self.anon_struct.convert_to_anon_struct(anon_struct_type)

    def convert_to_struct(self, struct_type: StructType) -> Optional['StructValue']:
        return self.anon_struct.convert_to_struct(struct_type)

    def convert_to_distinct_type(self, t: 'Type') -> Optional['Value']:
        underlying = t.get_underlying_type()
        if isinstance(underlying, AnonStructType):
            return self.convert_to_anon_struct(underlying)
        elif isinstance(underlying, StructType):
            return self.convert_to_struct(underlying)
        else:
            return None

    def get_type(self) -> StructType:
        return self.t

    def __str__(self) -> str:
        # Assuming t.node._2.data.name can be accessed like this:
        type_name = getattr(self.t.node[1].data, 'name', 'unknown') if hasattr(self.t, 'node') else 'unknown'
        return f"{str(self.anon_struct)}: {type_name}"

    def truncate(self) -> 'StructValue':
        return StructValue(self.anon_struct.truncate(), self.t)


class Binop(Generic[T]):
    def __init__(self, int_op: Callable[[int, int], int], double_op: Callable[[float, float], float]):
        self.int_op = int_op
        self.double_op = double_op
