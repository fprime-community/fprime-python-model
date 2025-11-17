from __future__ import annotations
from typing import List, Callable, Optional, Any
from dataclasses import dataclass
from enum import Enum


@dataclass
class Indentation:
    value: int = 0

    def indent_in(self, n: int) -> Indentation:
        return Indentation(self.value + n)

    def indent_out(self, n: int) -> Indentation:
        return Indentation(max(self.value - n, 0))

    def __str__(self) -> str:
        return " " * self.value


class Line:
    def __init__(self, string: str = "", indent: Indentation | None = None):
        self.string = string
        self.indent = indent or Indentation(0)

    def __str__(self) -> str:
        return f"{self.indent}{self.string}" if self.string else ""

    def indent_in(self, n: int) -> Line:
        return Line(self.string, self.indent.indent_in(n))

    def indent_out(self, n: int) -> Line:
        return Line(self.string, self.indent.indent_out(n))

    def indent_to(self, n: int) -> Line:
        return Line(self.string, Indentation(n))

    def get_size(self) -> int:
        return int(self.indent.value) + len(self.string)


class IndentMode(Enum):
    INDENT = "Indent"
    NO_INDENT = "NoIndent"


@dataclass
class Lines: # TODO rename to JoinOpts
    lines: List[Line]

    def __iter__(self):
        return iter(self.lines)

    def __add__(self, other: Lines) -> Lines:
        return Lines(self.lines + other.lines)

    def __bool__(self):
        return bool(self.lines)

    def __str__(self) -> str:
        return "\n".join(str(l) for l in self.lines)

    def add_suffix(self, suffix: str) -> Lines:
        return self.join("", Lines([Line(suffix)]), False)

    def add_prefix(self, prefix: str) -> Lines:
        return Lines([Line(prefix)]).join("", self, False)

    def add_prefix_and_suffix(self, prefix: str, suffix: str) -> Lines:
        return self.add_prefix(prefix, self.add_suffix(self, suffix))

    def join(self, sep: str, other: Lines, indent: bool = True) -> Lines: # avoid passing boolean into func
        if not other:
            return self

        *prefix, last1 = self.lines
        first2, *rest2 = other.lines
        joined = join(sep, last1, first2)

        if indent:
            indent_size = last1.get_size() + len(sep)
            rest2 = [ln.indent_in(indent_size) for ln in rest2]

        return Lines(prefix + [joined] + rest2)

    def join_no_indent(self, sep: str, other: Lines) -> Lines:
        return self.join(sep, other, indent=False)

    def join_with_break(self, sep: str, other: Lines) -> Lines:
        if not other.lines and not sep:
            return self
        result = add_suffix(self.lines, " \\")
        result += [Line(sep + l.string, l.indent.indent_in(2)) for l in other.lines]
        return Lines(result)

    def join_opt(
        self, opt: Optional[Any], sep: str, f: Callable[[Any], Lines]
    ) -> Lines:
        return self if opt is None else self.join(sep, f(opt))

    def join_opt_with_break(
        self, opt: Optional[Any], sep: str, f: Callable[[Any], Lines]
    ) -> Lines:
        return self if opt is None else self.join_with_break(sep, f(opt))


def join(sep: str, l1: Line, l2: Line) -> Line:
    """Join two lines with a separator."""
    return Line(l1.string + sep + l2.string, l1.indent)


def join_lists(
    mode: IndentMode, l1: List[Line], sep: str, l2: List[Line]
) -> List[Line]:
    """Join two lists of lines respecting indentation."""
    if not l1:
        return l2
    if not l2:
        return l1

    *prefix, last1 = l1
    first2, *rest2 = l2
    joined = join(sep, last1, first2)

    if mode == IndentMode.INDENT:
        indent_size = last1.get_size() + len(sep)
        rest2 = [ln.indent_in(indent_size) for ln in rest2]

    return prefix + [joined] + rest2


def add_prefix(prefix: str, ls: List[Line]) -> List[Line]:
    """Prepend a prefix string as its own line."""
    return join_lists(IndentMode.NO_INDENT, [Line(prefix)], "", ls)


def add_suffix(ls: List[Line], suffix: str) -> List[Line]:
    """Append a suffix string as its own line."""
    return join_lists(IndentMode.NO_INDENT, ls, "", [Line(suffix)])


def add_prefix_and_suffix(prefix: str, ls: List[Line], suffix: str) -> List[Line]:
    return add_prefix(prefix, add_suffix(ls, suffix))


def blank() -> Line:
    return Line("")


def blank_separated(f: Callable[[Any], List[Line]], items: List[Any]) -> List[Line]:
    """Apply f to each item and insert blank lines between results."""
    if not items:
        return []
    result = []
    for i, item in enumerate(items):
        result.extend(f(item))
        if i < len(items) - 1:
            result.append(blank())
    return result


class LineUtils:
    """Convenience utilities for manipulating Lines."""

    indent_increment = 2
    q = '"'

    def indent_in(self, line: Line) -> Line:
        return line.indent_in(self.indent_increment)

    def line(self, s: str) -> Line:
        return Line(s)

    def lines(self, s: str) -> List[Line]:
        """Create multiple lines from a string, removing leading '|' markers."""
        stripped = "\n".join(
            part.split("|", 1)[1] if "|" in part else part for part in s.split("\n")
        )
        return [self.line(line) for line in stripped.split("\n")]

    def lines_opt(self, f: Callable, o: Optional[Any]) -> List[Line]:
        return [] if o is None else f(o)
