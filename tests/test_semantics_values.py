from fprime_python_model.model import FprimePythonModel
from fprime_python_model.semantics.types_values import (
    StringValue,
    IntegerValue,
    BooleanValue,
    FloatValue,
    AnonArrayValue,
    AnonArrayType,
    AnonStructType,
    AnonStructValue,
    FloatKind,
    FloatType,
    BooleanType,
    IntegerType,
    StringType,
)
import os


def test_types():
    # Get location of test directory
    test = "constants"
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

    value_map = model.analysis.value_map

    # Integer
    int_id = 33
    int_value = value_map[int_id]
    assert isinstance(int_value, IntegerValue)
    assert int_value.value == 1
    assert isinstance(int_value.get_type(), IntegerType)

    # String
    string_id = 5
    string_value = value_map[string_id]
    assert isinstance(string_value, StringValue)
    assert string_value.value == "This is a string."
    assert isinstance(string_value.get_type(), StringType)

    # Boolean
    bool_id = 73
    bool_value = value_map[bool_id]
    assert isinstance(bool_value, BooleanValue)
    assert bool_value.value == False
    assert isinstance(bool_value.get_type(), BooleanType)

    # Float
    float_id = 12
    float_value = value_map[float_id]
    assert isinstance(float_value, FloatValue)
    assert float_value.value == 2.0
    assert float_value.kind == FloatKind.F64
    assert isinstance(float_value.get_type(), FloatType)

    # Anon Struct
    struct_value_map = {
        "x": (IntegerValue, 1),
        "y": (StringValue, "abc"),
        "z": (BooleanValue, False),
    }

    struct_id = 40
    struct_value = value_map[struct_id]
    assert isinstance(struct_value, AnonStructValue)
    assert isinstance(struct_value.get_type(), AnonStructType)
    for unqual_name, value in struct_value.members.items():
        assert unqual_name in struct_value_map
        assert isinstance(value, struct_value_map[unqual_name][0])
        assert value.value == struct_value_map[unqual_name][1]

    # Anon Array
    array_values = [1, 2, 3]
    array_id = 9
    array_value = value_map[array_id]
    array_type = array_value.get_type()
    assert isinstance(array_value, AnonArrayValue)
    assert isinstance(array_type, AnonArrayType)
    assert array_type.get_array_size() == 3
    assert isinstance(array_type.elt_type, IntegerType)
    for index, value in enumerate(array_value.elements):
        assert value.value == array_values[index]
