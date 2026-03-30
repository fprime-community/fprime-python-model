from fprime_python_model.fpp_ast import fpp_ast
from fprime_python_model.fpp_ast.fpp_ast_node import AstNode
from fprime_python_model.utils.error import InternalError
from typing import Optional, List, TypeVar

T = TypeVar("T")


def get_substates(
    state: fpp_ast.DefState,
) -> List[fpp_ast.Annotated[AstNode[fpp_ast.DefState]]]:
    substates: list[fpp_ast.Annotated[AstNode[fpp_ast.DefState]]] = []

    for member in state.members or []:
        pre, inner, post = member.node

        if isinstance(inner, fpp_ast.StateMemberDefState):
            substates.append((pre, inner.node, post))

    return substates


def _list_to_opt(items, item_kind: str) -> Optional[T]:
    if len(items) == 0:
        return None
    if len(items) == 1:
        return items[0]

    raise InternalError(f"state should have at most one {item_kind}")


def get_entry_specifier_opt(
    state: fpp_ast.DefState,
) -> Optional[fpp_ast.Annotated[AstNode[fpp_ast.SpecStateEntry]]]:
    specifiers: list[fpp_ast.Annotated[AstNode[fpp_ast.SpecStateEntry]]] = []

    for member in state.members or []:
        pre, inner, post = member.node

        if isinstance(inner, fpp_ast.StateMemberSpecStateEntry):
            specifiers.append((pre, inner.node, post))

    return _list_to_opt(specifiers, "entry specifier")


def get_entry_actions(state: fpp_ast.DefState) -> List[AstNode[fpp_ast.Ident]]:
    spec = get_entry_specifier_opt(state)

    if spec:
        return spec[1].data.actions

    return []


def get_exit_specifier_opt(
    state: fpp_ast.DefState,
) -> Optional[fpp_ast.Annotated[AstNode[fpp_ast.SpecStateExit]]]:
    specifiers: list[fpp_ast.Annotated[AstNode[fpp_ast.SpecStateExit]]] = []

    for member in state.members or []:
        pre, inner, post = member.node

        if isinstance(inner, fpp_ast.StateMemberSpecStateExit):
            specifiers.append((pre, inner.node, post))

    return _list_to_opt(specifiers, "exit specifier")


def get_initial_specifier(
    state: fpp_ast.DefState,
) -> Optional[fpp_ast.Annotated[AstNode[fpp_ast.SpecInitialTransition]]]:
    specifiers: list[fpp_ast.Annotated[AstNode[fpp_ast.SpecInitialTransition]]] = []

    for member in state.members or []:
        pre, inner, post = member.node

        if isinstance(inner, fpp_ast.StateMemberSpecInitialTransition):
            specifiers.append((pre, inner.node, post))

    return _list_to_opt(specifiers, "initial transition")


def get_exit_actions(state: fpp_ast.DefState) -> List[AstNode[fpp_ast.Ident]]:
    spec = get_exit_specifier_opt(state)

    if spec:
        return spec[1].data.actions

    return []
