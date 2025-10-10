from fprime_python_model.fpp_ast.fpp_ast_node import AstId
from fprime_python_model.utils.error import InternalError
from typing import Optional, Dict
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Location:
    path: Path
    pos: str
    includingLoc: Optional[str]
