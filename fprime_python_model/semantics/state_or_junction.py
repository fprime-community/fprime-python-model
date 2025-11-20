from dataclasses import dataclass
from abc import ABC, abstractmethod
from fprime_python_model.semantics.state_machine_symbol import (
    StateMachineSymbolInterface,
    StateSymbol,
    ChoiceSymbol,
)


class StateOrChoice(ABC):

    @abstractmethod
    def get_symbol(self) -> StateMachineSymbolInterface:
        pass

    @abstractmethod
    def get_name(self) -> str:
        pass


@dataclass
class State(StateOrChoice):
    symbol: StateSymbol

    def get_symbol(self) -> StateMachineSymbolInterface:
        return self.symbol

    def get_name(self) -> str:
        return f"state {self.symbol.get_unqualified_name()}"


@dataclass
class Choice(StateOrChoice):
    symbol: ChoiceSymbol

    def get_symbol(self) -> StateMachineSymbolInterface:
        return self.symbol

    def get_name(self) -> str:
        return f"choice {self.symbol.get_unqualified_name()}"
