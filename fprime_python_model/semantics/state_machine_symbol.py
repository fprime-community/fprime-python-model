from fprime_python_model.semantics.symbol_interface import SymbolInterface
from dataclasses import dataclass
from fprime_python_model.fpp_ast import fpp_ast
from fprime_python_model.fpp_ast.fpp_ast_node import AstNode, AstId


class StateMachineSymbolInterface(SymbolInterface):
    pass


@dataclass
class ActionSymbol(StateMachineSymbolInterface):
    node: fpp_ast.Annotated[AstNode[fpp_ast.DefAction]]

    def get_node_id(self) -> AstId:
        return self.node[1]._id

    def get_unqualified_name(self) -> fpp_ast.Ident:
        return self.node[1].data.name


@dataclass
class GuardSymbol(StateMachineSymbolInterface):
    node: fpp_ast.Annotated[AstNode[fpp_ast.DefGuard]]

    def get_node_id(self) -> AstId:
        return self.node[1]._id

    def get_unqualified_name(self) -> fpp_ast.Ident:
        return self.node[1].data.name


@dataclass
class ChoiceSymbol(StateMachineSymbolInterface):
    node: fpp_ast.Annotated[AstNode[fpp_ast.DefChoice]]

    def get_node_id(self) -> AstId:
        return self.node[1]._id

    def get_unqualified_name(self) -> fpp_ast.Ident:
        return self.node[1].data.name


@dataclass
class SignalSymbol(StateMachineSymbolInterface):
    node: fpp_ast.Annotated[AstNode[fpp_ast.DefSignal]]

    def get_node_id(self) -> AstId:
        return self.node[1]._id

    def get_unqualified_name(self) -> fpp_ast.Ident:
        return self.node[1].data.name


@dataclass
class StateSymbol(StateMachineSymbolInterface):
    node: fpp_ast.Annotated[AstNode[fpp_ast.DefState]]

    def get_node_id(self) -> AstId:
        return self.node[1]._id

    def get_unqualified_name(self) -> fpp_ast.Ident:
        return self.node[1].data.name
