from dataclasses import dataclass
from typing import List, Tuple, Optional
from abc import ABC
from enum import Enum


class Field(ABC):
    def is_integer(self) -> bool:
        return False

    def is_rational(self) -> bool:
        return False

    def is_numeric(self) -> bool:
        return self.is_integer() or self.is_rational()


@dataclass
class DefaultField(Field):
    pass


class RationalFieldType(Enum):
    EXPONENT = "exponent"
    FIXED = "fixed"
    GENERAL = "general"


@dataclass
class RationalField(Field):
    precision: Optional[int]
    t: RationalFieldType

    def is_rational(self) -> bool:
        return True


class IntegeFieldType(Enum):
    CHARACTER = "character"
    DECIMAL = "decimal"
    HEXADECIMAL = "hexadecimal"
    OCTAL = "octal"


@dataclass
class IntegerField(Field):
    t: IntegeFieldType

    def is_integer(self) -> bool:
        return True


@dataclass
class Format:
    prefix: str
    fields: List[Tuple[Field, str]]
