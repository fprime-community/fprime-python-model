from abc import ABC, abstractmethod
from fprime_python_model.fpp_ast.fpp_ast_node import AstId
from fprime_python_model.semantics.name import UnqualifiedName


class SymbolInterface(ABC):
    @abstractmethod
    def get_node_id(self) -> AstId:
        pass

    @abstractmethod
    def get_unqualified_name(self) -> UnqualifiedName:
        pass

    def __hash__(self):
        return hash(self.get_node_id())

    def __eq__(self, other):
        return (
            isinstance(other, SymbolInterface)
            and self.get_node_id() == other.get_node_id()
        )
