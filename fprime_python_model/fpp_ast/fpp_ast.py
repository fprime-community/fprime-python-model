from abc import ABC, abstractmethod
from typing import List, TypeAlias, Optional, Tuple, override, TypeVar
from dataclasses import dataclass
from enum import Enum
from fprime_python_model.fpp_ast.fpp_ast_node import AstNode
from fprime_python_model.utils.error import InternalError

T = TypeVar("T")
Annotated: TypeAlias = Tuple[List[str], T, List[str]]
Ident: TypeAlias = str
type FormalParamList = List[Annotated[AstNode["FormalParam"]]]
TUMember: TypeAlias = "ModuleMember"


@dataclass
class TransUnit:
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


@dataclass(eq=True)
class Unqualified(QualIdent):
    """An unqualified identifier

    :param name: Unqualified identifier name
    :type name: Ident
    """

    name: Ident

    @override
    def to_ident_list(self):
        return [self.name]

    def __hash__(self):
        return hash(self.name)


@dataclass
class Qualified(QualIdent):
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


@dataclass
class DefAbsType:
    """
    Abstract type definition

    :param name: Name of the abstract type
    :type name: Ident
    """

    name: Ident


@dataclass
class DefAliasType:
    """
    Aliased type definition

    :param name: Name of the alias type
    :type name: Ident
    :param type_name: Type name that the alias type represents
    :type type_name: AstNode[TypeName]
    """

    name: Ident
    type_name: AstNode["TypeName"]


@dataclass
class DefArray:
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
    """

    name: Ident
    size: AstNode["Expr"]
    elt_type: AstNode["TypeName"]
    default: Optional[AstNode["Expr"]]
    format: Optional[AstNode[str]]


@dataclass
class DefComponent:
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


@dataclass
class DefComponentInstance:
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


@dataclass
class DefConstant:
    """
    Constant definition

    :param: name: Name of the constant
    :type name: Ident
    :param value: Value of the constant
    :type value: AstNode[Expr]

    """

    name: Ident
    value: AstNode["Expr"]


@dataclass
class DefEnum:
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
    """

    name: Ident
    type_name: Optional[AstNode["TypeName"]]
    constants: List[Annotated[AstNode["DefEnumConstant"]]]
    default: Optional[AstNode["Expr"]]


@dataclass
class DefEnumConstant:
    """
    Enum constant definition

    :param name: Name of the enum constant
    :type name: Ident
    :param value: Value of the enum
    :type value: Optional[AstNode[Expr]]
    """

    name: Ident
    value: Optional[AstNode["Expr"]]


@dataclass
class DefModule:
    """
    Module definition

    :param name: Name of the module
    :type name: Ident
    :param members: List of module members
    :type members: List[ModuleMember]
    """

    name: Ident
    members: List["ModuleMember"]


@dataclass
class DefPort:
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


@dataclass
class DefStateMachine:
    """
    State machine definition

    :param name: Name of the state machine
    :type name: Ident
    :param members: List of state machine members
    :type members: List[StateMachineMember]
    """

    name: Ident
    members: Optional[List["StateMachineMember"]]


@dataclass
class DefAction:
    """
    Action definition

    :param name: Name of the action
    :type name: Ident
    :param type_name: Type name of the action
    :type type_name: Optional[AstNode[TypeName]]
    """

    name: Ident
    type_name: Optional[AstNode["TypeName"]]


@dataclass
class DefChoice:
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


@dataclass
class DefGuard:
    """
    Guard definition

    :param name: Name of the guard
    :type name: Ident
    :param type_name: Type name of the guard
    :type type_name: Optional[AstNode[TypeName]]
    """

    name: Ident
    type_name: Optional[AstNode["TypeName"]]


@dataclass
class DefSignal:
    """
    Signal definition

    :param name: Name of the signal
    :type name: Ident
    :param type_name: Type name of the signal
    :type type_name: Optional[AstNode[TypeName]]
    """

    name: Ident
    type_name: Optional[AstNode["TypeName"]]


@dataclass
class DefState:
    """
    State definition

    :param name: Name of the state
    :type name: Ident
    :param members: List of state members
    :type members: List[StateMember]
    """

    name: Ident
    members: List["StateMember"]


@dataclass
class DefInterface:
    """
    Interface definition

    :param name: Name of the interface
    :type name: Ident
    :param members: List of interface members
    :type members: List[InterfaceMember]
    """

    name: Ident
    members: List["InterfaceMember"]


@dataclass
class DefStruct:
    """
    Struct definition

    :param name: Name of the struct
    :type name: Ident
    :param members: List of struct members
    :type members: List[Annotated[AstNode[StructMember]]]
    :param default: Default value of the struct
    :type default: Optional[AstNode[Expr]]
    """

    name: Ident
    members: List[Annotated[AstNode["StructTypeMember"]]]
    default: Optional[AstNode["Expr"]]


@dataclass
class DefTopology:
    """
    Topology defintion

    :param name: Name of the topology
    :type name: Ident
    :param members: List of topology members
    :type members: List[TopologyMember]
    """

    name: Ident
    members: List["TopologyMember"]


##########################
### Component Member
##########################


class ComponentMemberNode(ABC):
    pass


@dataclass
class ComponentMember:
    """
    Component member with annotated component member node

    :param node: Annotated component member node
    :type node: Annotated[ComponentMemberNode]
    """

    node: Annotated[ComponentMemberNode]


@dataclass
class ComponentMemberDefAbsType(ComponentMemberNode):
    """
    Abstract type component member

    :param node: Abstract type definition AST node
    :type node: AstNode[DefAbsType]
    """

    node: AstNode[DefAbsType]


@dataclass
class ComponentMemberDefAliasType(ComponentMemberNode):
    """
    Alias type component member

    :param node: Alias type definition AST node
    :type node: AstNode[DefAliasType]
    """

    node: AstNode[DefAliasType]


@dataclass
class ComponentMemberDefArray(ComponentMemberNode):
    """
    Array component member

    :param node: Array definition AST node
    :type node: AstNode[DefArray]
    """

    node: AstNode[DefArray]


@dataclass
class ComponentMemberDefConstant(ComponentMemberNode):
    """
    Constant component member

    :param node: Constant definition AST node
    :type node: AstNode[DefConstant]
    """

    node: AstNode[DefConstant]


@dataclass
class ComponentMemberDefEnum(ComponentMemberNode):
    """
    Enum component member

    :param node: Enum definition AST node
    :type node: AstNode[DefEnum]
    """

    node: AstNode[DefEnum]


@dataclass
class ComponentMemberDefStateMachine(ComponentMemberNode):
    """
    State machine component member

    :param node: State machine definition AST node
    :type node: AstNode[DefStateMachine]
    """

    node: AstNode[DefStateMachine]


@dataclass
class ComponentMemberDefStruct(ComponentMemberNode):
    """
    Struct component member

    :param node: Struct definition AST node
    :type node: AstNode[DefStruct]
    """

    node: AstNode[DefStruct]


@dataclass
class ComponentMemberSpecCommand(ComponentMemberNode):
    """
    Command component member

    :param node: Command specifier AST node
    :type node: AstNode[SpecCommand]
    """

    node: AstNode["SpecCommand"]


@dataclass
class ComponentMemberSpecContainer(ComponentMemberNode):
    """
    Container component member

    :param node: Container specifier AST node
    :type node: AstNode[SpecContainer]
    """

    node: AstNode["SpecContainer"]


@dataclass
class ComponentMemberSpecEvent(ComponentMemberNode):
    """
    Event component member

    :param node: Event specifier AST node
    :type node: AstNode[SpecEvent]
    """

    node: AstNode["SpecEvent"]


@dataclass
class ComponentMemberSpecInclude(ComponentMemberNode):
    """
    Include specifier component member

    :param node: Include specifier AST node
    :type node: AstNode[SpecInclude]
    """

    node: AstNode["SpecInclude"]


@dataclass
class ComponentMemberSpecInternalPort(ComponentMemberNode):
    """
    Internal port specifier component member

    :param node: Internal port specifier AST node
    :type node: AstNode[SpecInternalPort]
    """

    node: AstNode["SpecInternalPort"]


@dataclass
class ComponentMemberSpecParam(ComponentMemberNode):
    """
    Param component member

    :param node: Param specifier AST node
    :type node: AstNode[SpecParam]
    """

    node: AstNode["SpecParam"]


@dataclass
class ComponentMemberSpecPortInstance(ComponentMemberNode):
    """
    Port instance component member

    :param node: Port instance specifier AST node
    :type node: AstNode[SpecPortInstance]
    """

    node: AstNode["SpecPortInstance"]


@dataclass
class ComponentMemberSpecPortMatching(ComponentMemberNode):
    """
    Port matching component member

    :param node: Port matching specifier AST node
    :type node: AstNode[SpecPortMatching]
    """

    node: AstNode["SpecPortMatching"]


@dataclass
class ComponentMemberSpecRecord(ComponentMemberNode):
    """
    Record component member

    :param node: Record specifier AST node
    :type node: AstNode[SpecRecord]
    """

    node: AstNode["SpecRecord"]


@dataclass
class ComponentMemberSpecStateMachineInstance(ComponentMemberNode):
    """
    State machine instance component member

    :param node: State machine instance specifier AST node
    :type node: AstNode[SpecStateMachineInstance]
    """

    node: AstNode["SpecStateMachineInstance"]


@dataclass
class ComponentMemberSpecTlmChannel(ComponentMemberNode):
    """
    Telemetry channel component member

    :param node: Telemetry channel specifier AST node
    :type node: AstNode[SpecTlmChannel]
    """

    node: AstNode["SpecTlmChannel"]


@dataclass
class ComponentMemberSpecImportInterface(ComponentMemberNode):
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


@dataclass
class ModuleMember:
    """
    Module member with annotated module member node

    :param node: Annotated module member node
    :type node: Annotated[ModuleMemberNode]

    """

    node: Annotated[ModuleMemberNode]


@dataclass
class ModuleMemberDefAbsType(ModuleMemberNode):
    """
    Abstract type module member

    :param node: Abstract type definition AST node
    :type node: AstNode[DefAbsType]
    """

    node: AstNode[DefAbsType]


@dataclass
class ModuleMemberDefAliasType(ModuleMemberNode):
    """
    Alias type module member

    :param node: Alias type definition AST node
    :type node: AstNode[DefAliasType]
    """

    node: AstNode[DefAliasType]


@dataclass
class ModuleMemberDefArray(ModuleMemberNode):
    """
    Array module member

    :param node: Array definition AST node
    :type node: AstNode[DefArray]
    """

    node: AstNode[DefArray]


@dataclass
class ModuleMemberDefComponent(ModuleMemberNode):
    """
    Component module member

    :param node: Component definition AST node
    :type node: AstNode[DefComponent]
    """

    node: AstNode[DefComponent]


@dataclass
class ModuleMemberDefComponentInstance(ModuleMemberNode):
    """
    Component instance module member

    :param node: Component instance definition AST node
    :type node: AstNode[DefComponentInstance]
    """

    node: AstNode[DefComponentInstance]


@dataclass
class ModuleMemberDefConstant(ModuleMemberNode):
    """
    Constant module member

    :param node: Constant definition AST node
    :type node: AstNode[DefConstant]
    """

    node: AstNode[DefConstant]


@dataclass
class ModuleMemberDefEnum(ModuleMemberNode):
    """
    Enum module member

    :param node: Enum definition AST node
    :type node: AstNode[DefEnum]
    """

    node: AstNode[DefEnum]


@dataclass
class ModuleMemberDefInterface(ModuleMemberNode):
    """
    Interface module member

    :param node: Interface definition AST node
    :type node: AstNode[DefInterface]
    """

    node: AstNode["DefInterface"]


@dataclass
class ModuleMemberDefModule(ModuleMemberNode):
    """
    Module module member

    :param node: Module definition AST node
    :type node: AstNode[DefModule]
    """

    node: AstNode[DefModule]


@dataclass
class ModuleMemberDefPort(ModuleMemberNode):
    """
    Port module member

    :param node: Port definition AST node
    :type node: AstNode[DefPort]
    """

    node: AstNode["DefPort"]


@dataclass
class ModuleMemberDefStateMachine(ModuleMemberNode):
    """
    State machine module member

    :param node: State machine definition AST node
    :type node: AstNode[DefStateMachine]
    """

    node: AstNode["DefStateMachine"]


@dataclass
class ModuleMemberDefStruct(ModuleMemberNode):
    """
    Struct module member

    :param node: Struct definition AST node
    :type node: AstNode[DefStruct]
    """

    node: AstNode["DefStruct"]


@dataclass
class ModuleMemberDefTopology(ModuleMemberNode):
    """
    Topology module member

    :param node: Topology definition AST node
    :type node: AstNode[DefTopology]
    """

    node: AstNode["DefTopology"]


@dataclass
class ModuleMemberSpecInclude(ModuleMemberNode):
    """
    Include specifier module member

    :param node: Include specifier AST node
    :type node: AstNode[SpecInclude]
    """

    node: AstNode["SpecInclude"]


@dataclass
class ModuleMemberSpecLoc(ModuleMemberNode):
    """
    Location specifier module member

    :param node: Location specifier AST node
    :type node: AstNode[SpecLoc]
    """

    node: AstNode["SpecLoc"]


##########################
### State Machine Member
##########################


@dataclass
class StateMachineMember:
    """
    State machine member with annotated state machine member member node

    :param node: Annotated state machine member node
    :type node: Annotated[StateMachineMemberNode]
    """

    node: Annotated["StateMachineMemberNode"]


class StateMachineMemberNode(ABC):
    pass


@dataclass
class StateMachineMemberDefAction(StateMachineMemberNode):
    """
    Action state machine member

    :param node: Action definition AST node
    :type node: AstNode[DefAction]
    """

    node: AstNode["DefAction"]


@dataclass
class StateMachineMemberDefChoice(StateMachineMemberNode):
    """
    Choice state machine member

    :param node: Choice definition AST node
    :type node: AstNode[DefChoice]
    """

    node: AstNode["DefChoice"]


@dataclass
class StateMachineMemberDefGuard(StateMachineMemberNode):
    """
    Guard state machine member

    :param node: Guard definition AST node
    :type node: AstNode[DefGuard]
    """

    node: AstNode["DefGuard"]


@dataclass
class StateMachineMemberDefSignal(StateMachineMemberNode):
    """
    Signal state machine member

    :param node: Signal definition AST node
    :type node: AstNode[DefSignal]
    """

    node: AstNode["DefSignal"]


@dataclass
class StateMachineMemberDefState(StateMachineMemberNode):
    """
    State state machine member

    :param node: State definition AST node
    :type node: AstNode[DefState]
    """

    node: AstNode["DefState"]


@dataclass
class StateMachineMemberSpecInitialTransition(StateMachineMemberNode):
    """
    Initial transition state machine member

    :param node: Initial transition specifier AST node
    :type node: AstNode[SpecInitialTransition]
    """

    node: AstNode["SpecInitialTransition"]


##########################
### State Member
##########################


@dataclass
class StateMember:
    """
    State member with annotated state member node

    :param node: Annotated state member node
    :type node: Annotated[StateMemberNode]
    """

    node: Annotated["StateMemberNode"]


class StateMemberNode(ABC):
    pass


@dataclass
class StateMemberDefChoice(StateMemberNode):
    """
    Choice state member

    :param node: Choice definition AST node
    :type node: AstNode[DefChoice]
    """

    node: AstNode[DefChoice]


@dataclass
class StateMemberDefState(StateMemberNode):
    """
    State state member

    :param node: State definition AST node
    :type node: AstNode[DefState]
    """

    node: AstNode[DefState]


@dataclass
class StateMemberSpecStateEntry(StateMemberNode):
    """
    State entry state member

    :param node: State entry specifier AST node
    :type node: AstNode[SpecStateEntry]
    """

    node: AstNode["SpecStateEntry"]


@dataclass
class StateMemberSpecStateExit(StateMemberNode):
    """
    State exit state member

    :param node: State exit specifier AST node
    :type node: AstNode[SpecStateExit]
    """

    node: AstNode["SpecStateExit"]


@dataclass
class StateMemberSpecInitialTransition(StateMemberNode):
    """
    Initial state state member

    :param node: Initial transition specifier AST node
    :type node: AstNode[SpecInitialTransition]
    """

    node: AstNode["SpecInitialTransition"]


@dataclass
class StateMemberSpecStateTransition(StateMemberNode):
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


@dataclass
class ExprArray(Expr):
    """
    Array expression

    :param elts: List of expression AST nodes
    :type elts: List[AstNode[Expr]]
    """

    elts: List[AstNode[Expr]]


@dataclass
class ExprBinop(Expr):
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


@dataclass
class ExprDot(Expr):
    """
    Dot expression

    :param e: Expression AST node
    :type e: AstNode[Expr]
    :param id: Identifier AST node
    :type id: AstNode[Ident]
    """

    e: AstNode[Expr]
    id: AstNode[Ident]


@dataclass
class ExprIdent(Expr):
    """
    Ident expression

    :param value: Identifier AST node
    :type value: AstNode[Ident]
    """

    value: Ident


@dataclass
class ExprLiteralBool(Expr):
    """
    Literal Boolean expression

    :param value: Boolean value
    :type value: LiteralBool
    """

    value: "LiteralBool"


@dataclass
class ExprLiteralInt(Expr):
    """
    Literal integer expression

    :param value: Integer value
    :type value: str
    """

    value: str


@dataclass
class ExprLiteralFloat(Expr):
    """
    Literal float expression

    :param value: Float value
    :type value: str
    """

    value: str


@dataclass
class ExprLiteralString(Expr):
    """
    Literal string expression

    :param value: String value
    :type value: str
    """

    value: str


@dataclass
class ExprParen(Expr):
    """
    Parenthesis expression

    :param e: Expression AST node
    :type e: AstNode[Expr]
    """

    e: AstNode[Expr]


@dataclass
class ExprStruct(Expr):
    """
    Struct expression

    :param members: List of struct member AST nodes
    :type members: List[AstNode[StructMember]]
    """

    members: List[AstNode["StructMember"]]


@dataclass
class ExprUnop(Expr):
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


@dataclass
class TopologyMember:
    """
    Topology member with anotated topology member node

    :param node: Annotated topology member node
    :type node: Annotated[TopologyMemberNode]
    """

    node: Annotated[TopologyMemberNode]


@dataclass
class TopologyMemberSpecCompInstance(TopologyMemberNode):
    """
    Component instance topology member

    :param node: Component instance specifier AST node
    :type node: AstNode[SpecCompInstance]
    """

    node: AstNode["SpecCompInstance"]


@dataclass
class TopologyMemberSpecConnectionGraph(TopologyMemberNode):
    """
    Connection graph topology member

    :param node: Connection graph specifier AST node
    :type node: AstNode[SpecConnectionGraph]
    """

    node: AstNode["SpecConnectionGraph"]


@dataclass
class TopologyMemberSpecInclude(TopologyMemberNode):
    """
    Include specifier topology member

    :param node: Include specifier AST node
    :type node: AstNode[SpecInclude]
    """

    node: AstNode["SpecInclude"]


@dataclass
class TopologyMemberSpecTlmPacketSet(TopologyMemberNode):
    """
    Telemetry packet set topology member

    :param node: Telemetry packet set specifier AST node
    :type node: AstNode[SpecTlmPacketSet]
    """

    node: AstNode["SpecTlmPacketSet"]


@dataclass
class TopologyMemberSpecTopImport(TopologyMemberNode):
    """
    Topology import topology member

    :param node: Topology import specifier AST node
    :type node: AstNode[SpecTopImport]
    """

    node: AstNode["SpecImport"]


#################################
### Telemetry Packet Set Member
#################################


class TlmPacketSetMemberNode(ABC):
    pass


@dataclass
class TlmPacketSetMember:
    """
    Telemetry packet set member with annotated telemetry packet set member node

    :param node: Annotated telemetry packet set member node
    :type node: Annotated[TlmPacketSetMemberNode]
    """

    node: Annotated[TlmPacketSetMemberNode]


@dataclass
class TlmPacketSetMemberSpecInclude(TlmPacketSetMemberNode):
    """
    Include specifier telemetry packet set member

    :param node: Include specifier AST node
    :type node: AstNode[SpecInclude]
    """

    node: AstNode["SpecInclude"]


@dataclass
class TlmPacketSetMemberSpecTlmPacket(TlmPacketSetMemberNode):
    """
    Telemetry packet telemetry packet set member

    :param node: Telemetry packet specifier AST node
    :type node: AstNode[SpecTlmPacket]
    """

    node: AstNode["SpecTlmPacket"]


############################
### Interface Member
############################


@dataclass
class InterfaceMember:
    """
    Interface member with annotated interface member node

    :param node: Annotated interface member node
    :type node: Annotated[InterfaceMemberNode]
    """

    node: Annotated["InterfaceMemberNode"]


class InterfaceMemberNode(ABC):
    pass


@dataclass
class InterfaceMemberSpecPortInstance(InterfaceMemberNode):
    """
    Port instance interface member

    :param node: Port instance specifier AST node
    :type node: AstNode[SpecPortInstance]
    """

    node: AstNode["SpecPortInstance"]


@dataclass
class InterfaceMemberSpecImportInterface(InterfaceMemberNode):
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


@dataclass
class TlmPacketMemberSpecInclude(TlmPacketMember):
    """
    Include specifier telemetry packet member

    :param node: Include specifier AST node
    :type node: AstNode[SpecInclude]
    """

    node: AstNode["SpecInclude"]


@dataclass
class TlmPacketMemberTlmChannelIdentifier(TlmPacketMember):
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


@dataclass
class SpecCommand:
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


@dataclass
class SpecCompInstance:
    """
    Component instance specifier

    :param visibility: Component instance visibility
    :type visibility: Visibility
    :param instance: Component instance AST node
    :type instance: AstNode[QualIdent]
    """

    visibility: "Visibility"
    instance: AstNode[QualIdent]


class SpecConnectionGraph(ABC):
    pass


@dataclass
class Direct(SpecConnectionGraph):
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


@dataclass
class Pattern(SpecConnectionGraph):
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


@dataclass
class Connection:
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


@dataclass
class SpecContainer:
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


@dataclass
class SpecEvent:
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
    :type throttle: Optional[AstNode[Expr]]
    """

    name: Ident
    params: FormalParamList
    severity: "SpecEventSeverity"
    id: Optional[AstNode[Expr]]
    format: AstNode[str]
    throttle: Optional[AstNode[Expr]]


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


@dataclass
class SpecInclude:
    """
    Include specifier

    :param file: Include file path
    :type file: AstNode[str]
    """

    file: AstNode[str]


@dataclass
class SpecInit:
    """
    Init specifier

    :param phase: Init phase
    :type phase: AstNode[Expr]
    :param code: Init code
    """

    phase: AstNode[Expr]
    code: str


@dataclass
class SpecInternalPort:
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


@dataclass
class SpecLoc:
    """
    Location specifier

    :param kind: Location specifier kind
    :type kind: SpecLocKind
    :param symbol: Location symbol
    :type symbol: AstNode[QualIdent]
    :param file: Path of the FPP source file
    :type file: AstNode[str]
    """

    kind: "SpecLocKind"
    symbol: AstNode[QualIdent]
    file: AstNode[str]


class SpecLocKind(Enum):
    """
    Represents location specifier kind

    Attributes:
        COMPONENT
        COMPONENT_INSTANCE
        CONSTANT
        PORT
        STATE_MACHINE
        TOPOLOGY
        TYPE
        INTERFACE
    """

    COMPONENT = "component"
    COMPONENT_INSTANCE = "instance"
    CONSTANT = "constant"
    PORT = "port"
    STATE_MACHINE = "state machine"
    TOPOLOGY = "topology"
    TYPE = "type "
    INTERFACE = "interface"

    def __str__(self):
        return self.value


@dataclass
class SpecParam:
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


@dataclass
class GeneralPortInstance(SpecPortInstance):
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


@dataclass
class SpecialPortInstance(SpecPortInstance):
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


@dataclass
class SpecPortMatching:
    """
    Port matching specifier

    :param port1: Port 1
    :type port1: AstNode[Ident]
    :param port2: Port 2
    :type port2: AstNode[Ident]
    """

    port1: AstNode[Ident]
    port2: AstNode[Ident]


@dataclass
class SpecRecord:
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


@dataclass
class SpecStateMachineInstance:
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


@dataclass
class SpecTlmChannel:
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


@dataclass
class SpecTlmPacket:
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


@dataclass
class SpecTlmPacketSet:
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


@dataclass
class SpecImport:
    """
    Import specifier

    :param sym: Qualified identifier
    :type sym: AstNode[QualIdent]
    """

    sym: AstNode[QualIdent]


@dataclass
class SpecInitialTransition:
    """
    Initial transition specifier

    :param transition: Initial transition
    :type transition: AstNode[TransitionExpr]
    """

    transition: AstNode["TransitionExpr"]


@dataclass
class SpecStateEntry:
    """
    State entry specifier

    :param actions: List of actions
    :type actions: List[AstNode[Ident]]
    """

    actions: List[AstNode[Ident]]


@dataclass
class SpecStateExit:
    """
    State exit specifier

    :param actions: List of actions
    :type actions: List[AstNode[Ident]]
    """

    actions: List[AstNode[Ident]]


@dataclass
class SpecStateTransition:
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


@dataclass
class TypeNameFloat(TypeName):
    """
    Float type name

    :param name: Float type name
    :type name: TypeFloat
    """

    name: TypeFloat


@dataclass
class TypeNameInt(TypeName):
    """
    Integer type name

    :param name: Integer type name
    :type name: TypeInt
    """

    name: TypeInt


@dataclass
class TypeNameQualIdent(TypeName):
    """
    Qualified identifier type name

    :param name: Qualified identifier type name
    :type name: AstNode[QualIdent]
    """

    name: AstNode[QualIdent]


@dataclass
class TypeNameBool(TypeName):
    """
    Boolean type name
    """

    pass


@dataclass
class TypeNameString(TypeName):
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


class Visibility(Enum):
    """
    Represents visbility

    Attributes:
        PRIVATE
        PUBLIC
    """

    PRIVATE = "private"
    PUBLIC = "public"

    def __str__(self):
        return self.value


@dataclass
class FormalParam:
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


@dataclass
class PortInstanceIdentifier:
    """
    Port instance identifier

    :param component_instance: Component instance AST node
    :type component_instance: AstNode[QualIdent]
    :param port_name: Port name AST node
    :type port_name: AstNode[Ident]
    """

    component_instance: AstNode[QualIdent]
    port_name: AstNode[Ident]


@dataclass
class TransitionExpr:
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


@dataclass
class Transition(TransitionOrDo):
    """
    Transition within transition specifier

    :param transition: Transition expression
    :type transition: AstNode[TransitionExpr]
    """

    transition: AstNode[TransitionExpr]


@dataclass
class Do(TransitionOrDo):
    """
    Do within transition specifier

    :param actions: List of actions
    :type actions: List[AstNode[Ident]]
    """

    actions: List[AstNode[Ident]]


@dataclass
class StructMember:
    """
    Struct member

    :param name: Member name
    :type name: Ident
    :param value: Member value
    :type value: AstNode[Expr]
    """

    name: Ident
    value: AstNode[Expr]


@dataclass
class StructTypeMember:
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


@dataclass
class TlmChannelIdentifier:
    """
    Telemetry channel identifier

    :param component_instance: Qualified name of component instance
    :type component_instance: AstNode[QualIdent]
    :param channel_name: Qualified name of channel
    :type channel_name: AstNode[Ident]
    """

    component_instance: AstNode[QualIdent]
    channel_name: AstNode[Ident]
