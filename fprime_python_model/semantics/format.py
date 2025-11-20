from dataclasses import dataclass
from typing import List, Tuple, Optional
from abc import ABC
from enum import Enum


class Field(ABC):
    """
    A replacement field
    """

    def is_integer(self) -> bool:
        """
        Whether the field is an integer replacement field

        :return: True if the field is an integer replacement field, False otherwise
        :rtype: bool
        """
        return False

    def is_rational(self) -> bool:
        """
        Whether the field is a rational replacement field

        :return: True if the field is a rational replacement field, False otherwise
        :rtype: bool
        """
        return False

    def is_numeric(self) -> bool:
        """
        Whether the field is a numeric replacement field

        :return: True if the field is a numeric field, False otherwise
        :rtype: bool
        """
        return self.is_integer() or self.is_rational()


@dataclass
class DefaultField(Field):
    """
    The default field
    """

    pass


class RationalFieldType(Enum):
    """
    Represents the type of rational field

    Attributes:
        EXPONENT
        FIXED
        GENERAL
    """

    EXPONENT = "exponent"
    FIXED = "fixed"
    GENERAL = "general"


@dataclass
class RationalField(Field):
    """
    A rational replacement field

    :param precision: The number of digits after the decimal point for fixed-point notation
    :type precision: Optional[int]
    :param t: The rational field type
    :type t: RationalFieldType
    """

    precision: Optional[int]
    t: RationalFieldType

    def is_rational(self) -> bool:
        return True


class IntegerFieldType(Enum):
    """
    Represents the type of integer field

    Attributes:
        CHARACTER
        DECIMAL
        HEXADECIMAL
        OCTAL
    """

    CHARACTER = "character"
    DECIMAL = "decimal"
    HEXADECIMAL = "hexadecimal"
    OCTAL = "octal"


@dataclass
class IntegerField(Field):
    """
    An integer replacement field

    :param t: The integer field type
    :type t: IntegerFieldType
    """

    t: IntegerFieldType

    def is_integer(self) -> bool:
        return True


@dataclass
class Format:
    """
    An FPP presentation format

    :param prefix: The first part of the format, before any fields
    :type prefix: str
    :param fields: The list of pairs of fields followed by suffix strings
    :type fields: List[Tuple[Field, str]]
    """

    prefix: str
    fields: List[Tuple[Field, str]]
