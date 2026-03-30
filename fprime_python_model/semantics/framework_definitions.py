from dataclasses import dataclass, field
from typing import Dict
from fprime_python_model.semantics.symbol import ConstantSymbol, TypeSymbol


@dataclass
class FrameworkDefinitions:
    constant_map: Dict[str, ConstantSymbol] = field(default_factory=dict)
    type_map: Dict[str, TypeSymbol] = field(default_factory=dict)

    def add_constant(self, name: str, sym: ConstantSymbol):
        self.constant_map[name] = sym

    def add_type(self, name: str, sym: TypeSymbol):
        self.type_map[name] = sym
