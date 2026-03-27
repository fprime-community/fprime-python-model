from fprime_python_model.semantics.port_instance_identifier import PortInstanceIdentifier
from fprime_python_model.fpp_ast.fpp_ast_node import AstNode
from fprime_python_model.fpp_ast import fpp_ast
from dataclasses import dataclass

@dataclass
class TopologyPort:
    a_node: fpp_ast.Annotated[AstNode[fpp_ast.SpecTopPort]]
    pii: PortInstanceIdentifier

    def get_underlying_port(self) -> AstNode[fpp_ast.PortInstanceIdentifier]:
        return self.a_node[1].data.underlying_port
