"""Write a CppDoc to a cpp file"""

from __future__ import annotations
from typing import List, Optional, Callable

from fprime_python_model.codegen.cppwriter.cpp_doc import (
    CppDoc,
    Class,
    Constructor,
    Destructor,
    Function,
    FunctionParam,
    SVQualifier,
    ConstQualifier,
    Namespace,
)
from fprime_python_model.codegen.cppwriter.cpp_doc_writer import (
    CppDocWriter,
    Input,
    cpp_doc_writer_utils,
)
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


class CppDocCppWriter(CppDocWriter):
    """Write a CppDoc to a cpp file"""

    def param_string(self, p: FunctionParam) -> str:
        """Generate parameter string"""
        return f"{p.t.hpp_type} {p.name}"

    def param_string_comma(self, p: FunctionParam) -> str:
        """Generate parameter string with comma"""
        return f"{self.param_string(p)},"

    def param_line(self, p: FunctionParam) -> Line:
        """Generate parameter line"""
        return self.line(self.param_string(p))

    def param_line_comma(self, p: FunctionParam) -> Line:
        """Generate parameter line with comma"""
        return self.line(self.param_string_comma(p))

    def write_params(self, prefix: str, params: List[FunctionParam]) -> List[Line]:
        """Write parameter list"""
        if len(params) == 0:
            return self.lines(f"{prefix}()")
        elif len(params) == 1:
            return self.lines(f"{prefix}({self.param_string(params[0])})")
        else:
            # Multiple parameters
            # Reverse params, take last param (head) without comma, rest (tail) with commas
            reversed_params = list(reversed(params))
            head = reversed_params[0]
            tail = reversed_params[1:]

            # Build param lines: head without comma, tail with commas, then reverse back
            param_lines_parts = [self.param_line(head)] + [
                self.param_line_comma(p) for p in tail
            ]
            param_lines = list(reversed(param_lines_parts))

            result = [self.line(f"{prefix}(")]
            for line in param_lines:
                result.append(line.indent_in(2 * self.indent_increment))
            result.append(self.line(")"))
            return result

    def write_selected_lines(
        self,
        input_val: Input,
        selected_cpp_file_name_base_opt: Optional[str],
        lines_fn: Callable[[], List[Line]],
    ) -> List[Line]:
        """Write lines for the selected C++ file"""
        # Resolve the selected cpp file for the lines
        if selected_cpp_file_name_base_opt:
            selected_cpp_file = f"{selected_cpp_file_name_base_opt}.cpp"
        else:
            selected_cpp_file = input_val.default_cpp_file_name

        # Resolve the output cpp file
        output_cpp_file = input_val.get_output_cpp_file_name()

        # Write the lines if the two cpp files match
        if selected_cpp_file == output_cpp_file:
            return lines_fn()
        else:
            return []

    def visit_class(self, input_val: Input, c: Class) -> List[Line]:
        """Visit a class"""
        name = c.name
        new_class_name_list = [name] + input_val.class_name_list
        in1 = Input(
            hpp_file=input_val.hpp_file,
            default_cpp_file_name=input_val.default_cpp_file_name,
            output_cpp_file_name_opt=input_val.output_cpp_file_name_opt,
            class_name_list=new_class_name_list,
        )

        result = []
        for member in c.members:
            result.extend(self.visit_class_member(in1, member))
        return result

    def visit_constructor(
        self, input_val: Input, constructor: Constructor
    ) -> List[Line]:
        """Visit a constructor"""

        def generate_lines():
            unqualified_class_name = input_val.get_enclosing_class_unqualified()
            qualified_class_name = input_val.get_enclosing_class_qualified()

            name_lines = self.lines(f"{qualified_class_name} ::")
            param_lines = self.write_params(unqualified_class_name, constructor.params)

            if constructor.initializers:
                lines2 = add_suffix(param_lines, " :")
            else:
                lines2 = param_lines

            param_lines = [self.indent_in(line) for line in lines2]

            if constructor.initializers:
                reversed_inits = list(reversed(constructor.initializers))
                head = reversed_inits[0]
                tail = reversed_inits[1:]
                init_list = [head] + [f"{init}," for init in tail]
                init_list_reversed = list(reversed(init_list))
                initializer_lines = [
                    self.line(init).indent_in(2 * self.indent_increment)
                    for init in init_list_reversed
                ]
            else:
                initializer_lines = []

            body_lines = cpp_doc_writer_utils.write_function_body(constructor.body)

            return [blank()] + name_lines + param_lines + initializer_lines + body_lines

        return self.write_selected_lines(
            input_val, constructor.cpp_file_name_base_opt, generate_lines
        )

    def visit_cpp_doc(
        self, cpp_doc: CppDoc, cpp_file_name_base_opt: Optional[str] = None
    ) -> List[Line]:
        """Visit a CppDoc"""
        cpp_file_name_opt = (
            f"{cpp_file_name_base_opt}.cpp" if cpp_file_name_base_opt else None
        )
        input_val = Input(
            hpp_file=cpp_doc.hpp_file,
            default_cpp_file_name=cpp_doc.cpp_file_name,
            output_cpp_file_name_opt=cpp_file_name_opt,
        )

        result = []
        result.extend(
            cpp_doc_writer_utils.write_banner(
                cpp_doc,
                input_val.get_output_cpp_file_name(),
                f"cpp file for {cpp_doc.description}",
            )
        )

        for member in cpp_doc.members:
            result.extend(self.visit_member(input_val, member))

        return [cpp_doc_writer_utils.left_align_directive(line) for line in result]

    def visit_destructor(self, input_val: Input, destructor: Destructor) -> List[Line]:
        """Visit a destructor"""

        def generate_lines():
            unqualified_class_name = input_val.get_enclosing_class_unqualified()
            qualified_class_name = input_val.get_enclosing_class_qualified()

            start_line1 = self.line(f"{qualified_class_name} ::")
            start_line2 = self.indent_in(self.line(f"~{unqualified_class_name}()"))
            body_lines = cpp_doc_writer_utils.write_function_body(destructor.body)

            return [blank(), start_line1, start_line2] + body_lines

        return self.write_selected_lines(
            input_val, destructor.cpp_file_name_base_opt, generate_lines
        )

    def visit_function(self, input_val: Input, function: Function) -> List[Line]:
        """Visit a function"""

        def generate_lines():
            # If the function is pure virtual with no body, don't write implementation
            if (
                function.sv_qualifier == SVQualifier.PURE_VIRTUAL
                and len(function.body) == 0
            ):
                return []

            # Otherwise write out the implementation
            # Build prototype
            lines1 = self.write_params(function.name, function.params)

            # Add const qualifier using match on enum
            match function.const_qualifier:
                case ConstQualifier.CONST:
                    prototype_lines = add_suffix(lines1, " const")
                case ConstQualifier.NON_CONST:
                    prototype_lines = lines1

            # Build start lines with return type
            ret_type = (
                f"{function.ret_type.get_cpp_type()} "
                if function.ret_type.get_cpp_type()
                else ""
            )

            if input_val.class_name_list:
                # Member function
                line1 = self.line(
                    f"{ret_type}{input_val.get_enclosing_class_qualified()} ::"
                )
                start_lines = [line1] + [
                    self.indent_in(line) for line in prototype_lines
                ]
            else:
                # Standalone function
                start_lines = add_prefix(ret_type, prototype_lines)

            body_lines = cpp_doc_writer_utils.write_function_body(function.body)

            if input_val.class_name_list:
                content_lines = start_lines + body_lines
            else:
                # For standalone functions, join with a space
                content_lines = join_lists(
                    IndentMode.NO_INDENT, start_lines, " ", body_lines
                )

            return [blank()] + content_lines

        return self.write_selected_lines(
            input_val, function.cpp_file_name_base_opt, generate_lines
        )

    def visit_lines(self, input_val: Input, lines: Lines) -> List[Line]:
        """Visit lines"""
        match lines.output:
            case LinesOutput.HPP:
                return []
            case _:
                # CPP or BOTH - write to cpp
                return self.write_selected_lines(
                    input_val, lines.cpp_file_name_base_opt, lambda: lines.lines
                )

    def visit_namespace(self, input_val: Input, namespace: Namespace) -> List[Line]:
        """Visit a namespace"""
        output_lines = []
        for member in namespace.members:
            output_lines.extend(self.visit_namespace_member(input_val, member))

        # If the namespace has no members, don't write it out
        if not output_lines:
            return []

        name = namespace.name
        return (
            [blank(), self.line(f"namespace {name} {{")]
            + [self.indent_in(line) for line in output_lines]
            + [blank(), self.line("}")]
        )


# Create singleton instance
cpp_doc_cpp_writer = CppDocCppWriter()
