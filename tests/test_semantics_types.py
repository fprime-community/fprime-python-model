from fprime_python_model.model import FprimePythonModel
from fprime_python_model.semantics.format import (
    Format,
    RationalField,
    RationalFieldType,
)
from fprime_python_model.semantics.types_values import (
    ArrayType,
    StringType,
    IntegerType,
    PrimitiveIntType,
    PrimitiveType,
    AliasType,
    EnumType,
    StructType,
    AbsType,
    Signedness,
    StructValue,
    AnonStructValue,
    PrimitiveIntKind,
    EnumConstantValue,
    ArrayValue,
    AnonArrayValue,
    FloatValue,
    FloatKind,
    AnonArrayType,
    FloatType,
    AnonStructType,
)
from fprime_python_model.fpp_ast import fpp_ast
import os


def test_types():
    # Get location of test directory
    test = "types"
    test_dir = os.path.dirname(os.path.abspath(__file__))
    test_path = os.path.join(test_dir, test)
    print(f"Test Case: {test}")
    fpp_ref_file = os.path.join(test_path, f"{test}.fpp")
    ast_file = os.path.join(test_path, f"{test}_ast.json")
    analysis_file = os.path.join(test_path, f"{test}_analysis.json")
    locations_file = os.path.join(test_path, f"{test}_locations.json")
    files = [fpp_ref_file, ast_file, analysis_file, locations_file]

    # Make sure all test files exist
    for f in files:
        assert os.path.isfile(f)

    # Construct an FprimePythonModel using test inputs
    model = FprimePythonModel(ast_file, locations_file, analysis_file)

    type_map = model.analysis.type_map

    # Integer
    int_id = 128
    int_type = type_map[int_id]
    assert isinstance(int_type, IntegerType)
    assert int_type.is_numeric()
    assert int_type.is_int()
    assert not int_type.is_float()
    assert not int_type.is_displayable()

    # Primitive Integer
    primitive_int_id = 44
    primitive_int_type = type_map[primitive_int_id]
    assert isinstance(primitive_int_type, PrimitiveIntType)
    assert primitive_int_type.is_primitive()
    assert primitive_int_type.is_int()
    assert not primitive_int_type.is_float()
    assert primitive_int_type.is_displayable()

    # Primitive (float)
    primitive_float_id = 100
    primitive_float_type = type_map[primitive_float_id]
    assert isinstance(primitive_float_type, PrimitiveType)
    assert primitive_float_type.is_primitive()
    assert primitive_float_type.is_float()
    assert not primitive_float_type.is_int()
    assert primitive_float_type.is_displayable()

    # String
    string_id = 8
    string_type = type_map[string_id]
    assert isinstance(string_type, StringType)
    assert (
        string_type.size
        and isinstance(string_type.size.data, fpp_ast.ExprLiteralInt)
        and string_type.size.data.value == "40"
    )
    assert string_type.is_displayable()
    assert not string_type.is_numeric()

    # Alias types
    alias_id = 121
    alias_type = type_map[alias_id]
    alias_underlying_type = alias_type.get_underlying_type()
    assert isinstance(alias_type, AliasType)
    assert isinstance(alias_underlying_type, PrimitiveIntType)
    assert alias_type.is_displayable()
    assert alias_underlying_type.is_int()
    assert alias_underlying_type.is_numeric()
    assert not alias_underlying_type.is_float()

    # Arrays
    array_id = 88
    array_type = type_map[array_id]
    assert isinstance(array_type, ArrayType)
    assert array_type.get_def_node_id() == 108
    assert array_type.get_array_size() == None
    assert array_type.has_numeric_members()
    assert array_type.is_displayable()

    array_id2 = 112
    array_type2 = type_map[array_id2]
    assert isinstance(array_type2, ArrayType)
    assert array_type2.get_array_size() == 4
    assert array_type2.has_numeric_members()
    assert array_type2.format
    first_field = array_type2.format.fields[0]
    assert first_field[0].is_rational() and first_field[1] == ""

    # Enum
    enum_id = 72
    enum_type = type_map[enum_id]
    assert isinstance(enum_type, EnumType)
    assert enum_type.is_displayable()
    assert enum_type.default == None
    assert (
        enum_type.rep_type.bit_width() == 32
        and enum_type.rep_type.signedness() == Signedness.SIGNED
    )

    # Struct
    struct_id = 90
    struct_type = type_map[struct_id]
    assert isinstance(struct_type, StructType)
    assert struct_type.is_displayable()
    anon_struct_member_type_map = {
        "type": EnumType,
        "history": ArrayType,
        "pairHistory": ArrayType,
    }

    pair_history_struct_type = StructType(
        model.annotated_ast_id_map[103],
        AnonStructType(
            {
                "time": FloatType(FloatKind.F32),
                "value": FloatType(FloatKind.F32),
            }
        ),
    )
    anon_struct_member_value_map = {
        "type": EnumConstantValue(
            ("TRIANGLE", 0),
            EnumType(
                model.annotated_ast_id_map[119],
                PrimitiveIntType(PrimitiveIntKind.I32),
                None,
            ),
        ),
        "history": ArrayValue(
            AnonArrayValue([FloatValue(0.0, FloatKind.F32)] * 4),
            ArrayType(
                model.annotated_ast_id_map[112],
                AnonArrayType(4, FloatType(FloatKind.F32)),
            ),
        ),
        "pairHistory": ArrayValue(
            AnonArrayValue(
                [
                    StructValue(
                        AnonStructValue(
                            {
                                "time": FloatValue(0.0, FloatKind.F32),
                                "value": FloatValue(0.0, FloatKind.F32),
                            }
                        ),
                        pair_history_struct_type,
                    )
                ]
                * 4
            ),
            ArrayType(
                model.annotated_ast_id_map[108],
                AnonArrayType(
                    4,
                    StructType(
                        model.annotated_ast_id_map[103],
                        AnonStructType(
                            {
                                "time": FloatType(FloatKind.F32),
                                "value": FloatType(FloatKind.F32),
                            }
                        ),
                        StructValue(
                            AnonStructValue(
                                {
                                    "time": FloatValue(0.0, FloatKind.F32),
                                    "value": FloatValue(0.0, FloatKind.F32),
                                }
                            ),
                            pair_history_struct_type,
                        ),
                        {},
                        {
                            "time": Format(
                                "", [RationalField(None, RationalFieldType.FIXED)]
                            ),
                            "value": Format(
                                "", [RationalField(None, RationalFieldType.FIXED)]
                            ),
                        },
                    ),
                ),
            ),
        ),
    }

    for k, v in struct_type.anon_struct.members.items():
        assert k in anon_struct_member_type_map
        assert isinstance(v, anon_struct_member_type_map[k])

    for (
        k,
        v,
    ) in struct_type.default.anon_struct.members.items():
        assert k in anon_struct_member_value_map
        assert str(anon_struct_member_value_map[k]) == str(v)

    # Abstract type
    abs_id = 64
    abs_type = type_map[abs_id]
    assert isinstance(abs_type, AbsType)
    assert not abs_type.is_displayable()
    assert not abs_type.is_numeric()
    assert not abs_type.is_primitive()
