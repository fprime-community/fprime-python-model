"""Write a CppDoc to an hpp file"""

from __future__ import annotations
from typing import List, Optional

from fprime_python_model.codegen.cppwriter.cpp_doc import (
    CppDoc,
    Class,
    Constructor,
    Destructor,
    Function,
    FunctionParam,
    FinalQualifier,
    SVQualifier,
    ConstQualifier,
    ExplicitQualifier,
    VirtualQualifier,
    ClassMemberLines,
    MemberLines,
)
from fprime_python_model.codegen.cppwriter.cpp_doc_writer import (
    CppDocWriter,
    Input,
    cpp_doc_writer_utils,
)
from fprime_python_model.codegen.cppwriter.cpp_doc_cpp_writer import cpp_doc_cpp_writer
from fprime_python_model.utils.line_utils import (
    Line,
    Lines,
    LinesOutput,
    blank,
    join_lists,
    IndentMode,
    add_suffix,
    add_prefix,
)


class CppDocHppWriter(CppDocWriter):
    """Write a CppDoc to an hpp file"""

    def add_param_comment(self, s: str, comment_opt: Optional[str]) -> List[Line]:
        """Add parameter comment"""
        if comment_opt:
            ls = cpp_doc_writer_utils.write_doxygen_post_comment(comment_opt)
            # Join the parameter string with the comment using join_lists
            return join_lists(IndentMode.INDENT, self.lines(s), " ", ls)
        else:
            return self.lines(s)

    def add_param_default(self, s: str, default_opt: Optional[str]) -> str:
        """Add default value to parameter"""
        if default_opt:
            return f"{s} = {default_opt}"
        else:
            return s

    def open_include_guard(self, guard: str) -> List[Line]:
        """Generate opening include guard"""
        return self.lines(f"""
|#ifndef {guard}
|#define {guard}""")

    def close_include_guard(self) -> List[Line]:
        """Generate closing include guard"""
        return self.lines("""
|#endif""")

    def param_string(self, p: FunctionParam) -> str:
        """Generate parameter string"""
        s1 = cpp_doc_cpp_writer.param_string(p)
        return self.add_param_default(s1, p.default)

    def param_lines(self, p: FunctionParam) -> List[Line]:
        """Generate parameter lines"""
        return self.add_param_comment(self.param_string(p), p.comment)

    def param_lines_comma(self, p: FunctionParam) -> List[Line]:
        """Generate parameter lines with comma"""
        return self.add_param_comment(f"{self.param_string(p)},", p.comment)

    def write_access_tag(self, tag: str) -> List[Line]:
        """Write access tag (public, private, protected)"""
        return [blank(), self.line(f"{tag}:").indent_out(2)]

    def write_params(self, prefix: str, params: List[FunctionParam]) -> List[Line]:
        """Write parameter list"""
        if len(params) == 0:
            return self.lines(f"{prefix}()")
        elif len(params) == 1 and params[0].comment is None:
            return self.lines(f"{prefix}({self.param_string(params[0])})")
        else:
            head, *tail = reversed(params)
            params_lines_list = [self.param_lines(head)] + [
                self.param_lines_comma(p) for p in tail
            ]
            params_lines = [
                line for part in reversed(params_lines_list) for line in part
            ]
            return (
                [self.line(f"{prefix}(")]
                + [line.indent_in(2 * self.indent_increment) for line in params_lines]
                + [self.line(")")]
            )

    def visit_class(self, input_val: Input, c: Class) -> List[Line]:
        """Visit a class"""
        name = c.name
        comment_lines = cpp_doc_writer_utils.write_doxygen_comment_opt(c.comment)

        # Build class declaration
        if c.qualifier == FinalQualifier.FINAL:
            class_name = f"class {name} final"
        else:
            class_name = f"class {name}"

        # Handle superclass declarations
        if c.superclass_decls:
            open_lines = [
                self.line(f"{class_name} :"),
                self.indent_in(self.line(c.superclass_decls)),
                self.line("{"),
            ]
        else:
            open_lines = self.lines(f"{class_name} {{")

        # Process class members
        new_class_name_list = [name] + input_val.class_name_list
        in1 = Input(
            hpp_file=input_val.hpp_file,
            default_cpp_file_name=input_val.default_cpp_file_name,
            output_cpp_file_name_opt=input_val.output_cpp_file_name_opt,
            class_name_list=new_class_name_list,
        )

        body_lines = []
        for member in c.members:
            body_lines.extend(self.visit_class_member(in1, member))

        body_lines = [line.indent_in(2 * self.indent_increment) for line in body_lines]

        close_lines = [blank(), self.line("};")]

        return comment_lines + open_lines + body_lines + close_lines

    def visit_constructor(
        self, input_val: Input, constructor: Constructor
    ) -> List[Line]:
        """Visit a constructor"""
        unqualified_class_name = input_val.get_enclosing_class_unqualified()
        lines1 = cpp_doc_writer_utils.write_doxygen_comment_opt(constructor.comment)

        params = self.write_params(unqualified_class_name, constructor.params)
        name_and_params = add_suffix(params, ";")

        if constructor.explicit_qualifier == ExplicitQualifier.EXPLICIT:
            lines2 = add_prefix("explicit ", name_and_params)
        else:
            lines2 = name_and_params

        return lines1 + lines2

    def visit_cpp_doc(
        self, cpp_doc: CppDoc, cpp_file_name_base_opt: Optional[str] = None
    ) -> List[Line]:
        """Visit a CppDoc"""
        hpp_file = cpp_doc.hpp_file
        cpp_file_name = cpp_doc.cpp_file_name
        input_val = Input(hpp_file=hpp_file, default_cpp_file_name=cpp_file_name)

        ext = hpp_file.name.split(".")[-1]

        result = []
        result.extend(
            cpp_doc_writer_utils.write_banner(
                cpp_doc,
                input_val.hpp_file.name,
                f"{ext} file for {cpp_doc.description}",
            )
        )
        result.extend(self.open_include_guard(hpp_file.include_guard))

        for member in cpp_doc.members:
            result.extend(self.visit_member(input_val, member))

        result.extend(self.close_include_guard())

        return [cpp_doc_writer_utils.left_align_directive(line) for line in result]

    def visit_destructor(self, input_val: Input, destructor: Destructor) -> List[Line]:
        """Visit a destructor"""
        unqualified_class_name = input_val.get_enclosing_class_unqualified()

        lines1 = cpp_doc_writer_utils.write_doxygen_comment_opt(destructor.comment)

        if destructor.virtual_qualifier == VirtualQualifier.VIRTUAL:
            lines2 = self.lines(f"virtual ~{unqualified_class_name}();")
        else:
            lines2 = self.lines(f"~{unqualified_class_name}();")

        return lines1 + lines2

    def visit_function(self, input_val: Input, function: Function) -> List[Line]:
        """Visit a function"""
        comment_lines = cpp_doc_writer_utils.write_doxygen_comment_opt(function.comment)

        match function.sv_qualifier:
            case SVQualifier.PURE_VIRTUAL:
                sv_prefix = "virtual "
            case SVQualifier.STATIC:
                sv_prefix = "static "
            case SVQualifier.VIRTUAL:
                sv_prefix = "virtual "
            case _:
                sv_prefix = ""

        match function.ret_type.hpp_type:
            case "":
                ret_type = ""
            case t:
                ret_type = f"{t} "

        name_prefix = f"{sv_prefix}{ret_type}{function.name}"

        params_lines = self.write_params(name_prefix, function.params)

        match function.const_qualifier:
            case ConstQualifier.CONST:
                with_const = add_suffix(params_lines, " const")
            case _:
                with_const = params_lines

        match function.sv_qualifier:
            case SVQualifier.FINAL:
                with_qualifiers = add_suffix(with_const, " final")
            case SVQualifier.OVERRIDE:
                with_qualifiers = add_suffix(with_const, " override")
            case _:
                with_qualifiers = with_const

        match function.sv_qualifier:
            case SVQualifier.PURE_VIRTUAL:
                terminator = self.lines(" = 0;")
            case _:
                terminator = self.lines(";")

        signature_lines = join_lists(
            IndentMode.NO_INDENT, with_qualifiers, "", terminator
        )
        return comment_lines + signature_lines

    def visit_lines(self, input_val: Input, lines: Lines) -> List[Line]:
        """Visit lines"""
        content = lines.lines
        match lines.output:
            case LinesOutput.HPP:
                return content
            case LinesOutput.CPP:
                return []
            case LinesOutput.BOTH:
                return content
            case _:
                raise ValueError(f"Invalid LinesOutput value: {lines.output}")


# Create singleton instance
cpp_doc_hpp_writer = CppDocHppWriter()
