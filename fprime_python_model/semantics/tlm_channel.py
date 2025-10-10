from typing import TypeAlias, Dict, Tuple, Optional
from dataclasses import dataclass
from fprime_python_model.fpp_ast import fpp_ast
from fprime_python_model.fpp_ast.fpp_ast_node import AstNode, AstId
from fprime_python_model.semantics.types_values import Value, Type
from fprime_python_model.semantics.format import Format

TlmChannelId: TypeAlias = int
Limits: TypeAlias = Dict[fpp_ast.LimitKind, Tuple[AstId, Value]]


@dataclass
class TlmChannel:
    a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecTlmChannel]]
    channel_type: Type
    update: fpp_ast.SpecTlmChannelUpdate
    format: Optional[Format]
    low_limits: Limits
    high_limits: Limits

    def get_name(self) -> fpp_ast.Ident:
        return self.a_node[1].data.name

    def get_node(self) -> AstNode[fpp_ast.SpecTlmChannel]:
        return self.a_node[1]
