from abc import ABC, abstractmethod
from fpp_ast_node import AstId
from fpp_ast import Unqualified

class SymbolInterface(ABC):
    @abstractmethod
    def get_node_id(self) -> AstId:
        pass

    @abstractmethod
    def get_unqualified_name(self) -> Unqualified:
        pass

    def __hash__(self):
        return hash(self.get_node_id())

    def __eq__(self, other):
        return isinstance(other, SymbolInterface) and self.get_node_id() == other.get_node_id()
