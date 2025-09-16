from fprime_python_model.fpp_ast.fpp_locations import Locations, Location
import json
from typing import Dict
import os
from fprime_python_model.fpp_ast.fpp_ast_node import AstId
from pathlib import Path


def translate_location_map_json(file: str) -> dict[AstId, Location]:
    if not os.path.exists(file):
        raise FileNotFoundError(f'File "{file}" not found')
    with open(file, "r") as f:
        data: Dict[str, dict] = json.load(f)
        for k, v in data.items():
            try:
                Locations.put(
                    int(k), Location(Path(v["file"]), v["pos"], v["includingLoc"])
                )
            except KeyError as e:
                raise KeyError(f"Location map for ID {k} is missing required field {e}")
    return Locations.get_map()
