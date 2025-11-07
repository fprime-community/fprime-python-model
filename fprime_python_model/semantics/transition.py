from dataclasses import dataclass
from abc import ABC, abstractmethod
from typing import List, Optional
from fprime_python_model.semantics.state_machine_symbol import ActionSymbol, GuardSymbol
from fprime_python_model.semantics.state_or_junction import StateOrChoice


class Transition(ABC):

    @abstractmethod
    def get_actions(self) -> List[ActionSymbol]:
        pass

    @abstractmethod
    def get_target_opt(self) -> Optional[StateOrChoice]:
        pass


@dataclass
class ExternalTransition(Transition):
    actions: List[ActionSymbol]
    target: StateOrChoice

    def get_actions(self) -> List[ActionSymbol]:
        return self.actions

    def get_target_opt(self) -> Optional[StateOrChoice]:
        return self.target


@dataclass
class InternalTransition(Transition):
    actions: List[ActionSymbol]

    def get_actions(self) -> List[ActionSymbol]:
        return self.actions

    def get_target_opt(self) -> Optional[StateOrChoice]:
        return None


@dataclass
class GuardedTransition(Transition):
    guard_opt: Optional[GuardSymbol]
    transition: Transition

    def get_actions(self) -> List[ActionSymbol]:
        return []

    def get_target_opt(self) -> Optional[StateOrChoice]:
        return None
