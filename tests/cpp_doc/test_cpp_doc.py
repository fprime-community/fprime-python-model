"""Tests for CppDoc data classes"""

import unittest
from fprime_python_model.codegen.cppwriter.cpp_doc import (
    CppDoc, HppFile, Class, Function, Constructor, Destructor,
    FunctionParam, Type, Namespace, Member, MemberClass, MemberFunction,
    MemberNamespace, ClassMember, ClassMemberClass, ClassMemberConstructor,
    ClassMemberDestructor, ClassMemberFunction, ClassMemberLines,
    FinalQualifier, ExplicitQualifier, VirtualQualifier, SVQualifier,
    ConstQualifier, FileBanner, DefaultFileBanner
)
from fprime_python_model.utils.line_utils import Line, Lines


class TestHppFile(unittest.TestCase):
    """Test HppFile class"""

    def test_create_hpp_file(self):
        hpp = HppFile(name="MyClass.hpp", include_guard="MY_CLASS_HPP")
        self.assertEqual(hpp.name, "MyClass.hpp")
        self.assertEqual(hpp.include_guard, "MY_CLASS_HPP")


class TestType(unittest.TestCase):
    """Test Type class"""

    def test_type_with_only_hpp_type(self):
        t = Type(hpp_type="int")
        self.assertEqual(t.hpp_type, "int")
        self.assertEqual(t.get_cpp_type(), "int")

    def test_type_with_different_cpp_type(self):
        t = Type(hpp_type="String", cpp_type="std::string")
        self.assertEqual(t.hpp_type, "String")
        self.assertEqual(t.cpp_type, "std::string")
        self.assertEqual(t.get_cpp_type(), "std::string")


class TestFunctionParam(unittest.TestCase):
    """Test FunctionParam class"""

    def test_simple_param(self):
        t = Type(hpp_type="int")
        param = FunctionParam(t=t, name="value")
        self.assertEqual(param.name, "value")
        self.assertEqual(param.t.hpp_type, "int")
        self.assertIsNone(param.comment)
        self.assertIsNone(param.default)

    def test_param_with_default(self):
        t = Type(hpp_type="bool")
        param = FunctionParam(t=t, name="flag", default="true", comment="Enable feature")
        self.assertEqual(param.default, "true")
        self.assertEqual(param.comment, "Enable feature")


class TestFunction(unittest.TestCase):
    """Test Function class"""

    def test_simple_function(self):
        ret_type = Type(hpp_type="void")
        func = Function(
            comment="Does something",
            name="doSomething",
            params=[],
            ret_type=ret_type,
            body=[]
        )
        self.assertEqual(func.name, "doSomething")
        self.assertEqual(func.sv_qualifier, SVQualifier.NON_SV)
        self.assertEqual(func.const_qualifier, ConstQualifier.NON_CONST)

    def test_function_with_qualifiers(self):
        ret_type = Type(hpp_type="int")
        param = FunctionParam(t=Type(hpp_type="int"), name="x")
        func = Function(
            comment=None,
            name="getValue",
            params=[param],
            ret_type=ret_type,
            body=[],
            sv_qualifier=SVQualifier.VIRTUAL,
            const_qualifier=ConstQualifier.CONST
        )
        self.assertEqual(func.sv_qualifier, SVQualifier.VIRTUAL)
        self.assertEqual(func.const_qualifier, ConstQualifier.CONST)
        self.assertEqual(len(func.params), 1)


class TestConstructor(unittest.TestCase):
    """Test Constructor class"""

    def test_default_constructor(self):
        ctor = Constructor(
            comment="Default constructor",
            params=[],
            initializers=[],
            body=[]
        )
        self.assertEqual(ctor.explicit_qualifier, ExplicitQualifier.NOT_EXPLICIT)
        self.assertIsNone(ctor.cpp_file_name_base_opt)

    def test_explicit_constructor(self):
        param = FunctionParam(t=Type(hpp_type="int"), name="value")
        ctor = Constructor(
            comment="Explicit constructor",
            params=[param],
            initializers=["m_value(value)"],
            body=[],
            explicit_qualifier=ExplicitQualifier.EXPLICIT
        )
        self.assertEqual(ctor.explicit_qualifier, ExplicitQualifier.EXPLICIT)
        self.assertEqual(len(ctor.initializers), 1)


class TestDestructor(unittest.TestCase):
    """Test Destructor class"""

    def test_non_virtual_destructor(self):
        dtor = Destructor(
            comment="Destructor",
            body=[]
        )
        self.assertEqual(dtor.virtual_qualifier, VirtualQualifier.NON_VIRTUAL)

    def test_virtual_destructor(self):
        dtor = Destructor(
            comment="Virtual destructor",
            body=[],
            virtual_qualifier=VirtualQualifier.VIRTUAL
        )
        self.assertEqual(dtor.virtual_qualifier, VirtualQualifier.VIRTUAL)


class TestClass(unittest.TestCase):
    """Test Class class"""

    def test_simple_class(self):
        cls = Class(
            comment="A simple class",
            name="SimpleClass",
            superclass_decls=None,
            members=[]
        )
        self.assertEqual(cls.name, "SimpleClass")
        self.assertEqual(cls.qualifier, FinalQualifier.NON_FINAL)
        self.assertIsNone(cls.superclass_decls)

    def test_final_class_with_superclass(self):
        cls = Class(
            comment="A final class",
            name="FinalClass",
            superclass_decls="public BaseClass",
            members=[],
            qualifier=FinalQualifier.FINAL
        )
        self.assertEqual(cls.qualifier, FinalQualifier.FINAL)
        self.assertEqual(cls.superclass_decls, "public BaseClass")

    def test_class_with_members(self):
        func = Function(
            comment="Member function",
            name="method",
            params=[],
            ret_type=Type(hpp_type="void"),
            body=[]
        )
        ctor = Constructor(comment=None, params=[], initializers=[], body=[])

        cls = Class(
            comment="Class with members",
            name="MyClass",
            superclass_decls=None,
            members=[
                ClassMemberConstructor(constructor=ctor),
                ClassMemberFunction(function=func)
            ]
        )
        self.assertEqual(len(cls.members), 2)
        self.assertIsInstance(cls.members[0], ClassMemberConstructor)
        self.assertIsInstance(cls.members[1], ClassMemberFunction)


class TestNamespace(unittest.TestCase):
    """Test Namespace class"""

    def test_empty_namespace(self):
        ns = Namespace(name="MyNamespace", members=[])
        self.assertEqual(ns.name, "MyNamespace")
        self.assertEqual(len(ns.members), 0)

    def test_namespace_with_function(self):
        func = Function(
            comment="Free function",
            name="helper",
            params=[],
            ret_type=Type(hpp_type="void"),
            body=[]
        )
        ns = Namespace(name="Util", members=[MemberFunction(function=func)])
        self.assertEqual(len(ns.members), 1)


class TestFileBanner(unittest.TestCase):
    """Test FileBanner classes"""

    def test_default_file_banner(self):
        banner = DefaultFileBanner()
        self.assertEqual(banner.get_title("Test.hpp"), "Test.hpp")
        self.assertEqual(banner.get_author("Test.hpp"), "Generated by fpp tools")
        self.assertEqual(banner.get_description("Test.hpp", "Test file"), "Test file")

    def test_default_file_banner_with_tool_name(self):
        banner = DefaultFileBanner(tool_name_opt="MyTool v1.0")
        self.assertEqual(banner.get_author("Test.hpp"), "Generated by MyTool v1.0")


class TestCppDoc(unittest.TestCase):
    """Test CppDoc class"""

    def test_simple_cppdoc(self):
        hpp = HppFile(name="Test.hpp", include_guard="TEST_HPP")
        doc = CppDoc(
            description="Test document",
            hpp_file=hpp,
            cpp_file_name="Test.cpp",
            members=[]
        )
        self.assertEqual(doc.description, "Test document")
        self.assertEqual(doc.hpp_file.name, "Test.hpp")
        self.assertEqual(doc.cpp_file_name, "Test.cpp")

    def test_cppdoc_with_default_banner(self):
        hpp = HppFile(name="Test.hpp", include_guard="TEST_HPP")
        doc = CppDoc(
            description="Test",
            hpp_file=hpp,
            cpp_file_name="Test.cpp",
            members=[],
            tool_name_opt="TestTool"
        )
        banner = doc.get_file_banner()
        self.assertIsInstance(banner, DefaultFileBanner)
        self.assertEqual(banner.get_author("Test.hpp"), "Generated by TestTool")

    def test_cppdoc_with_custom_banner(self):
        hpp = HppFile(name="Test.hpp", include_guard="TEST_HPP")
        custom_banner = DefaultFileBanner(tool_name_opt="Custom")
        doc = CppDoc(
            description="Test",
            hpp_file=hpp,
            cpp_file_name="Test.cpp",
            members=[],
            file_banner_opt=custom_banner
        )
        banner = doc.get_file_banner()
        self.assertEqual(banner.get_author("Test.hpp"), "Generated by Custom")

    def test_cppdoc_with_class_member(self):
        hpp = HppFile(name="MyClass.hpp", include_guard="MY_CLASS_HPP")
        cls = Class(
            comment="My class",
            name="MyClass",
            superclass_decls=None,
            members=[]
        )
        doc = CppDoc(
            description="Class document",
            hpp_file=hpp,
            cpp_file_name="MyClass.cpp",
            members=[MemberClass(c=cls)]
        )
        self.assertEqual(len(doc.members), 1)
        self.assertIsInstance(doc.members[0], MemberClass)
        self.assertEqual(doc.members[0].c.name, "MyClass")


class TestEnums(unittest.TestCase):
    """Test enum types"""

    def test_final_qualifier(self):
        self.assertIsNotNone(FinalQualifier.FINAL)
        self.assertIsNotNone(FinalQualifier.NON_FINAL)

    def test_explicit_qualifier(self):
        self.assertIsNotNone(ExplicitQualifier.EXPLICIT)
        self.assertIsNotNone(ExplicitQualifier.NOT_EXPLICIT)

    def test_virtual_qualifier(self):
        self.assertIsNotNone(VirtualQualifier.VIRTUAL)
        self.assertIsNotNone(VirtualQualifier.NON_VIRTUAL)

    def test_sv_qualifier(self):
        self.assertIsNotNone(SVQualifier.STATIC)
        self.assertIsNotNone(SVQualifier.VIRTUAL)
        self.assertIsNotNone(SVQualifier.OVERRIDE)
        self.assertIsNotNone(SVQualifier.FINAL)
        self.assertIsNotNone(SVQualifier.PURE_VIRTUAL)
        self.assertIsNotNone(SVQualifier.NON_SV)

    def test_const_qualifier(self):
        self.assertIsNotNone(ConstQualifier.CONST)
        self.assertIsNotNone(ConstQualifier.NON_CONST)


if __name__ == "__main__":
    unittest.main()
