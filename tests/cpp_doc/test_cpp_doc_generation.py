"""Integration tests for CppDoc code generation (translated from Main.scala)"""

import unittest
from fprime_python_model.codegen.cppwriter.cpp_doc import (
    CppDoc, HppFile, Class, Function, Constructor, Destructor,
    FunctionParam, Type, Namespace,
    MemberClass, MemberFunction, MemberNamespace, MemberLines,
    ClassMemberClass, ClassMemberConstructor, ClassMemberDestructor,
    ClassMemberFunction, ClassMemberLines,
    FinalQualifier, ExplicitQualifier, VirtualQualifier, SVQualifier,
    ConstQualifier
)
from fprime_python_model.codegen.cppwriter.cpp_doc_hpp_writer import cpp_doc_hpp_writer
from fprime_python_model.codegen.cppwriter.cpp_doc_cpp_writer import cpp_doc_cpp_writer
from fprime_python_model.codegen.cppwriter.cpp_doc_writer import cpp_doc_writer_utils
from fprime_python_model.utils.line_utils import Line, Lines, LineUtils, LinesOutput, blank
from tests.cpp_doc.test_utils import compile_and_assert, assert_matches_gold_standard


class TestCppDocGeneration(unittest.TestCase):
    """Test C++ code generation from CppDoc structures"""

    def setUp(self):
        """Set up test fixtures"""
        self.line_utils = LineUtils()

        # Create include header lines
        include_header = [
            blank(),
            self.line_utils.line('#include "C.hpp"')
        ]

        # Build the CppDoc structure (translated from Main.scala)
        self.cpp_doc = CppDoc(
            description="CppDoc test",
            hpp_file=HppFile(name="C.hpp", include_guard="N_C_HPP"),
            cpp_file_name="C.cpp",
            members=[
                # Lines for cpp only
                MemberLines(lines=Lines(lines=include_header, output=LinesOutput.CPP)),

                # Lines for Other.cpp
                MemberLines(lines=Lines(
                    lines=include_header,
                    output=LinesOutput.CPP,
                    cpp_file_name_base_opt="Other"
                )),

                # Namespace N with class C
                MemberNamespace(
                    namespace=Namespace(
                        name="N",
                        members=[
                            MemberClass(
                                c=Class(
                                    comment=None,
                                    name="C",
                                    superclass_decls=None,
                                    members=[
                                        # Public access tag
                                        ClassMemberLines(
                                            lines=Lines(lines=cpp_doc_hpp_writer.write_access_tag("public"))
                                        ),

                                        # Nested class banner comment
                                        ClassMemberLines(
                                            lines=Lines(
                                                lines=cpp_doc_writer_utils.write_banner_comment("Nested class"),
                                                output=LinesOutput.BOTH
                                            )
                                        ),

                                        # Nested class N
                                        ClassMemberClass(
                                            c=Class(
                                                comment=None,
                                                name="N",
                                                superclass_decls=None,
                                                members=[
                                                    ClassMemberLines(
                                                        lines=Lines(
                                                            lines=cpp_doc_hpp_writer.write_access_tag("public")
                                                        )
                                                    ),
                                                    ClassMemberConstructor(
                                                        constructor=Constructor(
                                                            comment="This is line 1.\n\nThis is line 3.",
                                                            params=[],
                                                            initializers=[],
                                                            body=[
                                                                self.line_utils.line("// line1"),
                                                                self.line_utils.line("// line2")
                                                            ]
                                                        )
                                                    ),
                                                    ClassMemberDestructor(
                                                        destructor=Destructor(
                                                            comment="This is line 1.\nThis is line 2.",
                                                            body=[
                                                                self.line_utils.line("// Body line 1"),
                                                                self.line_utils.line("// Body line 2")
                                                            ]
                                                        )
                                                    ),
                                                    ClassMemberFunction(
                                                        function=Function(
                                                            comment="This is line 1.\nThis is line 2.",
                                                            name="f",
                                                            params=[
                                                                FunctionParam(
                                                                    t=Type(hpp_type="const double"),
                                                                    name="x",
                                                                    comment="This is parameter x line 1.\n\nThis is parameter x line 3."
                                                                ),
                                                                FunctionParam(
                                                                    t=Type(hpp_type="const int"),
                                                                    name="y",
                                                                    comment="This is parameter y line 1.\nThis is parameter y line 2."
                                                                )
                                                            ],
                                                            ret_type=Type(hpp_type="void"),
                                                            body=[],
                                                            cpp_file_name_base_opt="Other"
                                                        )
                                                    )
                                                ]
                                            )
                                        ),

                                        # Constructors and destructors banner
                                        ClassMemberLines(
                                            lines=Lines(
                                                lines=cpp_doc_writer_utils.write_banner_comment("Consructors and destructors"),
                                                output=LinesOutput.BOTH
                                            )
                                        ),

                                        # Constructor with parameters
                                        ClassMemberConstructor(
                                            constructor=Constructor(
                                                comment="This is line 1.\nThis is line 2.",
                                                params=[
                                                    FunctionParam(
                                                        t=Type(hpp_type="const double"),
                                                        name="x",
                                                        comment="This is parameter x"
                                                    ),
                                                    FunctionParam(
                                                        t=Type(hpp_type="const int"),
                                                        name="y",
                                                        comment="This is parameter y"
                                                    )
                                                ],
                                                initializers=["x(x)", "y(y)"],
                                                body=[
                                                    self.line_utils.line("// line1"),
                                                    self.line_utils.line("// line2")
                                                ]
                                            )
                                        ),

                                        # Destructor
                                        ClassMemberDestructor(
                                            destructor=Destructor(
                                                comment="This is line 1.\nThis is line 2.",
                                                body=[
                                                    self.line_utils.line("// Body line 1"),
                                                    self.line_utils.line("// Body line 2")
                                                ]
                                            )
                                        ),

                                        # Public member functions
                                        ClassMemberLines(
                                            lines=Lines(
                                                lines=cpp_doc_hpp_writer.write_access_tag("public")
                                            )
                                        ),

                                        ClassMemberLines(
                                            lines=Lines(
                                                lines=cpp_doc_writer_utils.write_banner_comment("Public member functions"),
                                                output=LinesOutput.BOTH
                                            )
                                        ),

                                        # Function f with default parameters
                                        ClassMemberFunction(
                                            function=Function(
                                                comment="This is line 1.\nThis is line 2.",
                                                name="f",
                                                params=[
                                                    FunctionParam(
                                                        t=Type(hpp_type="const double"),
                                                        name="x",
                                                        comment="This is parameter x",
                                                        default="0.0"
                                                    ),
                                                    FunctionParam(
                                                        t=Type(hpp_type="const int"),
                                                        name="y",
                                                        comment="This is parameter y",
                                                        default="0"
                                                    )
                                                ],
                                                ret_type=Type(hpp_type="void"),
                                                body=[]
                                            )
                                        ),

                                        # Pure virtual const function
                                        ClassMemberFunction(
                                            function=Function(
                                                comment="This is line 1.\nThis is line 2.",
                                                name="g",
                                                params=[],
                                                ret_type=Type(hpp_type="void"),
                                                body=[],
                                                sv_qualifier=SVQualifier.PURE_VIRTUAL,
                                                const_qualifier=ConstQualifier.CONST
                                            )
                                        ),

                                        # Private member variables
                                        ClassMemberLines(
                                            lines=Lines(
                                                lines=(
                                                    cpp_doc_hpp_writer.write_access_tag("private") +
                                                    cpp_doc_writer_utils.write_banner_comment("Private member variables") +
                                                    cpp_doc_writer_utils.write_doxygen_comment("Member variable x") +
                                                    self.line_utils.lines("double x;") +
                                                    cpp_doc_writer_utils.write_doxygen_comment("Member variable y") +
                                                    self.line_utils.lines("int y;")
                                                )
                                            )
                                        )
                                    ]
                                )
                            )
                        ]
                    )
                ),

                # Namespace M with class M
                MemberNamespace(
                    namespace=Namespace(
                        name="M",
                        members=[
                            MemberClass(
                                c=Class(
                                    comment=None,
                                    name="M",
                                    superclass_decls=None,
                                    members=[
                                        ClassMemberLines(
                                            lines=Lines(
                                                lines=cpp_doc_hpp_writer.write_access_tag("public")
                                            )
                                        ),
                                        ClassMemberConstructor(
                                            constructor=Constructor(
                                                comment="This is line 1.\n\nThis is line 3.",
                                                params=[],
                                                initializers=[],
                                                body=[
                                                    self.line_utils.line("// line1"),
                                                    self.line_utils.line("// line2")
                                                ],
                                                explicit_qualifier=ExplicitQualifier.NOT_EXPLICIT,
                                                cpp_file_name_base_opt="Other"
                                            )
                                        ),
                                        ClassMemberDestructor(
                                            destructor=Destructor(
                                                comment="This is line 1.\nThis is line 2.",
                                                body=[
                                                    self.line_utils.line("// Body line 1"),
                                                    self.line_utils.line("// Body line 2")
                                                ],
                                                virtual_qualifier=VirtualQualifier.VIRTUAL,
                                                cpp_file_name_base_opt="Other"
                                            )
                                        )
                                    ]
                                )
                            )
                        ]
                    )
                )
            ]
        )

    def test_generate_hpp(self):
        """Test HPP file generation matches gold standard"""
        hpp_output = cpp_doc_hpp_writer.visit_cpp_doc(self.cpp_doc)

        # Compare against gold standard
        assert_matches_gold_standard(self, hpp_output, "C.hpp")

    def test_generate_cpp(self):
        """Test CPP file generation matches gold standard and compiles"""
        hpp_output = cpp_doc_hpp_writer.visit_cpp_doc(self.cpp_doc)
        cpp_output = cpp_doc_cpp_writer.visit_cpp_doc(self.cpp_doc)

        # Compare against gold standard
        assert_matches_gold_standard(self, cpp_output, "C.cpp")

        # Verify it compiles with header
        compile_and_assert(self, {
            "C.hpp": hpp_output,
            "C.cpp": cpp_output
        })

    def test_generate_other_cpp(self):
        """Test Other.cpp file generation matches gold standard and compiles"""
        hpp_output = cpp_doc_hpp_writer.visit_cpp_doc(self.cpp_doc)
        other_cpp_output = cpp_doc_cpp_writer.visit_cpp_doc(self.cpp_doc, cpp_file_name_base_opt="Other")

        # Compare against gold standard
        assert_matches_gold_standard(self, other_cpp_output, "Other.cpp")

        # Verify it compiles with header
        compile_and_assert(self, {
            "C.hpp": hpp_output,
            "Other.cpp": other_cpp_output
        })


if __name__ == '__main__':
    unittest.main()
