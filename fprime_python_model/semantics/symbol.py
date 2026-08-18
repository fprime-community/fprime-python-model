from fprime_python_model.semantics.symbol_interface import SymbolInterface
from dataclasses import dataclass
from fprime_python_model.fpp_ast import fpp_ast
from fprime_python_model.fpp_ast.fpp_ast_node import AstNode


# A data structure that represents a definition
class Symbol(SymbolInterface):

    def is_dictionary_def(self):
        return False

    @staticmethod
    def construct(node: fpp_ast.Annotated[AstNode]) -> "Symbol":
        """Construct a typed symbol from an AST node

        This is a helper function that inspects the type of the AST node and then constructs the appropriate Symbol
        instance based on that type.

        Args:
            node: annotated AST node from which to construct the symbol
        Returns:
            An instance of a subclass of Symbol corresponding to the AST node type
        """
        node_type = type(node[1].data)
        if node_type == fpp_ast.DefAbsType:
            return AbsTypeSymbol(node)
        elif node_type == fpp_ast.DefAliasType:
            return AliasTypeSymbol(node)
        elif node_type == fpp_ast.DefArray:
            return ArraySymbol(node)
        elif node_type == fpp_ast.DefComponent:
            return ComponentSymbol(node)
        elif node_type == fpp_ast.DefComponentInstance:
            return ComponentInstanceSymbol(node)
        elif node_type == fpp_ast.DefConstant:
            return ConstantSymbol(node)
        elif node_type == fpp_ast.DefEnum:
            return EnumSymbol(node)
        elif node_type == fpp_ast.DefEnumConstant:
            return EnumConstantSymbol(node)
        elif node_type == fpp_ast.DefInterface:
            return InterfaceSymbol(node)
        elif node_type == fpp_ast.DefModule:
            return ModuleSymbol(node)
        elif node_type == fpp_ast.DefPort:
            return PortSymbol(node)
        elif node_type == fpp_ast.DefStateMachine:
            return StateMachineSymbol(node)
        elif node_type == fpp_ast.DefStruct:
            return StructSymbol(node)
        elif node_type == fpp_ast.DefSystem:
            return SystemSymbol(node)
        elif node_type == fpp_ast.DefTopology:
            return TopologySymbol(node)
        else:
            raise ValueError(f"Unknown symbol type for node: {node}")


# A type symbol
class TypeSymbol(Symbol):

    def is_dictionary_def(self):
        return super().is_dictionary_def()


# A port interface instance symbol
class InterfaceInstanceSymbol(Symbol):

    def is_dictionary_def(self):
        return super().is_dictionary_def()


@dataclass(frozen=True)
class AbsTypeSymbol(TypeSymbol):
    node: fpp_ast.Annotated[AstNode[fpp_ast.DefAbsType]]

    def get_node_id(self):
        return self.node[1]._id

    def get_unqualified_name(self):
        return self.node[1].data.name


@dataclass(frozen=True)
class AliasTypeSymbol(TypeSymbol):
    node: fpp_ast.Annotated[AstNode[fpp_ast.DefAliasType]]

    def get_node_id(self):
        return self.node[1]._id

    def get_unqualified_name(self):
        return self.node[1].data.name

    def is_dictionary_def(self):
        return self.node[1].data.is_dictionary_def


@dataclass(frozen=True)
class ArraySymbol(TypeSymbol):
    node: fpp_ast.Annotated[AstNode[fpp_ast.DefArray]]

    def get_node_id(self):
        return self.node[1]._id

    def get_unqualified_name(self):
        return self.node[1].data.name

    def is_dictionary_def(self):
        return self.node[1].data.is_dictionary_def


@dataclass(frozen=True)
class ComponentSymbol(Symbol):
    node: fpp_ast.Annotated[AstNode[fpp_ast.DefComponent]]

    def get_node_id(self):
        return self.node[1]._id

    def get_unqualified_name(self):
        return self.node[1].data.name


@dataclass(frozen=True)
class ComponentInstanceSymbol(InterfaceInstanceSymbol):
    node: fpp_ast.Annotated[AstNode[fpp_ast.DefComponentInstance]]

    def get_node_id(self):
        return self.node[1]._id

    def get_unqualified_name(self):
        return self.node[1].data.name


@dataclass(frozen=True)
class ConstantSymbol(Symbol):
    node: fpp_ast.Annotated[AstNode[fpp_ast.DefConstant]]

    def get_node_id(self):
        return self.node[1]._id

    def get_unqualified_name(self):
        return self.node[1].data.name

    def is_dictionary_def(self):
        return self.node[1].data.is_dictionary_def


@dataclass(frozen=True)
class EnumSymbol(TypeSymbol):
    node: fpp_ast.Annotated[AstNode[fpp_ast.DefEnum]]

    def get_node_id(self):
        return self.node[1]._id

    def get_unqualified_name(self):
        return self.node[1].data.name

    def is_dictionary_def(self):
        return self.node[1].data.is_dictionary_def


@dataclass(frozen=True)
class EnumConstantSymbol(Symbol):
    node: fpp_ast.Annotated[AstNode[fpp_ast.DefEnumConstant]]

    def get_node_id(self):
        return self.node[1]._id

    def get_unqualified_name(self):
        return self.node[1].data.name


@dataclass(frozen=True)
class InterfaceSymbol(Symbol):
    node: fpp_ast.Annotated[AstNode[fpp_ast.DefInterface]]

    def get_node_id(self):
        return self.node[1]._id

    def get_unqualified_name(self):
        return self.node[1].data.name


@dataclass(frozen=True)
class ModuleSymbol(Symbol):
    node: fpp_ast.Annotated[AstNode[fpp_ast.DefModule]]

    def get_node_id(self):
        return self.node[1]._id

    def get_unqualified_name(self):
        return self.node[1].data.name


@dataclass(frozen=True)
class PortSymbol(Symbol):
    node: fpp_ast.Annotated[AstNode[fpp_ast.DefPort]]

    def get_node_id(self):
        return self.node[1]._id

    def get_unqualified_name(self):
        return self.node[1].data.name


@dataclass(frozen=True)
class StateMachineSymbol(Symbol):
    node: fpp_ast.Annotated[AstNode[fpp_ast.DefStateMachine]]

    def get_node_id(self):
        return self.node[1]._id

    def get_unqualified_name(self):
        return self.node[1].data.name


@dataclass(frozen=True)
class StructSymbol(TypeSymbol):
    node: fpp_ast.Annotated[AstNode[fpp_ast.DefStruct]]

    def get_node_id(self):
        return self.node[1]._id

    def get_unqualified_name(self):
        return self.node[1].data.name

    def is_dictionary_def(self):
        return self.node[1].data.is_dictionary_def


@dataclass(frozen=True)
class SystemSymbol(Symbol):
    node: fpp_ast.Annotated[AstNode[fpp_ast.DefSystem]]

    def get_node_id(self):
        return self.node[1]._id

    def get_unqualified_name(self):
        return self.node[1].data.name


@dataclass(frozen=True)
class TopologySymbol(InterfaceInstanceSymbol):
    node: fpp_ast.Annotated[AstNode[fpp_ast.DefTopology]]

    def get_node_id(self):
        return self.node[1]._id

    def get_unqualified_name(self):
        return self.node[1].data.name
