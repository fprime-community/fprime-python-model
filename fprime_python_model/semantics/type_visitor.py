from typing import Generic, TypeVar
from fprime_python_model.semantics.types_values import (
    AbsType,
    AliasType,
    AnonArrayType,
    AnonStructType,
    ArrayType,
    Type,
    EnumType,
    FloatType,
    PrimitiveIntType,
    IntegerType,
    StringType,
    StructType,
    BooleanType,
)

In = TypeVar("In")
Out = TypeVar("Out")


class TypeVisitor(Generic[In, Out]):
    def abs_type(self, in_: In, t: AbsType) -> Out:
        return self.default(in_, t)

    def alias_type(self, in_: In, t: AliasType) -> Out:
        return self.default(in_, t)

    def anon_array(self, in_: In, t: AnonArrayType) -> Out:
        return self.default(in_, t)

    def anon_struct(self, in_: In, t: AnonStructType) -> Out:
        return self.default(in_, t)

    def array(self, in_: In, t: ArrayType) -> Out:
        return self.default(in_, t)

    def boolean(self, in_: In) -> Out:
        return self.default(in_, BooleanType())

    def default(self, in_: In, t: Type) -> Out:
        raise NotImplementedError

    def enumeration(self, in_: In, t: EnumType) -> Out:
        return self.default(in_, t)

    def float(self, in_: In, t: FloatType) -> Out:
        return self.default(in_, t)

    def Integer(self, in_: In) -> Out:
        return self.default(in_, IntegerType())

    def primitive_int(self, in_: In, t: PrimitiveIntType) -> Out:
        return self.default(in_, t)

    def string(self, in_: In, t: StringType) -> Out:
        return self.default(in_, t)

    def struct(self, in_: In, t: StructType) -> Out:
        return self.default(in_, t)

    def ty(self, in_: In, t: Type) -> Out:
        return self.match_type(in_, t)

    def match_type(self, in_: In, t: Type) -> Out:
        if isinstance(t, AbsType):
            return self.abs_type(in_, t)
        elif isinstance(t, AliasType):
            return self.alias_type(in_, t)
        elif isinstance(t, AnonArrayType):
            return self.anon_array(in_, t)
        elif isinstance(t, AnonStructType):
            return self.anon_struct(in_, t)
        elif isinstance(t, ArrayType):
            return self.array(in_, t)
        elif t is BooleanType:
            return self.boolean(in_)
        elif isinstance(t, EnumType):
            return self.enumeration(in_, t)
        elif isinstance(t, FloatType):
            return self.float(in_, t)
        elif t is IntegerType:
            return self.Integer(in_)
        elif isinstance(t, PrimitiveIntType):
            return self.primitive_int(in_, t)
        elif isinstance(t, StringType):
            return self.string(in_, t)
        elif isinstance(t, StructType):
            return self.struct(in_, t)
        else:
            raise TypeError(f"Unknown Type: {t}")
