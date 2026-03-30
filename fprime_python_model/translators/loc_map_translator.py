from fprime_python_model.fpp_ast.fpp_locations import Location
import json
from typing import Dict, Optional
import os
from fprime_python_model.fpp_ast.fpp_ast_node import AstId
from pathlib import Path


def translate_including_loc(d: dict) -> Optional[Location]:
    if "Some" in d:
        return translate_loc(d["Some"])
    else:
        return None


def translate_loc(d: dict) -> Location:
    return Location(
        Path(d["file"]),
        d["pos"],
        translate_including_loc(d["includingLoc"]),
    )


def translate_location_map_json(file: str) -> dict[AstId, Location]:
    loc_map: dict[AstId, Location] = dict()
    if not os.path.exists(file):
        raise FileNotFoundError(f'File "{file}" not found')
    with open(file, "r") as f:
        data: Dict[str, dict] = json.load(f)
        for k, v in data["locationMap"].items():
            try:
                loc_map[int(k)] = translate_loc(v)
            except KeyError as e:
                raise KeyError(f"Location map for ID {k} is missing required field {e}")
    return loc_map
