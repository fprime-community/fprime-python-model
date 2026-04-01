"""Write a Cpp doc as hpp or cpp"""

from __future__ import annotations
from abc import abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional

from fprime_python_model.codegen.cppwriter.cpp_doc import CppDoc, HppFile, Namespace
from fprime_python_model.codegen.cppwriter.cpp_doc_visitor import CppDocVisitor
from fprime_python_model.utils.line_utils import Line, LineUtils, join, blank


@dataclass
class Input:
    """Input context for CppDocWriter"""

    hpp_file: HppFile
    default_cpp_file_name: str
    output_cpp_file_name_opt: Optional[str] = None
    class_name_list: List[str] = field(
        default_factory=list
    )  # List of enclosing class names, backwards

    def get_enclosing_class_qualified(self) -> str:
        """Get the enclosing class name, including any qualifier"""
        return "::".join(reversed(self.class_name_list))

    def get_enclosing_class_unqualified(self) -> str:
        """Get the enclosing class name with no qualifier"""
        return self.class_name_list[0].split("::")[-1]

    def get_output_cpp_file_name(self) -> str:
        """Get the output cpp file name"""
        return (
            self.output_cpp_file_name_opt
            if self.output_cpp_file_name_opt
            else self.default_cpp_file_name
        )


class CppDocWriter(CppDocVisitor[Input, List[Line]], LineUtils):
    """Write a Cpp doc as hpp or cpp"""

    def __init__(self):
        LineUtils.__init__(self)

    def default(self, input_val: Input) -> List[Line]:
        """Default returns empty list"""
        return []

    @abstractmethod
    def visit_cpp_doc(
        self, cpp_doc: CppDoc, cpp_file_name_base_opt: Optional[str] = None
    ) -> List[Line]:
        """Visit a CppDoc"""
        raise NotImplementedError

    def visit_namespace(self, input_val: Input, namespace: Namespace) -> List[Line]:
        """Visit a namespace"""
        name = namespace.name
        start_lines = [blank(), self.line(f"namespace {name} {{")]
        output_lines = []
        for member in namespace.members:
            output_lines.extend(self.visit_namespace_member(input_val, member))
        end_lines = [blank(), self.line("}")]
        return start_lines + [self.indent_in(line) for line in output_lines] + end_lines


# Static utility methods
class CppDocWriterUtils(LineUtils):
    """Static utility methods for CppDocWriter"""

    def __init__(self):
        LineUtils.__init__(self)

    def write_banner_comment(self, comment: str) -> List[Line]:
        """Write a banner comment"""
        banner = self.line(
            "// ----------------------------------------------------------------------"
        )
        return [blank(), banner] + self.write_comment_body(comment) + [banner]

    def write_comment(self, comment: str) -> List[Line]:
        """Write a comment"""
        return [blank()] + self.write_comment_body(comment)

    def write_doxygen_comment_opt(self, comment_opt: Optional[str]) -> List[Line]:
        """Write an optional Doxygen comment"""
        if comment_opt:
            return self.write_doxygen_comment(comment_opt)
        else:
            return [blank()]

    def write_doxygen_post_comment_opt(self, comment_opt: Optional[str]) -> List[Line]:
        """Write an optional Doxygen post comment"""
        if comment_opt:
            return self.write_doxygen_post_comment(comment_opt)
        else:
            return [blank()]

    def add_comment_prefix(self, prefix: str, line: Line) -> Line:
        """Add a prefix to a comment line"""
        if line.string == "":
            return self.line(prefix)
        else:
            return join(" ", self.line(prefix), line)

    def write_doxygen_comment(self, comment: str) -> List[Line]:
        """Write a Doxygen comment"""
        return [blank()] + [
            self.add_comment_prefix("//!", line) for line in self.lines(comment)
        ]

    def write_doxygen_post_comment(self, comment: str) -> List[Line]:
        """Write a Doxygen post comment"""
        return [self.add_comment_prefix("//!<", line) for line in self.lines(comment)]

    def write_comment_body(self, comment: str) -> List[Line]:
        """Write a comment body"""
        return [self.add_comment_prefix("//", line) for line in self.lines(comment)]

    def left_align_directive(self, line: Line) -> Line:
        """Left align a compiler directive"""
        if line.string.startswith("#"):
            return Line(line.string)
        else:
            return line

    def write_banner(
        self, cpp_doc: CppDoc, file_name: str, generic_description: str
    ) -> List[Line]:
        """Write a header banner"""
        file_banner = cpp_doc.get_file_banner()
        title = file_banner.get_title(file_name)
        author = file_banner.get_author(file_name)
        description = file_banner.get_description(file_name, generic_description)

        banner_text = f"""|// ======================================================================
|// \\title  {title}
|// \\author {author}
|// \\brief  {description}
|// ======================================================================"""
        return self.lines(banner_text)

    def write_function_body(self, body: List[Line]) -> List[Line]:
        """Write a function body"""
        if len(body) == 0:
            body_lines = [blank()]
        else:
            body_lines = [self.indent_in(line) for line in body]
        return [self.line("{")] + body_lines + [self.line("}")]


# Create a singleton instance for use by other modules
cpp_doc_writer_utils = CppDocWriterUtils()
