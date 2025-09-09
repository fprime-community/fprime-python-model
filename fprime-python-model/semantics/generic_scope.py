from dataclasses import dataclass
from typing import Dict, TypeVar, Generic, Optional
from semantics.symbol_interface import SymbolInterface
import fpp_ast

NG = TypeVar('NG')
S = TypeVar('S', bound=SymbolInterface)


class GenericNameSymbolMap(Generic[S]):
    def __init__(self, symbol_map: Optional[Dict[fpp_ast.Unqualified, S]] = None):
        self.map: Dict[fpp_ast.Unqualified, S] = symbol_map if symbol_map is not None else {}

    def __call__(self, name: fpp_ast.Unqualified) -> S:
        """Get a symbol from the map. Raises if not found."""
        return self.map[name]

    def put(self, name: fpp_ast.Unqualified, symbol: S) -> "GenericNameSymbolMap[S]":
        new_map = self.map.copy()
        new_map[name] = symbol
        return GenericNameSymbolMap(new_map)

    def get(self, name: fpp_ast.Unqualified) -> Optional[S]:
        """Get a symbol from the map. Return None if not found."""
        return self.map.get(name)


@dataclass(frozen=True)
class GenericScope(Generic[NG, S]):
    map: Dict[NG, GenericNameSymbolMap[S]]

    def __init__(self, map: Optional[Dict[NG, GenericNameSymbolMap[S]]] = None):
        object.__setattr__(self, 'map', map or {})

    def __call__(self, name_group: NG, name: fpp_ast.Unqualified) -> S:
        name_symbol_map = self._get_name_symbol_map(name_group)
        symbol = name_symbol_map.get(name)
        if symbol is None:
            raise KeyError(f"Symbol not found for name: {name}")
        return symbol

    def put(self, name_group: NG, name: fpp_ast.Unqualified, symbol: S) -> 'GenericScope[NG, S]':
        name_symbol_map = self._get_name_symbol_map(name_group)
        new_map = self.map.copy()
        new_map[name_group] = name_symbol_map.put(name, symbol)
        return GenericScope(new_map)

    def get(self, name_group: NG, name: fpp_ast.Unqualified) -> Optional[S]:
        name_symbol_map = self._get_name_symbol_map(name_group)
        return name_symbol_map.get(name)

    def _get_name_symbol_map(self, name_group: NG) -> GenericNameSymbolMap[S]:
        return self.map.get(name_group, GenericNameSymbolMap())
