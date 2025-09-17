from fprime_python_model.semantics.symbol_interface import SymbolInterface
from dataclasses import dataclass
from fprime_python_model.fpp_ast import fpp_ast
from fprime_python_model.fpp_ast.fpp_ast_node import AstNode


class Symbol(SymbolInterface):
    pass


@dataclass
class AbsTypeSymbol(Symbol):
    node: fpp_ast.Annotated[AstNode[fpp_ast.DefAbsType]]

    def get_node_id(self):
        return self.node[1]._id

    def get_unqualified_name(self):
        return self.node[1].data.name


@dataclass
class AliasTypeSymbol(Symbol):
    node: fpp_ast.Annotated[AstNode[fpp_ast.DefAliasType]]

    def get_node_id(self):
        return self.node[1]._id

    def get_unqualified_name(self):
        return self.node[1].data.name


@dataclass
class ArraySymbol(Symbol):
    node: fpp_ast.Annotated[AstNode[fpp_ast.DefArray]]

    def get_node_id(self):
        return self.node[1]._id

    def get_unqualified_name(self):
        return self.node[1].data.name


@dataclass
class ComponentSymbol(Symbol):
    node: fpp_ast.Annotated[AstNode[fpp_ast.DefComponent]]

    def get_node_id(self):
        return self.node[1]._id

    def get_unqualified_name(self):
        return self.node[1].data.name


@dataclass
class ComponentInstanceSymbol(Symbol):
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


@dataclass
class EnumSymbol(Symbol):
    node: fpp_ast.Annotated[AstNode[fpp_ast.DefEnum]]

    def get_node_id(self):
        return self.node[1]._id

    def get_unqualified_name(self):
        return self.node[1].data.name


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
class StructSymbol(Symbol):
    node: fpp_ast.Annotated[AstNode[fpp_ast.DefStruct]]

    def get_node_id(self):
        return self.node[1]._id

    def get_unqualified_name(self):
        return self.node[1].data.name


@dataclass
class TopologySymbol(Symbol):
    node: fpp_ast.Annotated[AstNode[fpp_ast.DefTopology]]

    def get_node_id(self):
        return self.node[1]._id

    def get_unqualified_name(self):
        return self.node[1].data.name
