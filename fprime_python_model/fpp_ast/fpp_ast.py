from abc import ABC, abstractmethod
import sys
from typing import List, TypeAlias, Optional, Tuple, TypeVar
# typing.override was added in Python 3.12. On older versions we fall back to a
# no-op decorator so the codebase stays compatible with Python 3.10+.
if sys.version_info >= (3, 12):
    from typing import override
else:
    def override(func):  # type: ignore[no-redef]
        return func

from enum import Enum
from dataclasses import dataclass
from fprime_python_model.fpp_ast.fpp_ast_node import AstNode, FrozenAstData
from fprime_python_model.utils.error import InternalError

T = TypeVar("T")
Annotated: TypeAlias = Tuple[List[str], T, List[str]]
Ident: TypeAlias = str
FormalParamList: TypeAlias = List[Annotated[AstNode["FormalParam"]]]
TUMember: TypeAlias = "ModuleMember"


@dataclass(frozen=True)
class TransUnit(FrozenAstData):
    """
    Translation unit consisting of translation unit members

    :param members: The list of translation unit members contained in this unit.
    :type members: List[TUMember]
    """

    members: List[TUMember]


class Binop(Enum):
    """
    Represents a binary operation

    Attributes:
        ADD
        DIV
        MUL
        SUB
    """

    ADD = "+"
    DIV = "/"
    MUL = "*"
    SUB = "-"

    def __str__(self):
        return self.value


class ComponentKind(Enum):
    """Represents component kind

    Attributes:
        ACTIVE
        PASSIVE
        QUEUED
    """

    ACTIVE = "active"
    PASSIVE = "passive"
    QUEUED = "queued"

    def __str__(self):
        return self.value


class QualIdent(ABC):
    """A possibly-qualified identifier"""

    @abstractmethod
    def to_ident_list(self) -> List[Ident]:
        """
        Convert a qualified identifier to a list of identifiers

        :return: List of identifiers
        :rtype: List[Ident]
        """
        pass


@dataclass(frozen=True)
class Unqualified(QualIdent, FrozenAstData):
    """An unqualified identifier

    :param name: Unqualified identifier name
    :type name: Ident
    """

    name: Ident

    @override
    def to_ident_list(self):
        return [self.name]


@dataclass(frozen=True)
class Qualified(QualIdent, FrozenAstData):
    """
    A qualified identifier

    :param qualifier: Qualified identifier qualifier
    :type qualifier: AstNode[QualIdent]
    :param name: Qualified identifier name
    :type name: AstNode[Ident]
    """

    qualifier: AstNode[QualIdent]
    name: AstNode[Ident]

    @override
    def to_ident_list(self):
        return self.qualifier.data.to_ident_list() + [self.name.data]


def qual_ident_from_node_list(node_list: "NodeList") -> QualIdent:
    """
    Construct a qualified identifier from a node list

    :param node_list: List of Ident AST nodes
    :type node_list: NodeList
    :return: Qualified identifier created from node list
    :rtype: QualIdent
    """
    split_node_list = split(node_list)
    if not split_node_list[0] and split_node_list[1]:
        return Unqualified(split_node_list[1].data)
    else:
        qualifier_1 = qual_ident_from_node_list(split_node_list[0])
        node = AstNode.create_with_id(qualifier_1, name(split_node_list[0])._id)
        return Qualified(node, split_node_list[1])


NodeList: TypeAlias = List[AstNode[Ident]]
"""
A qualified identifier represented as a list of identifier nodes
This is useful during parsing
"""


def split(node_list: NodeList) -> Tuple[List[AstNode[Ident]], AstNode[Ident]]:
    """
    Split a qualified identifier list into qualifier and name

    :param node_list: List of Ident AST nodes
    :type node_list: NodeList
    :raises InternalError: Raised if the node list is empty
    :return: Tuple consisting of qualifier and name
    :rtype: Tuple[List[AstNode[Ident]], AstNode[Ident]]
    """
    rev: NodeList = node_list[::-1]
    if not rev:
        raise InternalError("node list should not be empty")
    else:
        return rev[1:][::-1], rev[0]


def qualifier(node_list: NodeList) -> List[AstNode[Ident]]:
    """
    Get the qualifier

    :param node_list: List of Ident AST nodes
    :type node_list: NodeList
    :return: List of qualifier Ident AST nodes
    :rtype: List[AstNode[Ident]]
    """
    return split(node_list)[0]


def name(node_list: NodeList) -> AstNode[Ident]:
    """
    Get the unqualified name

    :param node_list: List of Ident AST nodes
    :type node_list: NodeList
    :return: Unqualified Ident AST node
    :rtype: AstNode[Ident]
    """
    return split(node_list)[1]


##########################
### Definitions
##########################


@dataclass(frozen=True)
class DefAbsType(FrozenAstData):
    """
    Abstract type definition

    :param name: Name of the abstract type
    :type name: Ident
    """

    name: Ident


@dataclass(frozen=True)
class DefAliasType(FrozenAstData):
    """
    Aliased type definition

    :param name: Name of the alias type
    :type name: Ident
    :param type_name: Type name that the alias type represents
    :type type_name: AstNode[TypeName]
    :param is_dictionary_def: Whether the alias type is a dictionary definition
    :type is_dictionary_def: bool
    """

    name: Ident
    type_name: AstNode["TypeName"]
    is_dictionary_def: bool


@dataclass(frozen=True)
class DefArray(FrozenAstData):
    """
    Array definition

    :param name: Name of the array
    :type name: Ident
    :param size: Size of the array
    :type size: AstNode[Expr]
    :param elt_type: Type of the array elements
    :type elt_type: AstNode[TypeName]
    :param default: Default value of the array
    :type default: Optional[AstNode[Expr]]
    :param format: Format string
    :type format: Optional[AstNode[str]]
    :param is_dictionary_def: Whether the array is a dictionary definition
    :type is_dictionary_def: bool
    """

    name: Ident
    size: AstNode["Expr"]
    elt_type: AstNode["TypeName"]
    default: Optional[AstNode["Expr"]]
    format: Optional[AstNode[str]]
    is_dictionary_def: bool


@dataclass(frozen=True)
class DefComponent(FrozenAstData):
    """
    Component definition

    :param kind: Component kind
    :type kind: ComponentKind
    :param name: Name of the component
    :type name: Ident
    :param members: List of component members
    :type members: List[ComponentMember]
    """

    kind: ComponentKind
    name: Ident
    members: List["ComponentMember"]


@dataclass(frozen=True)
class DefComponentInstance(FrozenAstData):
    """
    Component instance definition

    :param name: Name of the component instance
    :type name: Ident
    :param component: The component associated with the component instance
    :type component: AstNode[QualIdent]
    :param base_id: Base ID of the component instance
    :type base_id: AstNode[Expr]
    :param impl_type: Implementation type of the component instance
    :type impl_type: Optional[AstNode[str]]
    :param file: File that provides the implementation associated with the component instance
    :type file: Optional[AstNode[str]]
    :param queue_size: Queue size
    :type queue_size: Optional[AstNode[Expr]]
    :param stack_size: Stack size in bytes
    :param priority: Thread priority
    :type priority: Optional[AstNode[Expr]]
    :param cpu: CPU affinity
    :type cpu: Optional[AstNode[Expr]]
    :param init_specs: List of init specifiers
    :type init_specs: List[Annotated[AstNode[SpecInit]]]
    """

    name: Ident
    component: AstNode[QualIdent]
    base_id: AstNode["Expr"]
    impl_type: Optional[AstNode[str]]
    file: Optional[AstNode[str]]
    queue_size: Optional[AstNode["Expr"]]
    stack_size: Optional[AstNode["Expr"]]
    priority: Optional[AstNode["Expr"]]
    cpu: Optional[AstNode["Expr"]]
    init_specs: List[Annotated[AstNode["SpecInit"]]]


@dataclass(frozen=True)
class DefConstant(FrozenAstData):
    """
    Constant definition

    :param: name: Name of the constant
    :type name: Ident
    :param value: Value of the constant
    :type value: AstNode[Expr]
    :param is_dictionary_def: Whether the constant is a dictionary definition
    :type is_dictionary_def: bool
    """

    name: Ident
    value: AstNode["Expr"]
    is_dictionary_def: bool


@dataclass(frozen=True)
class DefEnum(FrozenAstData):
    """
    Enum definition

    :param name: Name of the enum
    :type name: Ident
    :param type_name: Type name of the enum
    :type type_name: Optional[AstNode[TypeName]]
    :param constants: List of enum constants
    :type constants: List[Annotated[AstNode[DefEnumConstant]]]
    :param default: Default value of the enum
    :type default: Optional[AstNode[Expr]]
    :param is_dictionary_def: Whether the enum is a dictionary definition
    :type is_dictionary_def: bool
    """

    name: Ident
    type_name: Optional[AstNode["TypeName"]]
    constants: List[Annotated[AstNode["DefEnumConstant"]]]
    default: Optional[AstNode["Expr"]]
    is_dictionary_def: bool


@dataclass(frozen=True)
class DefEnumConstant(FrozenAstData):
    """
    Enum constant definition

    :param name: Name of the enum constant
    :type name: Ident
    :param value: Value of the enum
    :type value: Optional[AstNode[Expr]]
    """

    name: Ident
    value: Optional[AstNode["Expr"]]


@dataclass(frozen=True)
class DefModule(FrozenAstData):
    """
    Module definition

    :param name: Name of the module
    :type name: Ident
    :param members: List of module members
    :type members: List[ModuleMember]
    """

    name: Ident
    members: List["ModuleMember"]


@dataclass(frozen=True)
class DefPort(FrozenAstData):
    """
    Port definition

    :param name: Name of the port
    :type name: Ident
    :param params: Port formal parameters
    :type params: Optional[AstNode[FormalParamList]]
    :param return_type: Return type of the port
    :type return_type: Optional[AstNode[TypeName]]
    """

    name: Ident
    params: FormalParamList
    return_type: Optional[AstNode["TypeName"]]


@dataclass(frozen=True)
class DefStateMachine(FrozenAstData):
    """
    State machine definition

    :param name: Name of the state machine
    :type name: Ident
    :param members: List of state machine members
    :type members: List[StateMachineMember]
    """

    name: Ident
    members: Optional[List["StateMachineMember"]]


@dataclass(frozen=True)
class DefAction(FrozenAstData):
    """
    Action definition

    :param name: Name of the action
    :type name: Ident
    :param type_name: Type name of the action
    :type type_name: Optional[AstNode[TypeName]]
    """

    name: Ident
    type_name: Optional[AstNode["TypeName"]]


@dataclass(frozen=True)
class DefChoice(FrozenAstData):
    """
    Choice definition

    :param name: Name of the choice
    :type name: Ident
    :param guard: Guard identifier
    :type guard: AstNode[Ident]
    :param if_transition: If transition
    :type if_transition: AstNode[TransitionExpr]
    :param else_transition: Else transition
    :type else_transition: AstNode[TransitionExpr]
    """

    name: Ident
    guard: AstNode[Ident]
    if_transition: AstNode["TransitionExpr"]
    else_transition: AstNode["TransitionExpr"]


@dataclass(frozen=True)
class DefGuard(FrozenAstData):
    """
    Guard definition

    :param name: Name of the guard
    :type name: Ident
    :param type_name: Type name of the guard
    :type type_name: Optional[AstNode[TypeName]]
    """

    name: Ident
    type_name: Optional[AstNode["TypeName"]]


@dataclass(frozen=True)
class DefSignal(FrozenAstData):
    """
    Signal definition

    :param name: Name of the signal
    :type name: Ident
    :param type_name: Type name of the signal
    :type type_name: Optional[AstNode[TypeName]]
    """

    name: Ident
    type_name: Optional[AstNode["TypeName"]]


@dataclass(frozen=True)
class DefState(FrozenAstData):
    """
    State definition

    :param name: Name of the state
    :type name: Ident
    :param members: List of state members
    :type members: List[StateMember]
    """

    name: Ident
    members: List["StateMember"]


@dataclass(frozen=True)
class DefInterface(FrozenAstData):
    """
    Interface definition

    :param name: Name of the interface
    :type name: Ident
    :param members: List of interface members
    :type members: List[InterfaceMember]
    """

    name: Ident
    members: List["InterfaceMember"]


@dataclass(frozen=True)
class DefStruct(FrozenAstData):
    """
    Struct definition

    :param name: Name of the struct
    :type name: Ident
    :param members: List of struct members
    :type members: List[Annotated[AstNode[StructMember]]]
    :param default: Default value of the struct
    :type default: Optional[AstNode[Expr]]
    :param is_dictionary_def: Whether the struct is a dictionary definition
    :type is_dictionary_def: bool
    """

    name: Ident
    members: List[Annotated[AstNode["StructTypeMember"]]]
    default: Optional[AstNode["Expr"]]
    is_dictionary_def: bool


@dataclass(frozen=True)
class DefSystem(FrozenAstData):
    """
    System definition

    :param name: Name of the system
    :type name: Ident
    :param topology: Deployment topology implementing the system
    :type topology: AstNode[QualIdent]
    """

    name: Ident
    topology: AstNode[QualIdent]


@dataclass(frozen=True)
class DefTopology(FrozenAstData):
    """
    Topology defintion

    :param name: Name of the topology
    :type name: Ident
    :param members: List of topology members
    :type members: List[TopologyMember]
    """

    isDeployment: bool
    name: Ident
    members: List["TopologyMember"]
    implements: List[AstNode[QualIdent]]


##########################
### Component Member
##########################


class ComponentMemberNode(ABC):
    pass


@dataclass(frozen=True)
class ComponentMember(FrozenAstData):
    """
    Component member with annotated component member node

    :param node: Annotated component member node
    :type node: Annotated[ComponentMemberNode]
    """

    node: Annotated[ComponentMemberNode]


@dataclass(frozen=True)
class ComponentMemberDefAbsType(ComponentMemberNode, FrozenAstData):
    """
    Abstract type component member

    :param node: Abstract type definition AST node
    :type node: AstNode[DefAbsType]
    """

    node: AstNode[DefAbsType]


@dataclass(frozen=True)
class ComponentMemberDefAliasType(ComponentMemberNode, FrozenAstData):
    """
    Alias type component member

    :param node: Alias type definition AST node
    :type node: AstNode[DefAliasType]
    """

    node: AstNode[DefAliasType]


@dataclass(frozen=True)
class ComponentMemberDefArray(ComponentMemberNode, FrozenAstData):
    """
    Array component member

    :param node: Array definition AST node
    :type node: AstNode[DefArray]
    """

    node: AstNode[DefArray]


@dataclass(frozen=True)
class ComponentMemberDefConstant(ComponentMemberNode, FrozenAstData):
    """
    Constant component member

    :param node: Constant definition AST node
    :type node: AstNode[DefConstant]
    """

    node: AstNode[DefConstant]


@dataclass(frozen=True)
class ComponentMemberDefEnum(ComponentMemberNode, FrozenAstData):
    """
    Enum component member

    :param node: Enum definition AST node
    :type node: AstNode[DefEnum]
    """

    node: AstNode[DefEnum]


@dataclass(frozen=True)
class ComponentMemberDefStateMachine(ComponentMemberNode, FrozenAstData):
    """
    State machine component member

    :param node: State machine definition AST node
    :type node: AstNode[DefStateMachine]
    """

    node: AstNode[DefStateMachine]


@dataclass(frozen=True)
class ComponentMemberDefStruct(ComponentMemberNode, FrozenAstData):
    """
    Struct component member

    :param node: Struct definition AST node
    :type node: AstNode[DefStruct]
    """

    node: AstNode[DefStruct]


@dataclass(frozen=True)
class ComponentMemberSpecCommand(ComponentMemberNode, FrozenAstData):
    """
    Command component member

    :param node: Command specifier AST node
    :type node: AstNode[SpecCommand]
    """

    node: AstNode["SpecCommand"]


@dataclass(frozen=True)
class ComponentMemberSpecContainer(ComponentMemberNode, FrozenAstData):
    """
    Container component member

    :param node: Container specifier AST node
    :type node: AstNode[SpecContainer]
    """

    node: AstNode["SpecContainer"]


@dataclass(frozen=True)
class ComponentMemberSpecEvent(ComponentMemberNode, FrozenAstData):
    """
    Event component member

    :param node: Event specifier AST node
    :type node: AstNode[SpecEvent]
    """

    node: AstNode["SpecEvent"]


@dataclass(frozen=True)
class ComponentMemberSpecInclude(ComponentMemberNode, FrozenAstData):
    """
    Include specifier component member

    :param node: Include specifier AST node
    :type node: AstNode[SpecInclude]
    """

    node: AstNode["SpecInclude"]


@dataclass(frozen=True)
class ComponentMemberSpecInternalPort(ComponentMemberNode, FrozenAstData):
    """
    Internal port specifier component member

    :param node: Internal port specifier AST node
    :type node: AstNode[SpecInternalPort]
    """

    node: AstNode["SpecInternalPort"]


@dataclass(frozen=True)
class ComponentMemberSpecParam(ComponentMemberNode, FrozenAstData):
    """
    Param component member

    :param node: Param specifier AST node
    :type node: AstNode[SpecParam]
    """

    node: AstNode["SpecParam"]


@dataclass(frozen=True)
class ComponentMemberSpecPortInstance(ComponentMemberNode, FrozenAstData):
    """
    Port instance component member

    :param node: Port instance specifier AST node
    :type node: AstNode[SpecPortInstance]
    """

    node: AstNode["SpecPortInstance"]


@dataclass(frozen=True)
class ComponentMemberSpecPortMatching(ComponentMemberNode, FrozenAstData):
    """
    Port matching component member

    :param node: Port matching specifier AST node
    :type node: AstNode[SpecPortMatching]
    """

    node: AstNode["SpecPortMatching"]


@dataclass(frozen=True)
class ComponentMemberSpecRecord(ComponentMemberNode, FrozenAstData):
    """
    Record component member

    :param node: Record specifier AST node
    :type node: AstNode[SpecRecord]
    """

    node: AstNode["SpecRecord"]


@dataclass(frozen=True)
class ComponentMemberSpecStateMachineInstance(ComponentMemberNode, FrozenAstData):
    """
    State machine instance component member

    :param node: State machine instance specifier AST node
    :type node: AstNode[SpecStateMachineInstance]
    """

    node: AstNode["SpecStateMachineInstance"]


@dataclass(frozen=True)
class ComponentMemberSpecTlmChannel(ComponentMemberNode, FrozenAstData):
    """
    Telemetry channel component member

    :param node: Telemetry channel specifier AST node
    :type node: AstNode[SpecTlmChannel]
    """

    node: AstNode["SpecTlmChannel"]


@dataclass(frozen=True)
class ComponentMemberSpecImportInterface(ComponentMemberNode, FrozenAstData):
    """
    Import specifier component member

    :param node: Import specifier AST node
    :type node: AstNode[SpecImport]
    """

    node: AstNode["SpecImport"]


##########################
### Module Member
##########################


class ModuleMemberNode(ABC):
    pass


@dataclass(frozen=True)
class ModuleMember(FrozenAstData):
    """
    Module member with annotated module member node

    :param node: Annotated module member node
    :type node: Annotated[ModuleMemberNode]

    """

    node: Annotated[ModuleMemberNode]


@dataclass(frozen=True)
class ModuleMemberDefAbsType(ModuleMemberNode, FrozenAstData):
    """
    Abstract type module member

    :param node: Abstract type definition AST node
    :type node: AstNode[DefAbsType]
    """

    node: AstNode[DefAbsType]


@dataclass(frozen=True)
class ModuleMemberDefAliasType(ModuleMemberNode, FrozenAstData):
    """
    Alias type module member

    :param node: Alias type definition AST node
    :type node: AstNode[DefAliasType]
    """

    node: AstNode[DefAliasType]


@dataclass(frozen=True)
class ModuleMemberDefArray(ModuleMemberNode, FrozenAstData):
    """
    Array module member

    :param node: Array definition AST node
    :type node: AstNode[DefArray]
    """

    node: AstNode[DefArray]


@dataclass(frozen=True)
class ModuleMemberDefComponent(ModuleMemberNode, FrozenAstData):
    """
    Component module member

    :param node: Component definition AST node
    :type node: AstNode[DefComponent]
    """

    node: AstNode[DefComponent]


@dataclass(frozen=True)
class ModuleMemberDefComponentInstance(ModuleMemberNode, FrozenAstData):
    """
    Component instance module member

    :param node: Component instance definition AST node
    :type node: AstNode[DefComponentInstance]
    """

    node: AstNode[DefComponentInstance]


@dataclass(frozen=True)
class ModuleMemberDefConstant(ModuleMemberNode, FrozenAstData):
    """
    Constant module member

    :param node: Constant definition AST node
    :type node: AstNode[DefConstant]
    """

    node: AstNode[DefConstant]


@dataclass(frozen=True)
class ModuleMemberDefEnum(ModuleMemberNode, FrozenAstData):
    """
    Enum module member

    :param node: Enum definition AST node
    :type node: AstNode[DefEnum]
    """

    node: AstNode[DefEnum]


@dataclass(frozen=True)
class ModuleMemberDefInterface(ModuleMemberNode, FrozenAstData):
    """
    Interface module member

    :param node: Interface definition AST node
    :type node: AstNode[DefInterface]
    """

    node: AstNode["DefInterface"]


@dataclass(frozen=True)
class ModuleMemberDefModule(ModuleMemberNode, FrozenAstData):
    """
    Module module member

    :param node: Module definition AST node
    :type node: AstNode[DefModule]
    """

    node: AstNode[DefModule]


@dataclass(frozen=True)
class ModuleMemberDefPort(ModuleMemberNode, FrozenAstData):
    """
    Port module member

    :param node: Port definition AST node
    :type node: AstNode[DefPort]
    """

    node: AstNode["DefPort"]


@dataclass(frozen=True)
class ModuleMemberDefStateMachine(ModuleMemberNode, FrozenAstData):
    """
    State machine module member

    :param node: State machine definition AST node
    :type node: AstNode[DefStateMachine]
    """

    node: AstNode["DefStateMachine"]


@dataclass(frozen=True)
class ModuleMemberDefStruct(ModuleMemberNode, FrozenAstData):
    """
    Struct module member

    :param node: Struct definition AST node
    :type node: AstNode[DefStruct]
    """

    node: AstNode["DefStruct"]


@dataclass(frozen=True)
class ModuleMemberDefSystem(ModuleMemberNode, FrozenAstData):
    """
    System module member

    :param node: System definition AST node
    :type node: AstNode[DefSystem]
    """

    node: AstNode["DefSystem"]


@dataclass(frozen=True)
class ModuleMemberDefTopology(ModuleMemberNode, FrozenAstData):
    """
    Topology module member

    :param node: Topology definition AST node
    :type node: AstNode[DefTopology]
    """

    node: AstNode["DefTopology"]


@dataclass(frozen=True)
class ModuleMemberSpecInclude(ModuleMemberNode, FrozenAstData):
    """
    Include specifier module member

    :param node: Include specifier AST node
    :type node: AstNode[SpecInclude]
    """

    node: AstNode["SpecInclude"]


@dataclass(frozen=True)
class ModuleMemberSpecLoc(ModuleMemberNode, FrozenAstData):
    """
    Location specifier module member

    :param node: Location specifier AST node
    :type node: AstNode[SpecLoc]
    """

    node: AstNode["SpecLoc"]


##########################
### State Machine Member
##########################


@dataclass(frozen=True)
class StateMachineMember(FrozenAstData):
    """
    State machine member with annotated state machine member member node

    :param node: Annotated state machine member node
    :type node: Annotated[StateMachineMemberNode]
    """

    node: Annotated["StateMachineMemberNode"]


class StateMachineMemberNode(ABC):
    pass


@dataclass(frozen=True)
class StateMachineMemberDefAbsType(StateMachineMemberNode, FrozenAstData):
    node: AstNode[DefAbsType]


@dataclass(frozen=True)
class StateMachineMemberDefAction(StateMachineMemberNode, FrozenAstData):
    """
    Action state machine member

    :param node: Action definition AST node
    :type node: AstNode[DefAction]
    """

    node: AstNode["DefAction"]


@dataclass(frozen=True)
class StateMachineMemberDefAliasType(StateMachineMemberNode, FrozenAstData):
    node: AstNode[DefAliasType]


@dataclass(frozen=True)
class StateMachineMemberDefArray(StateMachineMemberNode, FrozenAstData):
    node: AstNode[DefArray]


@dataclass(frozen=True)
class StateMachineMemberDefChoice(StateMachineMemberNode, FrozenAstData):
    """
    Choice state machine member

    :param node: Choice definition AST node
    :type node: AstNode[DefChoice]
    """

    node: AstNode["DefChoice"]


@dataclass(frozen=True)
class StateMachineMemberDefConstant(StateMachineMemberNode, FrozenAstData):
    node: AstNode[DefConstant]


@dataclass(frozen=True)
class StateMachineMemberDefEnum(StateMachineMemberNode, FrozenAstData):
    node: AstNode[DefEnum]


@dataclass(frozen=True)
class StateMachineMemberDefGuard(StateMachineMemberNode, FrozenAstData):
    """
    Guard state machine member

    :param node: Guard definition AST node
    :type node: AstNode[DefGuard]
    """

    node: AstNode["DefGuard"]


@dataclass(frozen=True)
class StateMachineMemberDefSignal(StateMachineMemberNode, FrozenAstData):
    """
    Signal state machine member

    :param node: Signal definition AST node
    :type node: AstNode[DefSignal]
    """

    node: AstNode["DefSignal"]


@dataclass(frozen=True)
class StateMachineMemberDefState(StateMachineMemberNode, FrozenAstData):
    """
    State state machine member

    :param node: State definition AST node
    :type node: AstNode[DefState]
    """

    node: AstNode["DefState"]


@dataclass(frozen=True)
class StateMachineMemberDefStruct(StateMachineMemberNode, FrozenAstData):
    node: AstNode[DefStruct]


@dataclass(frozen=True)
class StateMachineMemberSpecInclude(StateMachineMemberNode, FrozenAstData):
    node: AstNode["SpecInclude"]


@dataclass(frozen=True)
class StateMachineMemberSpecInitialTransition(StateMachineMemberNode, FrozenAstData):
    """
    Initial transition state machine member

    :param node: Initial transition specifier AST node
    :type node: AstNode[SpecInitialTransition]
    """

    node: AstNode["SpecInitialTransition"]


##########################
### State Member
##########################


@dataclass(frozen=True)
class StateMember(FrozenAstData):
    """
    State member with annotated state member node

    :param node: Annotated state member node
    :type node: Annotated[StateMemberNode]
    """

    node: Annotated["StateMemberNode"]


class StateMemberNode(ABC):
    pass


@dataclass(frozen=True)
class StateMemberDefChoice(StateMemberNode, FrozenAstData):
    """
    Choice state member

    :param node: Choice definition AST node
    :type node: AstNode[DefChoice]
    """

    node: AstNode[DefChoice]


@dataclass(frozen=True)
class StateMemberDefState(StateMemberNode, FrozenAstData):
    """
    State state member

    :param node: State definition AST node
    :type node: AstNode[DefState]
    """

    node: AstNode[DefState]


@dataclass(frozen=True)
class StateMemberSpecStateEntry(StateMemberNode, FrozenAstData):
    """
    State entry state member

    :param node: State entry specifier AST node
    :type node: AstNode[SpecStateEntry]
    """

    node: AstNode["SpecStateEntry"]


@dataclass(frozen=True)
class StateMemberSpecStateExit(StateMemberNode, FrozenAstData):
    """
    State exit state member

    :param node: State exit specifier AST node
    :type node: AstNode[SpecStateExit]
    """

    node: AstNode["SpecStateExit"]


@dataclass(frozen=True)
class StateMemberSpecInitialTransition(StateMemberNode, FrozenAstData):
    """
    Initial state state member

    :param node: Initial transition specifier AST node
    :type node: AstNode[SpecInitialTransition]
    """

    node: AstNode["SpecInitialTransition"]


@dataclass(frozen=True)
class StateMemberSpecStateTransition(StateMemberNode, FrozenAstData):
    """
    Transition state member

    :param node: State transition specifier AST node
    :type node: AstNode[SpecStateTransition]
    """

    node: AstNode["SpecStateTransition"]


##########################
### Expressions
##########################


class Expr(ABC):
    pass


@dataclass(frozen=True)
class ExprArray(Expr, FrozenAstData):
    """
    Array expression

    :param elts: List of expression AST nodes
    :type elts: List[AstNode[Expr]]
    """

    elts: List[AstNode[Expr]]


@dataclass(frozen=True)
class ExprArraySubscript(Expr, FrozenAstData):
    """
    Array expression

    :param e1: Expression AST node
    :type e1: AstNode[Expr]
    :param e2: Expression AST node
    :type e2: AstNode[Expr]
    """

    e1: AstNode[Expr]
    e2: AstNode[Expr]


@dataclass(frozen=True)
class ExprBinop(Expr, FrozenAstData):
    """
    Binary operation expression

    :param e1: Left expression AST node
    :type e1: AstNode[Expr]
    :param op: Binary operation
    :type op: Binop
    :param e2: Right expression AST node
    :type e2: AstNode
    """

    e1: AstNode[Expr]
    op: "Binop"
    e2: AstNode[Expr]


@dataclass(frozen=True)
class ExprDot(Expr, FrozenAstData):
    """
    Dot expression

    :param e: Expression AST node
    :type e: AstNode[Expr]
    :param id: Identifier AST node
    :type id: AstNode[Ident]
    """

    e: AstNode[Expr]
    id: AstNode[Ident]


@dataclass(frozen=True)
class ExprIdent(Expr, FrozenAstData):
    """
    Ident expression

    :param value: Identifier AST node
    :type value: AstNode[Ident]
    """

    value: Ident


@dataclass(frozen=True)
class ExprLiteralBool(Expr, FrozenAstData):
    """
    Literal Boolean expression

    :param value: Boolean value
    :type value: LiteralBool
    """

    value: "LiteralBool"


@dataclass(frozen=True)
class ExprLiteralInt(Expr, FrozenAstData):
    """
    Literal integer expression

    :param value: Integer value
    :type value: str
    """

    value: str


@dataclass(frozen=True)
class ExprLiteralFloat(Expr, FrozenAstData):
    """
    Literal float expression

    :param value: Float value
    :type value: str
    """

    value: str


@dataclass(frozen=True)
class ExprLiteralString(Expr, FrozenAstData):
    """
    Literal string expression

    :param value: String value
    :type value: str
    """

    value: str


@dataclass(frozen=True)
class ExprParen(Expr, FrozenAstData):
    """
    Parenthesis expression

    :param e: Expression AST node
    :type e: AstNode[Expr]
    """

    e: AstNode[Expr]


@dataclass(frozen=True)
class ExprSizeOf(Expr, FrozenAstData):
    type_name: AstNode["TypeName"]


@dataclass(frozen=True)
class ExprStruct(Expr, FrozenAstData):
    """
    Struct expression

    :param members: List of struct member AST nodes
    :type members: List[AstNode[StructMember]]
    """

    members: List[AstNode["StructMember"]]


@dataclass(frozen=True)
class ExprUnop(Expr, FrozenAstData):
    """
    Unary operation expression

    :param op: Unary operation
    :type op: Unop
    :param e: Expression AST node
    :type e: AstNode[Expr]
    """

    op: "Unop"
    e: AstNode[Expr]


##########################
### Topology Member
##########################


class TopologyMemberNode(ABC):
    pass


@dataclass(frozen=True)
class TopologyMember(FrozenAstData):
    """
    Topology member with anotated topology member node

    :param node: Annotated topology member node
    :type node: Annotated[TopologyMemberNode]
    """

    node: Annotated[TopologyMemberNode]


@dataclass(frozen=True)
class TopologyMemberSpecInstance(TopologyMemberNode, FrozenAstData):
    """
    Component instance topology member

    :param node: Instance specifier AST node
    :type node: AstNode[SpecInstance]
    """

    node: AstNode["SpecInstance"]


@dataclass(frozen=True)
class TopologyMemberSpecConnectionGraph(TopologyMemberNode, FrozenAstData):
    """
    Connection graph topology member

    :param node: Connection graph specifier AST node
    :type node: AstNode[SpecConnectionGraph]
    """

    node: AstNode["SpecConnectionGraph"]


@dataclass(frozen=True)
class TopologyMemberSpecInclude(TopologyMemberNode, FrozenAstData):
    """
    Include specifier topology member

    :param node: Include specifier AST node
    :type node: AstNode[SpecInclude]
    """

    node: AstNode["SpecInclude"]


@dataclass(frozen=True)
class TopologyMemberSpecTlmPacketSet(TopologyMemberNode, FrozenAstData):
    """
    Telemetry packet set topology member

    :param node: Telemetry packet set specifier AST node
    :type node: AstNode[SpecTlmPacketSet]
    """

    node: AstNode["SpecTlmPacketSet"]


@dataclass(frozen=True)
class TopologyMemberSpecTopPort(TopologyMemberNode, FrozenAstData):
    """
    Topology import topology member

    :param node: Topology import specifier AST node
    :type node: AstNode[SpecTopPort]
    """

    node: AstNode["SpecTopPort"]


#################################
### Telemetry Packet Set Member
#################################


class TlmPacketSetMemberNode(ABC):
    pass


@dataclass(frozen=True)
class TlmPacketSetMember(FrozenAstData):
    """
    Telemetry packet set member with annotated telemetry packet set member node

    :param node: Annotated telemetry packet set member node
    :type node: Annotated[TlmPacketSetMemberNode]
    """

    node: Annotated[TlmPacketSetMemberNode]


@dataclass(frozen=True)
class TlmPacketSetMemberSpecInclude(TlmPacketSetMemberNode, FrozenAstData):
    """
    Include specifier telemetry packet set member

    :param node: Include specifier AST node
    :type node: AstNode[SpecInclude]
    """

    node: AstNode["SpecInclude"]


@dataclass(frozen=True)
class TlmPacketSetMemberSpecTlmPacket(TlmPacketSetMemberNode, FrozenAstData):
    """
    Telemetry packet telemetry packet set member

    :param node: Telemetry packet specifier AST node
    :type node: AstNode[SpecTlmPacket]
    """

    node: AstNode["SpecTlmPacket"]


############################
### Interface Member
############################


@dataclass(frozen=True)
class InterfaceMember(FrozenAstData):
    """
    Interface member with annotated interface member node

    :param node: Annotated interface member node
    :type node: Annotated[InterfaceMemberNode]
    """

    node: Annotated["InterfaceMemberNode"]


class InterfaceMemberNode(ABC):
    pass


@dataclass(frozen=True)
class InterfaceMemberSpecPortInstance(InterfaceMemberNode, FrozenAstData):
    """
    Port instance interface member

    :param node: Port instance specifier AST node
    :type node: AstNode[SpecPortInstance]
    """

    node: AstNode["SpecPortInstance"]


@dataclass(frozen=True)
class InterfaceMemberSpecImportInterface(InterfaceMemberNode, FrozenAstData):
    """
    Interface import interface member

    :param node: Import specifier AST node
    :type node: AstNode[SpecImport]
    """

    node: AstNode["SpecImport"]


###############################
### Telemetry Packet Member
###############################


class TlmPacketMember(ABC):
    pass


@dataclass(frozen=True)
class TlmPacketMemberSpecInclude(TlmPacketMember, FrozenAstData):
    """
    Include specifier telemetry packet member

    :param node: Include specifier AST node
    :type node: AstNode[SpecInclude]
    """

    node: AstNode["SpecInclude"]


@dataclass(frozen=True)
class TlmPacketMemberTlmChannelIdentifier(TlmPacketMember, FrozenAstData):
    """
    Telemetry channel identifier telemetry packet member

    :param node: Telemetry channel identifier AST node
    :type node: AstNode[TlmChannelIdentifier]
    """

    node: AstNode["TlmChannelIdentifier"]


##########################
### Specifiers
##########################


class QueueFull(Enum):
    """
    Represents queue full behavior

    Attributes:
        ASSERT
        BLOCK
        DROP
        HOOK
    """

    ASSERT = "assert"
    BLOCK = "block"
    DROP = "drop"
    HOOK = "hook"

    def __str__(self):
        return self.value


@dataclass(frozen=True)
class SpecCommand(FrozenAstData):
    """
    Command specifier

    :param kind: Command kind
    :type kind: SpecCommandKind
    :param name: Command name
    :type name: Ident
    :param params: Command formal parameters
    :type params: FormalParamList
    :param opcode: Command opcode
    :type opcode: Optional[AstNode[Expr]]
    :param priority: Command priority
    :type priority: Optional[AstNode[Expr]]
    :param queue_full: Command queue full behavior
    :type queue_full: Optional[QueueFull]
    """

    kind: "SpecCommandKind"
    name: Ident
    params: FormalParamList
    opcode: Optional[AstNode[Expr]]
    priority: Optional[AstNode[Expr]]
    queue_full: Optional[AstNode[QueueFull]]


class SpecCommandKind(Enum):
    """
    Represents command kind

    Attributes:
        ASYNC
        GUARDED
        SYNC
    """

    ASYNC = "async"
    GUARDED = "guarded"
    SYNC = "sync"

    def __str__(self):
        return self.value


@dataclass(frozen=True)
class SpecInstance(FrozenAstData):
    """
    Component instance specifier

    :param instance: Component instance AST node
    :type instance: AstNode[QualIdent]
    """

    instance: AstNode[QualIdent]


class SpecConnectionGraph(ABC):
    pass


@dataclass(frozen=True)
class Direct(SpecConnectionGraph, FrozenAstData):
    """
    Direction connection graph specifier

    :param name: Connection graph name
    :type name: Ident
    :param connections: List of connections
    :type connections: List[Connection]
    """

    name: Ident
    connections: List["Connection"]


class PatternKind(Enum):
    """
    Represents connection graph pattern kind

    Attributes:
        DIRECT
        COMMAND
        EVENT
        HEALTH
        PARAM
        TELEMETRY
        TEXT
    """

    COMMAND = "command"
    EVENT = "event"
    HEALTH = "health"
    PARAM = "param"
    TELEMETRY = "telemetry"
    TEXT_EVENT = "text event"
    TIME = "time"

    def __str__(self):
        return self.value


@dataclass(frozen=True)
class Pattern(SpecConnectionGraph, FrozenAstData):
    """
    Pattern connection graph specifier

    :param kind: Pattern kind
    :type kind: PatternKind
    :param source: Pattern source
    :type source: AstNode[QualIdent]
    :param targets: List of pattern targets
    :type targets: List[AstNode[QualIdent]]
    """

    kind: PatternKind
    source: AstNode[QualIdent]
    targets: List[AstNode[QualIdent]]


@dataclass(frozen=True)
class Connection(FrozenAstData):
    """
    Connection

    :param is_unmatched: Whether the connection is unmatched
    :type is_unmatched: bool
    :param from_port: From port instance identifier
    :type from_port: AstNode[PortInstanceIdentifier]
    :param from_index: From port index
    :type from_index: Optional[AstNode[Expr]]
    :param to_port: To port instance indentifier
    :type to_port: AstNode[PortInstanceIdentifier]
    :param to_index: To port index
    :type to_index: Optional[AstNode[Expr]]
    """

    is_unmatched: bool
    from_port: AstNode["PortInstanceIdentifier"]
    from_index: Optional[AstNode[Expr]]
    to_port: AstNode["PortInstanceIdentifier"]
    to_index: Optional[AstNode[Expr]]


@dataclass(frozen=True)
class SpecContainer(FrozenAstData):
    """
    Container specifier

    :param name: Container name
    :type name: Ident
    :param id: Container identifier
    :type id: Optional[AstNode[Expr]]
    :param default_priority: Container default priority
    :type default_priority: Optional[AstNode[Expr]]
    """

    name: Ident
    id: Optional[AstNode[Expr]]
    default_priority: Optional[AstNode[Expr]]


@dataclass(frozen=True)
class EventThrottle(FrozenAstData):
    """
    Event throttle

    :param count: Maximum throttle count
    :type count: AstNode[Expr]
    :param every: Throttle period
    :type every: Optional[AstNode[Expr]]
    """

    count: AstNode[Expr]
    every: Optional[AstNode[Expr]]


@dataclass(frozen=True)
class SpecEvent(FrozenAstData):
    """
    Event specifier

    :param name: Event name
    :type name: Ident
    :param params: Event formal parameters
    :type params: FormalParamList
    :param severity: Event severity
    :type severity: SpecEventSeverity
    :param id: Event identifier
    :type id: Optional[AstNode[Expr]]
    :param format: Event format string
    :type format: AstNode[str]
    :param throttle: Event throttle
    :type throttle: Optional[AstNode[EventThrottle]]
    """

    name: Ident
    params: FormalParamList
    severity: "SpecEventSeverity"
    id: Optional[AstNode[Expr]]
    format: AstNode[str]
    throttle: Optional[AstNode[EventThrottle]]


class SpecEventSeverity(Enum):
    """
    Represent event severity

    Attributes:
        ACTIVITY_HIGH
        ACTIVITY_LOW
        COMMAND
        DIAGNOSTIC
        FATAL
    """

    ACTIVITY_HIGH = "activity high"
    ACTIVITY_LOW = "activity low"
    COMMAND = "command"
    DIAGNOSTIC = "diagnostic"
    FATAL = "FATAL"
    WARNING_HIGH = "warning high"
    WARNING_LOW = "warning low"

    # override __str__ function to return the event string
    def __str__(self):
        return self.value


@dataclass(frozen=True)
class SpecInclude(FrozenAstData):
    """
    Include specifier

    :param file: Include file path
    :type file: AstNode[str]
    """

    file: AstNode[str]


@dataclass(frozen=True)
class SpecInit(FrozenAstData):
    """
    Init specifier

    :param phase: Init phase
    :type phase: AstNode[Expr]
    :param code: Init code
    """

    phase: AstNode[Expr]
    code: str


@dataclass(frozen=True)
class SpecInternalPort(FrozenAstData):
    """
    Internal port specifier

    :param name: Internal port name
    :type name: Ident
    :param params: Internal port formal parameters
    :type params: FormalParamList
    :param priority: Internal port priority
    :type priority: Optional[AstNode[Expr]]
    :param queue_full: Internal port queue full behavior
    :type queue_full: Optional[QueueFull]
    """

    name: Ident
    params: FormalParamList
    priority: Optional[AstNode[Expr]]
    queue_full: Optional[QueueFull]


@dataclass(frozen=True)
class SpecLoc(FrozenAstData):
    """
    Location specifier

    :param kind: Location specifier kind
    :type kind: SpecLocKind
    :param symbol: Location symbol
    :type symbol: AstNode[QualIdent]
    :param file: Path of the FPP source file
    :type file: AstNode[str]
    :param is_dictionary_def: Whether the location specifier specified the location of a dictionary definition
    :type is_dictionary_def: bool
    """

    kind: "SpecLocKind"
    symbol: AstNode[QualIdent]
    file: AstNode[str]
    is_dictionary_def: bool


class SpecLocKind(Enum):
    """
    Represents location specifier kind

    Attributes:
        COMPONENT
        INSTANCE
        CONSTANT
        PORT
        STATE_MACHINE
        TYPE
        INTERFACE
    """

    COMPONENT = "component"
    INSTANCE = "instance"
    CONSTANT = "constant"
    PORT = "port"
    STATE_MACHINE = "state machine"
    TYPE = "type"
    INTERFACE = "interface"

    def __str__(self):
        return self.value


@dataclass(frozen=True)
class SpecParam(FrozenAstData):
    """
    Parameter specifier

    :param name: Parameter name
    :type name: Ident
    :param type_name: Parameter type
    :type type_name: AstNode[TypeName]
    :param default: Parameter default value
    :type default: Optional[AstNode[Expr]]
    :param id: Parameter identifier
    :type id: Optional[AstNode[Expr]]
    :param set_opcode: Parameter set opcode
    :type set_opcode: Optional[AstNode[Expr]]
    :param save_opcode: Parameter save opcode
    :type save_opcode: Optional[AstNode[Expr]]
    :param is_external: Whether the parameter is external
    :type is_external: bool
    """

    name: Ident
    type_name: AstNode["TypeName"]
    default: Optional[AstNode[Expr]]
    id: Optional[AstNode[Expr]]
    set_opcode: Optional[AstNode[Expr]]
    save_opcode: Optional[AstNode[Expr]]
    is_external: bool


class SpecPortInstance(ABC):
    pass


@dataclass(frozen=True)
class GeneralPortInstance(SpecPortInstance, FrozenAstData):
    """
    General port instance specifier

    :param kind: General port instance kind
    :type kind: GeneralKind
    :param name: Port name
    :type name: Ident
    :param size: Port size
    :type size: Optional[AstNode[Expr]]
    :param port: Port identifier
    :type port: Optional[AstNode[QualIdent]]
    :param priority: General port instance priority
    :type priority: Optional[AstNode[Expr]]
    :param queue_full: General port instance queue full behavior
    :type queue_full: Optional[QueueFull]
    """

    kind: "GeneralKind"
    name: Ident
    size: Optional[AstNode[Expr]]
    port: Optional[AstNode[QualIdent]]
    priority: Optional[AstNode[Expr]]
    queue_full: Optional[AstNode[QueueFull]]


@dataclass(frozen=True)
class SpecialPortInstance(SpecPortInstance, FrozenAstData):
    """
    Special port instance specifier

    :param input_kind: Special port input kind
    :type input_kind: Optional[SpecialInputKind]
    :param kind: Special port instance kind
    :type kind: SpecialKind
    :param name: Port name
    :type name: Ident
    :param priority: Special port instance priority
    :type priority: Optional[AstNode[Expr]]
    :param queue_full: Special port instance queue full behavior
    :type queue_full: Optional[AstNode[QueueFull]]
    """

    input_kind: Optional["SpecialInputKind"]
    kind: "SpecialKind"
    name: Ident
    priority: Optional[AstNode[Expr]]
    queue_full: Optional[AstNode[QueueFull]]


class GeneralKind(Enum):
    """
    Represents general port instance kind

    Attributes:
        ASYNC_INPUT
        GUARDED_INPUT
        OUTPUT
        SYNC_INPUT
    """

    ASYNC_INPUT = "async input"
    GUARDED_INPUT = "guarded input"
    OUTPUT = "output"
    SYNC_INPUT = "sync input"

    def __str__(self):
        return self.value


class SpecialInputKind(Enum):
    """
    Represents special port input kind

    Attributes:
        ASYNC
        GUARDED
        SYNC
    """

    ASYNC = "async"
    GUARDED = "guarded"
    SYNC = "sync"

    def __str__(self):
        return self.value


class SpecialKind(Enum):
    """
    Represents special port instance kind

    Attributes:
        COMMAND_RECV
        COMMAND_REG
        COMMAND_RESP
        EVENT
        PARAM_GET
        PARAM_SET
        PRODUCT_GET
        PRODUCT_RECV
        PRODUCT_REQUEST
        PRODUCT_SEND
        TELEMETRY
        TEXT_EVENT
        TIME_GET
    """

    COMMAND_RECV = "command recv"
    COMMAND_REG = "command reg"
    COMMAND_RESP = "command resp"
    EVENT = "event"
    PARAM_GET = "param get"
    PARAM_SET = "param set"
    PRODUCT_GET = "product get"
    PRODUCT_RECV = "product recv"
    PRODUCT_REQUEST = "product request"
    PRODUCT_SEND = "product send"
    TELEMETRY = "telemetry"
    TEXT_EVENT = "text event"
    TIME_GET = "time get"

    def __str__(self):
        return self.value


@dataclass(frozen=True)
class SpecPortMatching(FrozenAstData):
    """
    Port matching specifier

    :param port1: Port 1
    :type port1: AstNode[Ident]
    :param port2: Port 2
    :type port2: AstNode[Ident]
    """

    port1: AstNode[Ident]
    port2: AstNode[Ident]


@dataclass(frozen=True)
class SpecRecord(FrozenAstData):
    """
    Record specifier

    :param name: Record name
    :type name: Ident
    :param record_type: Record type
    :type record_type: AstNode[TypeName]
    :param is_array: Whether the record is an array
    :type is_array: bool
    :param id: Record identifier
    :type id: Optional[AstNode[Expr]]
    """

    name: Ident
    record_type: AstNode["TypeName"]
    is_array: bool
    id: Optional[AstNode[Expr]]


@dataclass(frozen=True)
class SpecStateMachineInstance(FrozenAstData):
    """
    State machine instance specifier

    :param name: State machine instance name
    :type name: Ident
    :param state_machine: State machine AST node
    :type state_machine: AstNode[QualIdent]
    :param priority: State machine instance priority
    :type priority: Optional[AstNode[Expr]]
    :param queue_full: State machine instance queue full behavior
    :type queue_full: Optional[QueueFull]
    """

    name: Ident
    state_machine: AstNode[QualIdent]
    priority: Optional[AstNode[Expr]]
    queue_full: Optional[QueueFull]


@dataclass(frozen=True)
class SpecTlmChannel(FrozenAstData):
    """
    Telemetry channel specifier

    :param name: Channel name
    :type name: Ident
    :param type_name: Channel type
    :type type_name: AstNode[TypeName]
    :param id: Channel identifier
    :type id: Optional[AstNode[Expr]]
    :param update: Channel update
    :type update: Optional[AstNode[SpecTlmChannelUpdate]]
    :param format: Channel format string
    :type format: Optional[AstNode[str]]
    :param low: Channel lower limit
    :type low: List[Limit]
    :param high: Channel upper limit
    :type high: List[Limit]
    """

    name: Ident
    type_name: AstNode["TypeName"]
    id: Optional[AstNode[Expr]]
    update: Optional["SpecTlmChannelUpdate"]
    format: Optional[AstNode[str]]
    low: List["Limit"]
    high: List["Limit"]


class SpecTlmChannelUpdate(Enum):
    """
    Represents telemetry channel update

    Attributes:
        ALWAYS
        ON_CHANGE
    """

    ALWAYS = "always"
    ON_CHANGE = "on change"

    def __str__(self):
        return self.value


@dataclass(frozen=True)
class SpecTlmPacket(FrozenAstData):
    """
    Telemetry packet specifier

    :param name: Packet name
    :type name: Ident
    :param id: Packet identifier
    :type id: Optional[AstNode[Expr]]
    :param group: Packet group
    :type group: AstNode[Expr]
    :param members: List of telemetry packet members
    """

    name: Ident
    id: Optional[AstNode[Expr]]
    group: AstNode[Expr]
    members: List["TlmPacketMember"]


@dataclass(frozen=True)
class SpecTlmPacketSet(FrozenAstData):
    """
    Telemetry packet set specifier

    :param name: Packet set name
    :type name: Ident
    :param members: List of telemetry packet set members
    :type members: List[TlmPacketSetMember]
    :param omitted: List of omitted telemetry channels
    :type omitted: List[AstNode[TlmChannelIdentifier]]
    """

    name: Ident
    members: List["TlmPacketSetMember"]
    omitted: List[AstNode["TlmChannelIdentifier"]]


@dataclass(frozen=True)
class SpecTopPort(FrozenAstData):
    name: Ident
    underlying_port: AstNode["PortInstanceIdentifier"]


@dataclass(frozen=True)
class SpecImport(FrozenAstData):
    """
    Import specifier

    :param sym: Qualified identifier
    :type sym: AstNode[QualIdent]
    """

    sym: AstNode[QualIdent]


@dataclass(frozen=True)
class SpecInitialTransition(FrozenAstData):
    """
    Initial transition specifier

    :param transition: Initial transition
    :type transition: AstNode[TransitionExpr]
    """

    transition: AstNode["TransitionExpr"]


@dataclass(frozen=True)
class SpecStateEntry(FrozenAstData):
    """
    State entry specifier

    :param actions: List of actions
    :type actions: List[AstNode[Ident]]
    """

    actions: List[AstNode[Ident]]


@dataclass(frozen=True)
class SpecStateExit(FrozenAstData):
    """
    State exit specifier

    :param actions: List of actions
    :type actions: List[AstNode[Ident]]
    """

    actions: List[AstNode[Ident]]


@dataclass(frozen=True)
class SpecStateTransition(FrozenAstData):
    """
    State transition specifier

    :param signal: Signal definition identifier
    :type signal: AstNode[Ident]
    :param guard: Guard expression identifier
    :type guard: Optional[AstNode[Ident]]
    :param transition_or_do: Transition or do expression
    :type transition_or_do: AstNode[TransitionOrDo]
    """

    signal: AstNode[Ident]
    guard: Optional[AstNode[Ident]]
    transition_or_do: "TransitionOrDo"


Limit: TypeAlias = Tuple[AstNode["LimitKind"], AstNode[Expr]]


class LimitKind(Enum):
    """
    Represents telemetry channel limit kind

    Attributes:
        RED
        ORANGE
        YELLOW
    """

    RED = "red"
    ORANGE = "orange"
    YELLOW = "yellow"

    def __str__(self):
        return self.value


class TypeFloat(Enum):
    """
    Represents float type

    Attributes:
        F32
        F64
    """

    F32 = "F32"
    F64 = "F64"

    def __str__(self):
        return self.value


class TypeInt(Enum):
    """
    Represents integer type

    Attributes:
        I8
        I16
        I32
        I64
        U8
        U16
        U32
    """

    I8 = "I8"
    I16 = "I16"
    I32 = "I32"
    I64 = "I64"
    U8 = "U8"
    U16 = "U16"
    U32 = "U32"
    U64 = "U64"

    def __str__(self):
        return self.value


class TypeName(ABC):
    pass


@dataclass(frozen=True)
class TypeNameFloat(TypeName, FrozenAstData):
    """
    Float type name

    :param name: Float type name
    :type name: TypeFloat
    """

    name: TypeFloat


@dataclass(frozen=True)
class TypeNameInt(TypeName, FrozenAstData):
    """
    Integer type name

    :param name: Integer type name
    :type name: TypeInt
    """

    name: TypeInt


@dataclass(frozen=True)
class TypeNameQualIdent(TypeName, FrozenAstData):
    """
    Qualified identifier type name

    :param name: Qualified identifier type name
    :type name: AstNode[QualIdent]
    """

    name: AstNode[QualIdent]


@dataclass(frozen=True)
class TypeNameBool(TypeName, FrozenAstData):
    """
    Boolean type name
    """

    pass


@dataclass(frozen=True)
class TypeNameString(TypeName, FrozenAstData):
    """
    String type name

    :param size: String maximum length
    :type size: Optional[AstNode[Expr]]
    """

    size: Optional[AstNode[Expr]]


class Unop(Enum):
    """
    Represents unary operation

    Attributes:
        MINUS

    """

    MINUS = "-"

    def __str__(self):
        return self.value


@dataclass(frozen=True)
class FormalParam(FrozenAstData):
    """
    Formal parameter

    :param kind: Formal parameter kind
    :type kind: FormalParamKind
    :param name: Formal parameter name
    :type name: Ident
    :param type_name: Formal parameter type name
    :type type_name: AstNode[TypeName]
    """

    kind: "FormalParamKind"
    name: Ident
    type_name: AstNode[TypeName]


class FormalParamKind(Enum):
    """
    Formal parameter kind

    Attributes:
        REF
        VALUE
    """

    REF = "ref"
    VALUE = "value"


class LiteralBool(Enum):
    """
    Literal Boolean

    Attributes:
        TRUE
        FALSE
    """

    TRUE = "true"
    FALSE = "false"

    # override __str__ function to return the literal bool string
    def __str__(self):
        return self.value


@dataclass(frozen=True)
class PortInstanceIdentifier(FrozenAstData):
    """
    Port instance identifier

    :param interface_instance: Interface instance AST node
    :type interface_instance: AstNode[QualIdent]
    :param port_name: Port name AST node
    :type port_name: AstNode[Ident]
    """

    interface_instance: AstNode[QualIdent]
    port_name: AstNode[Ident]


@dataclass(frozen=True)
class TransitionExpr(FrozenAstData):
    """
    Transition expression

    :param actions: List of actions
    :type actions: List[AstNode[Ident]]
    :param target: Target AST node
    :type target: AstNode[QualIdent]
    """

    actions: List[AstNode[Ident]]
    target: AstNode[QualIdent]


class TransitionOrDo(ABC):
    """
    Transition or do within transition specifier
    """

    pass


@dataclass(frozen=True)
class Transition(TransitionOrDo, FrozenAstData):
    """
    Transition within transition specifier

    :param transition: Transition expression
    :type transition: AstNode[TransitionExpr]
    """

    transition: AstNode[TransitionExpr]


@dataclass(frozen=True)
class Do(TransitionOrDo, FrozenAstData):
    """
    Do within transition specifier

    :param actions: List of actions
    :type actions: List[AstNode[Ident]]
    """

    actions: List[AstNode[Ident]]


@dataclass(frozen=True)
class StructMember(FrozenAstData):
    """
    Struct member

    :param name: Member name
    :type name: Ident
    :param value: Member value
    :type value: AstNode[Expr]
    """

    name: Ident
    value: AstNode[Expr]


@dataclass(frozen=True)
class StructTypeMember(FrozenAstData):
    """
    Struct type member

    :param name: Member name
    :type name: Ident
    :param size: Member size
    :type size: Optional[AstNode[Expr]]
    :param type_name: Member type name
    :type type_name: AstNode[TypeName]
    :param format: Member format string
    :type format: Optional[AstNode[str]]
    """

    name: Ident
    size: Optional[AstNode[Expr]]
    type_name: AstNode[TypeName]
    format: Optional[AstNode[str]]


@dataclass(frozen=True)
class TlmChannelIdentifier(FrozenAstData):
    """
    Telemetry channel identifier

    :param component_instance: Qualified name of component instance
    :type component_instance: AstNode[QualIdent]
    :param channel_name: Qualified name of channel
    :type channel_name: AstNode[Ident]
    """

    component_instance: AstNode[QualIdent]
    channel_name: AstNode[Ident]
