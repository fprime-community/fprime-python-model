from fprime_python_model.semantics.symbol_interface import SymbolInterface
from dataclasses import dataclass
from fprime_python_model.fpp_ast import fpp_ast
from fprime_python_model.fpp_ast.fpp_ast_node import AstNode


# A data structure that represents a definition
class Symbol(SymbolInterface):

    def is_dictionary_def(self):
        return False


# A type symbol
class TypeSymbol(Symbol):

    def is_dictionary_def(self):
        return super().is_dictionary_def()


# A port interface instance symbol
class InterfaceInstanceSymbol(Symbol):

    def is_dictionary_def(self):
        return super().is_dictionary_def()


@dataclass
class AbsTypeSymbol(TypeSymbol):
    node: fpp_ast.Annotated[AstNode[fpp_ast.DefAbsType]]

    def get_node_id(self):
        return self.node[1]._id

    def get_unqualified_name(self):
        return self.node[1].data.name


@dataclass
class AliasTypeSymbol(TypeSymbol):
    node: fpp_ast.Annotated[AstNode[fpp_ast.DefAliasType]]

    def get_node_id(self):
        return self.node[1]._id

    def get_unqualified_name(self):
        return self.node[1].data.name

    def is_dictionary_def(self):
        return self.node[1].data.is_dictionary_def


@dataclass
class ArraySymbol(TypeSymbol):
    node: fpp_ast.Annotated[AstNode[fpp_ast.DefArray]]

    def get_node_id(self):
        return self.node[1]._id

    def get_unqualified_name(self):
        return self.node[1].data.name

    def is_dictionary_def(self):
        return self.node[1].data.is_dictionary_def


@dataclass
class ComponentSymbol(Symbol):
    node: fpp_ast.Annotated[AstNode[fpp_ast.DefComponent]]

    def get_node_id(self):
        return self.node[1]._id

    def get_unqualified_name(self):
        return self.node[1].data.name


@dataclass
class ComponentInstanceSymbol(InterfaceInstanceSymbol):
    node: fpp_ast.Annotated[AstNode[fpp_ast.DefComponentInstance]]

    def get_node_id(self):
        return self.node[1]._id

    def get_unqualified_name(self):
        return self.node[1].data.name


@dataclass
class ConstantSymbol(Symbol):
    node: fpp_ast.Annotated[AstNode[fpp_ast.DefConstant]]

    def get_node_id(self):
        return self.node[1]._id

    def get_unqualified_name(self):
        return self.node[1].data.name

    def is_dictionary_def(self):
        return self.node[1].data.is_dictionary_def


@dataclass
class EnumSymbol(TypeSymbol):
    node: fpp_ast.Annotated[AstNode[fpp_ast.DefEnum]]

    def get_node_id(self):
        return self.node[1]._id

    def get_unqualified_name(self):
        return self.node[1].data.name

    def is_dictionary_def(self):
        return self.node[1].data.is_dictionary_def


@dataclass
class EnumConstantSymbol(Symbol):
    node: fpp_ast.Annotated[AstNode[fpp_ast.DefEnumConstant]]

    def get_node_id(self):
        return self.node[1]._id

    def get_unqualified_name(self):
        return self.node[1].data.name


@dataclass
class InterfaceSymbol(Symbol):
    node: fpp_ast.Annotated[AstNode[fpp_ast.DefInterface]]

    def get_node_id(self):
        return self.node[1]._id

    def get_unqualified_name(self):
        return self.node[1].data.name


@dataclass
class ModuleSymbol(Symbol):
    node: fpp_ast.Annotated[AstNode[fpp_ast.DefModule]]

    def get_node_id(self):
        return self.node[1]._id

    def get_unqualified_name(self):
        return self.node[1].data.name


@dataclass
class PortSymbol(Symbol):
    node: fpp_ast.Annotated[AstNode[fpp_ast.DefPort]]

    def get_node_id(self):
        return self.node[1]._id

    def get_unqualified_name(self):
        return self.node[1].data.name


@dataclass
class StateMachineSymbol(Symbol):
    node: fpp_ast.Annotated[AstNode[fpp_ast.DefStateMachine]]

    def get_node_id(self):
        return self.node[1]._id

    def get_unqualified_name(self):
        return self.node[1].data.name


@dataclass
class StructSymbol(TypeSymbol):
    node: fpp_ast.Annotated[AstNode[fpp_ast.DefStruct]]

    def get_node_id(self):
        return self.node[1]._id

    def get_unqualified_name(self):
        return self.node[1].data.name

    def is_dictionary_def(self):
        return self.node[1].data.is_dictionary_def


@dataclass
class TopologySymbol(InterfaceInstanceSymbol):
    node: fpp_ast.Annotated[AstNode[fpp_ast.DefTopology]]

    def get_node_id(self):
        return self.node[1]._id

    def get_unqualified_name(self):
        return self.node[1].data.name
