from typing import Optional, TypeAlias
from dataclasses import dataclass
from fprime_python_model.fpp_ast import fpp_ast
from fprime_python_model.fpp_ast.fpp_ast_node import AstNode, AstId
from fprime_python_model.semantics.format import Format
from fprime_python_model.semantics.symbol import StateMachineSymbol
from fprime_python_model.semantics.state_machine import (
    get_symbol_kind,
    StateMachineKind,
)


@dataclass
class StateMachineInstance:
    a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecStateMachineInstance]]
    symbol: StateMachineSymbol
    priorty: Optional[int]
    queue_full: fpp_ast.QueueFull

    def get_node_id(self) -> AstId:
        return self.a_node[1]._id

    def get_name(self) -> str:
        return self.a_node[1].data.name

    def get_sm_kind(self) -> StateMachineKind:
        return get_symbol_kind(self.symbol)

    # TODO get loc
