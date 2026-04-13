from __future__ import annotations
import os
import json
from fprime_python_model.fpp_version import MIN_FPP_VERSION
from fprime_python_model.model import FprimePythonModel
from fprime_python_model.fpp_ast.fpp_ast_node import AstNode
from fprime_python_model.semantics.symbol import Symbol
from fprime_python_model.semantics.component_instance import ComponentInstance
from fprime_python_model.semantics.port_instance_identifier import (
    PortInstanceIdentifier,
)
from fprime_python_model.semantics.types_values import *
from fprime_python_model.semantics.analysis import Analysis
from dataclasses import is_dataclass, fields
from enum import Enum
from pathlib import Path
from typing import (
    Any,
    Callable,
    Dict,
    Optional,
    Type,
    TypeVar,
)
from functools import lru_cache

T = TypeVar("T")
SerializerFn = Callable[[Any], Any]

SERIALIZERS: Dict[Type[Any], SerializerFn] = {}


def serializer(cls: Type[T]):
    def wrapper(fn: Callable[[T], Any]):
        SERIALIZERS[cls] = fn
        return fn

    return wrapper


def find_serializer(obj: Any) -> Optional[SerializerFn]:
    for cls, fn in SERIALIZERS.items():
        if isinstance(obj, cls):
            return fn
    return None


def snake_to_camel(s: str) -> str:
    parts = s.split("_")
    return parts[0] + "".join(p.capitalize() for p in parts[1:])


@lru_cache(None)
def resolve_class_name(cls: type) -> str:
    name = cls.__name__

    suffix_to_strip = ("Value", "Type", "PortInstance", "Field")
    prefix_to_strip = ("Command", "NonParamKind", "ParamKind")

    for suffix in suffix_to_strip:
        if name.endswith(suffix) and name not in ("AliasType", "AbsType"):
            name = name.removesuffix(suffix)

    for prefix in prefix_to_strip:
        if name.startswith(prefix):
            name = name[len(prefix) :]
            break

    return name


def is_annotated_astnode_tuple(obj):
    return isinstance(obj, tuple) and len(obj) == 3 and isinstance(obj[1], AstNode)


def serialize(obj):
    fn = find_serializer(obj)
    if fn:
        return fn(obj)

    if obj is None:
        return "None"

    # primitives
    if isinstance(obj, (str, int, float, bool)):
        return obj

    if isinstance(obj, Path):
        return str(obj)

    # enums
    if isinstance(obj, Enum):
        return obj.name

    # AST node
    if isinstance(obj, AstNode):
        return {"astNodeId": obj.get_id()}

    # annotated AST tuple
    if is_annotated_astnode_tuple(obj):
        return serialize(obj[1])

    # dataclasses
    if is_dataclass(obj):
        runtime = type(obj)

        data = {
            snake_to_camel(f.name): serialize(getattr(obj, f.name)) for f in fields(obj)
        }

        return {resolve_class_name(runtime): data}

    # dict
    if isinstance(obj, dict):
        return {str(k): serialize(v) for k, v in obj.items()}

    # list/tuple/set
    if isinstance(obj, (list, tuple, set)):
        return [serialize(x) for x in obj]

    if hasattr(obj, "__dict__"):
        runtime = type(obj)

        data = {
            snake_to_camel(k): serialize(v)
            for k, v in obj.__dict__.items()
            if not callable(v) and not k.startswith("_")
        }

        return {resolve_class_name(runtime): data}

    return obj


# special cases


@serializer(AstNode)
def _ast_node(obj: AstNode):
    return {"astNodeId": obj.get_id()}


@serializer(Symbol)
def _symbol(symbol: Symbol):
    name = type(symbol).__name__.replace("Symbol", "")
    return {
        name: {
            "nodeId": symbol.get_node_id(),
            "unqualifiedName": symbol.get_unqualified_name(),
        }
    }


@serializer(ComponentInstance)
def _component_instance(obj: ComponentInstance):
    data = serialize(obj.__dict__)
    data["component"] = {"astNodeId": obj.component.a_node[1].get_id()}
    return data


@serializer(PortInstanceIdentifier)
def _port_instance_identifier(obj: PortInstanceIdentifier):
    data = serialize(obj.__dict__)

    if hasattr(obj.port_instance, "kind"):
        data.setdefault("portInstance", {})
        data["portInstance"]["General"] = {"kind": obj.port_instance.kind.name}

    return data


@serializer(PrimitiveIntType)
def _primitive_int(obj: PrimitiveIntType):
    return {"Int": {"PrimitiveInt": {"kind": {obj.kind.name: {}}}}}


@serializer(IntegerType)
def _integer(obj: IntegerType):
    return {"Int": {"Integer": {}}}


@serializer(FloatType)
def _float(obj: FloatType):
    return {"Primitive": {"Float": {"kind": {obj.kind.name: {}}}}}


def map_as_dict(m: Dict[Any, Any]) -> Dict[str, Any]:
    return {str(k): serialize(v) for k, v in m.items()}


def analysis_to_json(analysis: Analysis) -> Dict[str, Any]:
    return {
        "fppVersion": str(MIN_FPP_VERSION),
        "analysis": {
            "componentInstanceMap": map_as_dict(analysis.component_instance_map),
            "componentMap": map_as_dict(analysis.component_map),
            "includedFileSet": serialize(analysis.included_file_set),
            "inputFileSet": serialize(analysis.input_file_set),
            "locationSpecifierMap": serialize(analysis.location_specifier_map),
            "parentSymbolMap": serialize(analysis.parent_symbol_map),
            "symbolScopeMap": serialize(analysis.symbol_scope_map),
            "topologyMap": map_as_dict(analysis.topology_map),
            "typeMap": map_as_dict(analysis.type_map),
            "useDefMap": serialize(analysis.use_def_map),
            "valueMap": map_as_dict(analysis.value_map),
        },
    }


# for debugging
def json_diff(d1: Any, d2: Any, path="") -> list[str]:
    diffs = []

    if isinstance(d1, dict) and isinstance(d2, dict):
        keys1 = set(d1.keys())
        keys2 = set(d2.keys())

        # Keys only in d1
        for key in keys1 - keys2:
            diffs.append(f"{path}{key} only in first JSON")

        # Keys only in d2
        for key in keys2 - keys1:
            diffs.append(f"{path}{key} only in second JSON")

        # Keys in both
        for key in keys1 & keys2:
            diffs.extend(json_diff(d1[key], d2[key], path=f"{path}{key}."))

    elif isinstance(d1, list) and isinstance(d2, list):
        min_len = min(len(d1), len(d2))
        for i in range(min_len):
            diffs.extend(json_diff(d1[i], d2[i], path=f"{path}{i}."))
        if len(d1) > len(d2):
            for i in range(min_len, len(d1)):
                diffs.append(f"{path}{i} only in first JSON")
        elif len(d2) > len(d1):
            for i in range(min_len, len(d2)):
                diffs.append(f"{path}{i} only in second JSON")
    else:
        if d1 != d2:
            diffs.append(f"{path[:-1]} differs: {d1} != {d2}")

    return diffs


TEST_DIR = Path(__file__).resolve().parent

tests = [
    "types"
]  # ["commands", "events", "telemetry", "parameters", "location_specifier"]
for test in tests:
    print(f"Test case: {test}")
    test_path = TEST_DIR / test
    fpp_ref_file = test_path / f"{test}.fpp"
    ast_file = test_path / f"{test}_ast.json"
    analysis_file = test_path / f"{test}_analysis.json"
    locations_file = test_path / f"{test}_locations.json"

    files = [fpp_ref_file, ast_file, analysis_file, locations_file]

    # Make sure all test files exist
    for f in files:
        assert os.path.isfile(f)

    # Construct an FprimePythonModel using test inputs
    model = FprimePythonModel(ast_file, locations_file, analysis_file)
    with open("analysis.json", "w") as f:
        json.dump(analysis_to_json(model.analysis), f, indent=4)

    with open(analysis_file, "r") as f:
        orig_analysis = json.load(f)

    with open("analysis.json", "r") as f:
        test_analysis = json.load(f)

    res = json_diff(orig_analysis["analysis"], test_analysis["analysis"])
    if not res:
        print("No diffs!")
    for r in res:
        print(r)
        print()
