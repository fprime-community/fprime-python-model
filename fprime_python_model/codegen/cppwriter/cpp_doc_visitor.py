"""A C++ doc visitor"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TypeVar, Generic

from fprime_python_model.codegen.cppwriter.cpp_doc import (
    CppDoc, Class, Constructor, Destructor, Function,
    Member, MemberClass, MemberLines, MemberFunction, MemberNamespace,
    ClassMember, ClassMemberClass, ClassMemberConstructor, ClassMemberDestructor,
    ClassMemberLines, ClassMemberFunction, Namespace
)
from fprime_python_model.utils.line_utils import Lines

Input = TypeVar('Input')
Output = TypeVar('Output')


class CppDocVisitor(ABC, Generic[Input, Output]):
    """A C++ doc visitor"""

    @abstractmethod
    def default(self, input_val: Input) -> Output:
        """Default visitor implementation"""
        raise NotImplementedError

    def visit_class(self, input_val: Input, c: Class) -> Output:
        """Visit a class"""
        return self.default(input_val)

    def visit_constructor(self, input_val: Input, constructor: Constructor) -> Output:
        """Visit a constructor"""
        return self.default(input_val)

    def visit_destructor(self, input_val: Input, destructor: Destructor) -> Output:
        """Visit a destructor"""
        return self.default(input_val)

    def visit_function(self, input_val: Input, function: Function) -> Output:
        """Visit a function"""
        return self.default(input_val)

    def visit_lines(self, input_val: Input, lines: Lines) -> Output:
        """Visit lines"""
        return self.default(input_val)

    def visit_namespace(self, input_val: Input, namespace: Namespace) -> Output:
        """Visit a namespace"""
        return self.default(input_val)

    def visit_member(self, input_val: Input, member: Member) -> Output:
        """Visit a document member"""
        match member:
            case MemberClass(c=c):
                return self.visit_class(input_val, c)
            case MemberLines(lines=lines):
                return self.visit_lines(input_val, lines)
            case MemberFunction(function=function):
                return self.visit_function(input_val, function)
            case MemberNamespace(namespace=namespace):
                return self.visit_namespace(input_val, namespace)
            case _:
                raise ValueError(f"Unknown member type: {type(member)}")

    def visit_namespace_member(self, input_val: Input, member: Member) -> Output:
        """Visit a namespace member"""
        return self.visit_member(input_val, member)

    def visit_class_member(self, input_val: Input, member: ClassMember) -> Output:
        """Visit a class member"""
        match member:
            case ClassMemberClass(c=c):
                return self.visit_class(input_val, c)
            case ClassMemberConstructor(constructor=constructor):
                return self.visit_constructor(input_val, constructor)
            case ClassMemberDestructor(destructor=destructor):
                return self.visit_destructor(input_val, destructor)
            case ClassMemberLines(lines=lines):
                return self.visit_lines(input_val, lines)
            case ClassMemberFunction(function=function):
                return self.visit_function(input_val, function)
            case _:
                raise ValueError(f"Unknown class member type: {type(member)}")
