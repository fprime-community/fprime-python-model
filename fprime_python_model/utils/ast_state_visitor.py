from fprime_python_model.utils.fpp_ast_visitor import AstVisitor
from typing import TypeVar, Generic, Callable, List

State = TypeVar("State")
T = TypeVar("T")


class AstStateVisitor(AstVisitor[State, State], Generic[State]):
    """
    Visit an AST, carrying state
    """

    # Default state transformation
    def default(self, s: State) -> State:
        return s

    # Visit a list in sequence, threading state
    def visit_list(
        self,
        s: State,
        items: List[T],
        visit: Callable[[State, T], State],
    ) -> State:
        current_state = s

        for item in items:
            current_state = visit(current_state, item)

        return current_state
