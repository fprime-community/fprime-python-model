from semantics.symbol_interface import SymbolInterface
from dataclasses import dataclass
import fpp_ast
from fpp_ast_node import AstNode

class Symbol(SymbolInterface):
    pass


@dataclass(eq=False, unsafe_hash=True)
class AbsTypeSymbol(Symbol):
    node: fpp_ast.Annotated[AstNode[fpp_ast.DefAbsType]]

    def get_node_id(self):
        return self.node[1]._id

    def get_unqualified_name(self):
        return self.node[1].data.name


@dataclass(eq=False, unsafe_hash=True)
class AliasTypeSymbol(Symbol):
    node: fpp_ast.Annotated[AstNode[fpp_ast.DefAliasType]]

    def get_node_id(self):
        return self.node[1]._id

    def get_unqualified_name(self):
        return self.node[1].data.name


@dataclass(eq=False, unsafe_hash=True)
class ArraySymbol(Symbol):
    node: fpp_ast.Annotated[AstNode[fpp_ast.DefArray]]

    def get_node_id(self):
        return self.node[1]._id

    def get_unqualified_name(self):
        return self.node[1].data.name


@dataclass(eq=False, unsafe_hash=True)
class ComponentSymbol(Symbol):
    node: fpp_ast.Annotated[AstNode[fpp_ast.DefComponent]]

    def get_node_id(self):
        return self.node[1]._id

    def get_unqualified_name(self):
        return self.node[1].data.name


@dataclass(eq=False, unsafe_hash=True)
class ComponentInstanceSymbol(Symbol):
    node: fpp_ast.Annotated[AstNode[fpp_ast.DefComponentInstance]]

    def get_node_id(self):
        return self.node[1]._id

    def get_unqualified_name(self):
        return self.node[1].data.name


@dataclass(eq=False, unsafe_hash=True)
class ConstantSymbol(Symbol):
    node: fpp_ast.Annotated[AstNode[fpp_ast.DefConstant]]

    def get_node_id(self):
        return self.node[1]._id

    def get_unqualified_name(self):
        return self.node[1].data.name


@dataclass(eq=False, unsafe_hash=True)
class EnumSymbol(Symbol):
    node: fpp_ast.Annotated[AstNode[fpp_ast.DefEnum]]

    def get_node_id(self):
        return self.node[1]._id

    def get_unqualified_name(self):
        return self.node[1].data.name


@dataclass(eq=False, unsafe_hash=True)
class EnumConstantSymbol(Symbol):
    node: fpp_ast.Annotated[AstNode[fpp_ast.DefEnumConstant]]

    def get_node_id(self):
        return self.node[1]._id

    def get_unqualified_name(self):
        return self.node[1].data.name


@dataclass(eq=False, unsafe_hash=True)
class InterfaceSymbol(Symbol):
    node: fpp_ast.Annotated[AstNode[fpp_ast.DefInterface]]

    def get_node_id(self):
        return self.node[1]._id

    def get_unqualified_name(self):
        return self.node[1].data.name


@dataclass(eq=False, unsafe_hash=True)
class ModuleSymbol(Symbol):
    node: fpp_ast.Annotated[AstNode[fpp_ast.DefModule]]

    def get_node_id(self):
        return self.node[1]._id

    def get_unqualified_name(self):
        return self.node[1].data.name


@dataclass(eq=False, unsafe_hash=True)
class PortSymbol(Symbol):
    node: fpp_ast.Annotated[AstNode[fpp_ast.DefPort]]

    def get_node_id(self):
        return self.node[1]._id

    def get_unqualified_name(self):
        return self.node[1].data.name

@dataclass(eq=False, unsafe_hash=True)
class StateMachineSymbol(Symbol):
    node: fpp_ast.Annotated[AstNode[fpp_ast.DefStateMachine]]

    def get_node_id(self):
        return self.node[1]._id

    def get_unqualified_name(self):
        return self.node[1].data.name


@dataclass(eq=False, unsafe_hash=True)
class StructSymbol(Symbol):
    node: fpp_ast.Annotated[AstNode[fpp_ast.DefStruct]]

    def get_node_id(self):
        return self.node[1]._id

    def get_unqualified_name(self):
        return self.node[1].data.name


@dataclass(eq=False, unsafe_hash=True)
class TopologySymbol(Symbol):
    node: fpp_ast.Annotated[AstNode[fpp_ast.DefTopology]]

    def get_node_id(self):
        return self.node[1]._id

    def get_unqualified_name(self):
        return self.node[1].data.name
