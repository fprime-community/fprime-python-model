from fpp_ast_node import AstId
from error import InternalError
from typing import Optional, Dict
from dataclasses import dataclass
from pathlib import Path

@dataclass
class Location:
    path: Path
    pos: str
    includingLoc: Optional[str]

class Locations:
    """
    Manage locations of AST nodes
    """
    _map: Dict[AstId, Location] = {}

    @staticmethod
    def put(id: AstId, loc: Location):
        """
        Put a location into the map.
        """
        Locations._map[id] = loc

    @staticmethod
    def get(id: AstId) -> Location:
        """
        Get a location from the map. Raise InternalError if the location is not there.
        """
        if id in Locations._map:
            return Locations._map[id]
        else:
            raise InternalError(f"unknown location for AST node {id}")

    @staticmethod 
    def get_opt(id: AstId) -> Optional[Location]:
        """
        Get an optional location from the map.
        """
        return Locations._map.get(id)
    
    @staticmethod
    def get_map():
        """
        Get the location map as an immutable map.
        """
        return Locations._map.copy()



