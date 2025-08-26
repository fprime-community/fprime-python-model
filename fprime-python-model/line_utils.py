from typing import List, Union, Callable
from dataclasses import dataclass
from enum import Enum


@dataclass
class Indentation:
    value: int = 0

    def indent_in(self, n: int) -> "Indentation":
        return Indentation(self.value + n)

    def indent_out(self, n: int) -> "Indentation":
        return Indentation(max(self.value - n, 0))

    def __int__(self):
        return self.value

    def __str__(self):
        return " " * self.value


class Line:

    def __init__(self, string: str, indent: Indentation = Indentation(0)):
        self.string = string
        self.indent = indent

    def __str__(self):
        return "" if self.string == "" else f"{self.indent}{self.string}"

    def indent_in(self, n: int) -> "Line":
        return Line(self.string, self.indent.indent_in(n))

    def indent_out(self, n: int) -> "Line":
        return Line(self.string, self.indent.indent_out(n))

    def indent_to(self, n: int) -> "Line":
        return Line(self.string, Indentation(n))

    def get_size(self) -> int:
        return int(self.indent) + len(self.string)


class IndentMode(Enum):
    INDENT = "Indent"
    NO_INDENT = "NoIndent"


def join(sep: str, l1: Line, l2: Line) -> Line:
    indent = l1.indent
    string = l1.string + sep + l2.string
    return Line(string, indent)


def flatten(sep: str, lines: List[Line]) -> Line:
    if not lines:
        return Line()
    elif len(lines) == 1:
        return lines[0]
    else:
        head = lines[0]
        tail = flatten(sep, lines[1:])
        return join(sep, head, tail)


def join_lists(
    mode: IndentMode, lines1: List[Line], sep: str, lines2: List[Line]
) -> List[Line]:
    if not lines2:
        return lines1
    elif not lines1:
        return lines2
    else:
        l1_rev = list(reversed(lines1))
        hd1 = l1_rev[0]
        tl1 = l1_rev[1:]
        part1 = list(reversed(tl1))

        hd2, *tl2 = lines2
        part2 = join(sep, hd1, hd2)

        if mode == IndentMode.INDENT:
            indent = hd1.get_size() + len(sep)
            part3 = [line.indent_in(indent) for line in tl2]
        else:
            part3 = tl2

        return part1 + [part2] + part3


def add_prefix(prefix: str, ls: List[Line]) -> List[Line]:
    return join_lists(IndentMode.NO_INDENT, [Line(prefix)], "", ls)


def add_suffix(ls: List[Line], suffix: str) -> List[Line]:
    return join_lists(IndentMode.NO_INDENT, ls, "", [Line(suffix)])


def add_prefix_and_suffix(prefix: str, ls: List[Line], suffix: str) -> List[Line]:
    return add_prefix(prefix, add_suffix(ls, suffix))


def add_prefix_indent(prefix: str, ls: List[Line]) -> List[Line]:
    return join_lists(IndentMode.INDENT, [Line(prefix)], "", ls)


def add_prefix_line(prefix: Line, ll: List[Line]) -> List[Line]:
    return [prefix] + ll if ll else ll


def add_postfix_line(postfix: Line, ll: List[Line]) -> List[Line]:
    return ll + [postfix] if ll else ll


def flatten_with_prefix_line(prefix: Line, lll: List[List[Line]]) -> List[Line]:
    result = []
    for ll in lll:
        result.extend(add_prefix_line(prefix, ll))
    return result


def blank() -> Line:
    return Line()


def write(line: Line):
    print(str(line) + "\n")


def blank_separated(f: Callable[[any], List[Line]], ts: List[any]) -> List[Line]:
    if not ts:
        return []
    elif len(ts) == 1:
        return f(ts[0])
    else:
        head1 = f(ts[0])
        tail1 = blank_separated(f, ts[1:])
        return head1 + [blank()] + tail1


class LineUtils:
    indent_increment = 2
    q = '"'

    def indent_in(self, line: Line) -> Line:
        return line.indent_in(self.indent_increment)

    def line(self, s: str) -> Line:
        return Line(s)

    def lines(self, s: str) -> list[Line]:
        stripped = "\n".join(
            line[line.find("|") + 1 :] if "|" in line else line
            for line in s.split("\n")
        )
        return [self.line(line) for line in stripped.split("\n")]

    def lines_opt(self, f, o):
        if o is None:
            return []
        else:
            return f(o)

    add_blank_prefix = staticmethod(lambda lines: add_prefix_line(blank(), lines))
    add_blank_postfix = staticmethod(lambda lines: add_postfix_line(blank(), lines))
    flatten_with_blank_prefix = staticmethod(
        lambda lists: flatten_with_prefix_line(blank(), lists)
    )

    def intersperse_list(self, l: list, element) -> list:
        if len(l) < 2:
            return l
        result = []
        for item in l[:-1]:
            result.append(item)
            result.append(element)
        result.append(l[-1])
        return result

    def intersperse_blank_lines(self, l: list[list[Line]]) -> list[Line]:
        filtered = [lines for lines in l if lines]
        interspersed = self.intersperse_list(filtered, [Line.blank])
        return [line for sublist in interspersed for line in sublist]
