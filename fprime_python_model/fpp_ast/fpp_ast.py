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
    """Translation unit consisting of translation unit members
    """
    members: List[TUMember]


class Binop(Enum):
    """Binary operation
    """

    ADD = "+"
    DIV = "/"
    MUL = "*"
    SUB = "-"

    def __str__(self):
        return self.value


class ComponentKind(Enum):
    """Component kind
    """

    ACTIVE = "active"
    PASSIVE = "passive"
    QUEUED = "queued"

    def __str__(self):
        return self.value


class QualIdent(ABC):
    """A possibly-qualified identifier
    """

    @abstractmethod
    def to_ident_list(self) -> List[Ident]:
        """Convert a qualified identifier to a list of identifiers
        Returns:
            List[Ident]: List of identifiers
        """
        pass


@dataclass(eq=True)
class Unqualified(QualIdent):
    """An unqualified identifier
    """

    name: Ident

    @override
    def to_ident_list(self):
        return [self.name]

    def __hash__(self):
        return hash(self.name)


@dataclass
class Qualified(QualIdent):
    """A qualified identifier"""

    qualifier: AstNode[QualIdent]
    name: AstNode[Ident]

    @override
    def to_ident_list(self):
        return self.qualifier.data.to_ident_list() + [self.name.data]


def qual_ident_from_node_list(node_list: "NodeList") -> QualIdent:
    """Construct a qualified identifier from a node list

    Args:
        node_list (NodeList): List of Ident AST nodes

    Returns:
        QualIdent: Qualified identifier created from node list
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
    """Split a qualified identifier list into qualifier and name

    Args:
        node_list (NodeList): List of Ident AST nodes

    Raises:
        InternalError: Raised if the node list is empty

    Returns:
        Tuple[List[AstNode[Ident]], AstNode[Ident]]: _description_
    """
    rev: NodeList = node_list[::-1]
    if not rev:
        raise InternalError("node list should not be empty")
    else:
        return rev[1:][::-1], rev[0]


def qualifier(node_list: NodeList) -> List[AstNode[Ident]]:
    """Get the qualifier

    Args:
        node_list (NodeList): List of Ident AST nodes

    Returns:
        List[AstNode[Ident]]: List of qualifier Ident AST nodes
    """
    return split(node_list)[0]


def name(node_list: NodeList) -> AstNode[Ident]:
    """Get the unqualified name

    Args:
        node_list (NodeList): List of Ident AST nodes

    Returns:
        AstNode[Ident]: Unqualified Ident AST node
    """
    return split(node_list)[1]


##########################
### Definitions
##########################


@dataclass
class DefAbsType:
    """Abstract type definition
    """
    name: Ident


@dataclass
class DefAliasType:
    """Aliased type definition
    """
    name: Ident
    type_name: AstNode["TypeName"]


@dataclass
class DefArray:
    """Array definition
    """
    name: Ident
    size: AstNode["Expr"]
    elt_type: AstNode["TypeName"]
    default: Optional[AstNode["Expr"]]
    format: Optional[AstNode[str]]


@dataclass
class DefComponent:
    """Component definition
    """
    kind: ComponentKind
    name: Ident
    members: List["ComponentMember"]


@dataclass
class DefComponentInstance:
    """Component instance definition
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
    """Constant definition
    """
    name: Ident
    value: AstNode["Expr"]


@dataclass
class DefEnum:
    """Enum definition
    """
    name: Ident
    type_name: Optional[AstNode["TypeName"]]
    constants: List[Annotated[AstNode["DefEnumConstant"]]]
    default: Optional[AstNode["Expr"]]


@dataclass
class DefEnumConstant:
    """Enum constant definition
    """
    name: Ident
    value: Optional[AstNode["Expr"]]


@dataclass
class DefModule:
    """Module definition
    """
    name: Ident
    members: List["ModuleMember"]


@dataclass
class DefPort:
    """Port definition
    """
    name: Ident
    params: FormalParamList
    return_type: Optional[AstNode["TypeName"]]


@dataclass
class DefStateMachine:
    """State machine definition
    """
    name: Ident
    members: Optional[List["StateMachineMember"]]


@dataclass
class DefAction:
    """Action definition
    """
    name: Ident
    type_name: Optional[AstNode["TypeName"]]


@dataclass
class DefChoice:
    """Choice definition 
    """
    name: Ident
    guard: AstNode[Ident]
    if_transition: AstNode["TransitionExpr"]
    else_transition: AstNode["TransitionExpr"]


@dataclass
class DefGuard:
    """Guard definition
    """
    name: Ident
    type_name: Optional[AstNode["TypeName"]]


@dataclass
class DefSignal:
    """Signal definition
    """
    name: Ident
    type_name: Optional[AstNode["TypeName"]]


@dataclass
class DefState:
    """State definition
    """
    name: Ident
    members: List["StateMember"]


@dataclass
class DefInterface:
    """Interface definition
    """
    name: Ident
    members: List["InterfaceMember"]


@dataclass
class DefStruct:
    """Struct definition
    """
    name: Ident
    members: List[Annotated[AstNode["StructTypeMember"]]]
    default: Optional[AstNode["Expr"]]


@dataclass
class DefTopology:
    """Topology defintion
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
    """Component member with annotated component member node
    """
    node: Annotated[ComponentMemberNode]


@dataclass
class ComponentMemberDefAbsType(ComponentMemberNode):
    """Abstract type component member
    """
    node: AstNode[DefAbsType]


@dataclass
class ComponentMemberDefAliasType(ComponentMemberNode):
    """Alias type component member
    """
    node: AstNode[DefAliasType]


@dataclass
class ComponentMemberDefArray(ComponentMemberNode):
    """Array component member
    """
    node: AstNode[DefArray]


@dataclass
class ComponentMemberDefConstant(ComponentMemberNode):
    """Constant component member
    """
    node: AstNode[DefConstant]


@dataclass
class ComponentMemberDefEnum(ComponentMemberNode):
    """Enum component member
    """
    node: AstNode[DefEnum]


@dataclass
class ComponentMemberDefStateMachine(ComponentMemberNode):
    """State machine component member
    """
    node: AstNode[DefStateMachine]


@dataclass
class ComponentMemberDefStruct(ComponentMemberNode):
    """Struct component member
    """
    node: AstNode[DefStruct]


@dataclass
class ComponentMemberSpecCommand(ComponentMemberNode):
    """Command component member
    """
    node: AstNode["SpecCommand"]


@dataclass
class ComponentMemberSpecContainer(ComponentMemberNode):
    """Container component member
    """
    node: AstNode["SpecContainer"]


@dataclass
class ComponentMemberSpecEvent(ComponentMemberNode):
    """Event component member
    """
    node: AstNode["SpecEvent"]


@dataclass
class ComponentMemberSpecInclude(ComponentMemberNode):
    """Include specifier component member
    """
    node: AstNode["SpecInclude"]


@dataclass
class ComponentMemberSpecInternalPort(ComponentMemberNode):
    """Internal port specifier component member
    """
    node: AstNode["SpecInternalPort"]


@dataclass
class ComponentMemberSpecParam(ComponentMemberNode):
    """Param component member
    """
    node: AstNode["SpecParam"]


@dataclass
class ComponentMemberSpecPortInstance(ComponentMemberNode):
    """Port instance component member
    """
    node: AstNode["SpecPortInstance"]


@dataclass
class ComponentMemberSpecPortMatching(ComponentMemberNode):
    """Port matching component member
    """
    node: AstNode["SpecPortMatching"]


@dataclass
class ComponentMemberSpecRecord(ComponentMemberNode):
    """Record component member
    """
    node: AstNode["SpecRecord"]


@dataclass
class ComponentMemberSpecStateMachineInstance(ComponentMemberNode):
    """State machine instance component member
    """
    node: AstNode["SpecStateMachineInstance"]


@dataclass
class ComponentMemberSpecTlmChannel(ComponentMemberNode):
    """Telemetry channel component member
    """
    node: AstNode["SpecTlmChannel"]


@dataclass
class ComponentMemberSpecImportInterface(ComponentMemberNode):
    """Import specifier component member
    """
    node: AstNode["SpecImport"]


##########################
### Module Member
##########################


class ModuleMemberNode(ABC):
    pass


@dataclass
class ModuleMember:
    """Module member with annotated module member node
    """
    node: Annotated[ModuleMemberNode]


@dataclass
class ModuleMemberDefAbsType(ModuleMemberNode):
    """Abstract type module member
    """
    node: AstNode[DefAbsType]


@dataclass
class ModuleMemberDefAliasType(ModuleMemberNode):
    """Alias type module member
    """
    node: AstNode[DefAliasType]


@dataclass
class ModuleMemberDefArray(ModuleMemberNode):
    """Array module member
    """
    node: AstNode[DefArray]


@dataclass
class ModuleMemberDefComponent(ModuleMemberNode):
    """Component module member
    """
    node: AstNode[DefComponent]


@dataclass
class ModuleMemberDefComponentInstance(ModuleMemberNode):
    """Component instance module member
    """
    node: AstNode[DefComponentInstance]


@dataclass
class ModuleMemberDefConstant(ModuleMemberNode):
    """Constant module member
    """
    node: AstNode[DefConstant]


@dataclass
class ModuleMemberDefEnum(ModuleMemberNode):
    """Enum module member
    """
    node: AstNode[DefEnum]


@dataclass
class ModuleMemberDefInterface(ModuleMemberNode):
    """Interface module member
    """
    node: AstNode["DefInterface"]


@dataclass
class ModuleMemberDefModule(ModuleMemberNode):
    """Module module member
    """
    node: AstNode[DefModule]


@dataclass
class ModuleMemberDefPort(ModuleMemberNode):
    """Port module member
    """
    node: AstNode["DefPort"]


@dataclass
class ModuleMemberDefStateMachine(ModuleMemberNode):
    """State machine module member
    """
    node: AstNode["DefStateMachine"]


@dataclass
class ModuleMemberDefStruct(ModuleMemberNode):
    """Struct module member
    """
    node: AstNode["DefStruct"]


@dataclass
class ModuleMemberDefTopology(ModuleMemberNode):
    """Topology module member
    """
    node: AstNode["DefTopology"]


@dataclass
class ModuleMemberSpecInclude(ModuleMemberNode):
    """Include specifier module member
    """
    node: AstNode["SpecInclude"]


@dataclass
class ModuleMemberSpecLoc(ModuleMemberNode):
    """Location specifier module member
    """
    node: AstNode["SpecLoc"]


##########################
### State Machine Member
##########################


@dataclass
class StateMachineMember:
    """State machine member with annotated state machine member member node
    """
    node: Annotated["StateMachineMemberNode"]


class StateMachineMemberNode(ABC):
    pass


@dataclass
class StateMachineMemberDefAction(StateMachineMemberNode):
    """Action state machine member
    """
    node: AstNode["DefAction"]


@dataclass
class StateMachineMemberDefChoice(StateMachineMemberNode):
    """Choice state machine member
    """
    node: AstNode["DefChoice"]


@dataclass
class StateMachineMemberDefGuard(StateMachineMemberNode):
    """Guard state machine member
    """
    node: AstNode["DefGuard"]


@dataclass
class StateMachineMemberDefSignal(StateMachineMemberNode):
    """Signal state machine member
    """
    node: AstNode["DefSignal"]


@dataclass
class StateMachineMemberDefState(StateMachineMemberNode):
    """State state machine member
    """
    node: AstNode["DefState"]


@dataclass
class StateMachineMemberSpecInitialTransition(StateMachineMemberNode):
    """Initial state state machine member
    """
    node: AstNode["SpecInitialTransition"]


##########################
### State Member
##########################


@dataclass
class StateMember:
    """State member with annotated state member node
    """
    node: Annotated["StateMemberNode"]


class StateMemberNode(ABC):
    pass


@dataclass
class StateMemberDefChoice(StateMemberNode):
    """Choice state member
    """
    node: AstNode[DefChoice]


@dataclass
class StateMemberDefState(StateMemberNode):
    """State state member
    """
    node: AstNode[DefState]


@dataclass
class StateMemberSpecStateEntry(StateMemberNode):
    """State entry state member
    """
    node: AstNode["SpecStateEntry"]


@dataclass
class StateMemberSpecStateExit(StateMemberNode):
    """State exit state member
    """
    node: AstNode["SpecStateExit"]


@dataclass
class StateMemberSpecInitialTransition(StateMemberNode):
    """Initial state state member
    """
    node: AstNode["SpecInitialTransition"]


@dataclass
class StateMemberSpecStateTransition(StateMemberNode):
    """Transition state member
    """
    node: AstNode["SpecStateTransition"]


##########################
### Expressions
##########################


class Expr(ABC):
    pass


@dataclass
class ExprArray(Expr):
    """Array expression
    """
    elts: List[AstNode[Expr]]


@dataclass
class ExprBinop(Expr):
    """Binary operation expression
    """
    e1: AstNode[Expr]
    op: "Binop"
    e2: AstNode[Expr]


@dataclass
class ExprDot(Expr):
    """Dot expression
    """
    e: AstNode[Expr]
    id: AstNode[Ident]


@dataclass
class ExprIdent(Expr):
    """Ident expression
    """
    value: Ident


@dataclass
class ExprLiteralBool(Expr):
    """Literal Boolean expression
    """
    value: "LiteralBool"


@dataclass
class ExprLiteralInt(Expr):
    """Literal integer expression
    """
    value: str


@dataclass
class ExprLiteralFloat(Expr):
    """Literal float expression
    """
    value: str


@dataclass
class ExprLiteralString(Expr):
    """Literal string expression
    """
    value: str


@dataclass
class ExprParen(Expr):
    """Parenthesis expression
    """
    e: AstNode[Expr]


@dataclass
class ExprStruct(Expr):
    """Struct expression
    """
    members: List[AstNode["StructMember"]]


@dataclass
class ExprUnop(Expr):
    """Unary operation expression
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
    """Topology member with anotated topology member node
    """
    node: Annotated[TopologyMemberNode]


@dataclass
class TopologyMemberSpecCompInstance(TopologyMemberNode):
    """Component instance topology member
    """
    node: AstNode["SpecCompInstance"]


@dataclass
class TopologyMemberSpecConnectionGraph(TopologyMemberNode):
    """Connection graph topology member
    """
    node: AstNode["SpecConnectionGraph"]


@dataclass
class TopologyMemberSpecInclude(TopologyMemberNode):
    """Include specifier topology member
    """
    node: AstNode["SpecInclude"]


@dataclass
class TopologyMemberSpecTlmPacketSet(TopologyMemberNode):
    """Telemetry packet set topology member
    """
    node: AstNode["SpecTlmPacketSet"]


@dataclass
class TopologyMemberSpecTopImport(TopologyMemberNode):
    """Topology import topology member
    """
    node: AstNode["SpecImport"]


#################################
### Telemetry Packet Set Member
#################################


class TlmPacketSetMemberNode(ABC):
    pass


@dataclass
class TlmPacketSetMember:
    node: Annotated[TlmPacketSetMemberNode]


@dataclass
class TlmPacketSetMemberSpecInclude(TlmPacketSetMemberNode):
    node: AstNode["SpecInclude"]


@dataclass
class TlmPacketSetMemberSpecTlmPacket(TlmPacketSetMemberNode):
    node: AstNode["SpecTlmPacket"]


############################
### Interface Member
############################


@dataclass
class InterfaceMember:
    node: Annotated["InterfaceMemberNode"]


class InterfaceMemberNode(ABC):
    pass


@dataclass
class InterfaceMemberSpecPortInstance(InterfaceMemberNode):
    node: AstNode["SpecPortInstance"]


@dataclass
class InterfaceMemberSpecImportInterface(InterfaceMemberNode):
    node: AstNode["SpecImport"]


###############################
### Telemetry Packet Member
###############################


class TlmPacketMember(ABC):
    pass


@dataclass
class TlmPacketMemberSpecInclude(TlmPacketMember):
    node: AstNode["SpecInclude"]


@dataclass
class TlmPacketMemberTlmChannelIdentifier(TlmPacketMember):
    node: AstNode["TlmChannelIdentifier"]


##########################
### Specifiers
##########################


class QueueFull(Enum):
    ASSERT = "assert"
    BLOCK = "block"
    DROP = "drop"
    HOOK = "hook"

    def __str__(self):
        return self.value


@dataclass
class SpecCommand:
    kind: "SpecCommandKind"
    name: Ident
    params: FormalParamList
    opcode: Optional[AstNode[Expr]]
    priority: Optional[AstNode[Expr]]
    queue_full: Optional[AstNode[QueueFull]]


class SpecCommandKind(Enum):
    ASYNC = "async"
    GUARDED = "guarded"
    SYNC = "sync"

    def __str__(self):
        return self.value


@dataclass
class SpecCompInstance:
    visibility: "Visibility"
    instance: AstNode[QualIdent]


class SpecConnectionGraph(ABC):
    pass


@dataclass
class Direct(SpecConnectionGraph):
    name: Ident
    connections: List["Connection"]


class PatternKind(Enum):
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
    kind: PatternKind
    source: AstNode[QualIdent]
    targets: List[AstNode[QualIdent]]


@dataclass
class Connection:
    is_unmatched: bool
    from_port: AstNode["PortInstanceIdentifier"]
    from_index: Optional[AstNode[Expr]]
    to_port: AstNode["PortInstanceIdentifier"]
    to_index: Optional[AstNode[Expr]]


@dataclass
class SpecContainer:
    name: Ident
    id: Optional[AstNode[Expr]]
    default_priority: Optional[AstNode[Expr]]


@dataclass
class SpecEvent:
    name: Ident
    params: FormalParamList
    severity: "SpecEventSeverity"
    id: Optional[AstNode[Expr]]
    format: AstNode[str]
    throttle: Optional[AstNode[Expr]]


class SpecEventSeverity(Enum):
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
    file: AstNode[str]


@dataclass
class SpecInit:
    phase: AstNode[Expr]
    code: str


@dataclass
class SpecInternalPort:
    name: Ident
    params: FormalParamList
    priority: Optional[AstNode[Expr]]
    queue_full: Optional[QueueFull]


@dataclass
class SpecLoc:
    kind: "SpecLocKind"
    symbol: AstNode[QualIdent]
    file: AstNode[str]


class SpecLocKind(Enum):
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
    kind: "GeneralKind"
    name: Ident
    size: Optional[AstNode[Expr]]
    port: Optional[AstNode[QualIdent]]
    priority: Optional[AstNode[Expr]]
    queue_full: Optional[AstNode[QueueFull]]


@dataclass
class SpecialPortInstance(SpecPortInstance):
    input_kind: Optional["SpecialInputKind"]
    kind: "SpecialKind"
    name: Ident
    priority: Optional[AstNode[Expr]]
    queue_full: Optional[AstNode[QueueFull]]


class GeneralKind(Enum):
    ASYNC_INPUT = "async input"
    GUARDED_INPUT = "guarded input"
    OUTPUT = "output"
    SYNC_INPUT = "sync input"

    def __str__(self):
        return self.value


class SpecialInputKind(Enum):
    ASYNC = "async"
    GUARDED = "guarded"
    SYNC = "sync"

    def __str__(self):
        return self.value


class SpecialKind(Enum):
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
    port1: AstNode[Ident]
    port2: AstNode[Ident]


@dataclass
class SpecRecord:
    name: Ident
    record_type: AstNode["TypeName"]
    is_array: bool
    id: Optional[AstNode[Expr]]


@dataclass
class SpecStateMachineInstance:
    name: Ident
    state_machine: AstNode[QualIdent]
    priority: Optional[AstNode[Expr]]
    queue_full: Optional[QueueFull]


@dataclass
class SpecTlmChannel:
    name: Ident
    type_name: AstNode["TypeName"]
    id: Optional[AstNode[Expr]]
    update: Optional["SpecTlmChannelUpdate"]
    format: Optional[AstNode[str]]
    low: List["Limit"]
    high: List["Limit"]


class SpecTlmChannelUpdate(Enum):
    ALWAYS = "always"
    ON_CHANGE = "on change"

    def __str__(self):
        return self.value


@dataclass
class SpecTlmPacket:
    name: Ident
    id: Optional[AstNode[Expr]]
    group: AstNode[Expr]
    members: List["TlmPacketMember"]


@dataclass
class SpecTlmPacketSet:
    name: Ident
    members: List["TlmPacketSetMember"]
    omitted: List[AstNode["TlmChannelIdentifier"]]


@dataclass
class SpecImport:
    sym: AstNode[QualIdent]


@dataclass
class SpecInitialTransition:
    transition: AstNode["TransitionExpr"]


@dataclass
class SpecStateEntry:
    actions: List[AstNode[Ident]]


@dataclass
class SpecStateExit:
    actions: List[AstNode[Ident]]


@dataclass
class SpecStateTransition:
    signal: AstNode[Ident]
    guard: Optional[AstNode[Ident]]
    transition_or_do: "TransitionOrDo"


Limit: TypeAlias = Tuple[AstNode["LimitKind"], AstNode[Expr]]


class LimitKind(Enum):
    RED = "red"
    ORANGE = "orange"
    YELLOW = "yellow"

    def __str__(self):
        return self.value


class TypeFloat(Enum):
    F32 = "F32"
    F64 = "F64"

    def __str__(self):
        return self.value


class TypeInt(Enum):
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
    name: TypeFloat


@dataclass
class TypeNameInt(TypeName):
    name: TypeInt


@dataclass
class TypeNameQualIdent(TypeName):
    name: AstNode[QualIdent]


@dataclass
class TypeNameBool(TypeName):
    pass


@dataclass
class TypeNameString(TypeName):
    size: Optional[AstNode[Expr]]


class Unop(Enum):
    MINUS = "-"

    def __str__(self):
        return self.value


class Visibility(Enum):
    PRIVATE = "private"
    PUBLIC = "public"

    def __str__(self):
        return self.value


@dataclass
class FormalParam:
    kind: "FormalParamKind"
    name: Ident
    type_name: AstNode[TypeName]


class FormalParamKind(Enum):
    REF = "ref"
    VALUE = "value"


class LiteralBool(Enum):
    TRUE = "true"
    FALSE = "false"

    # override __str__ function to return the literal bool string
    def __str__(self):
        return self.value


@dataclass
class PortInstanceIdentifier:
    component_instance: AstNode[QualIdent]
    port_name: AstNode[Ident]


@dataclass
class TransitionExpr:
    actions: List[AstNode[Ident]]
    target: AstNode[QualIdent]


class TransitionOrDo(ABC):
    pass


@dataclass
class Transition(TransitionOrDo):
    transition: AstNode[TransitionExpr]


@dataclass
class Do(TransitionOrDo):
    actions: List[AstNode[Ident]]


@dataclass
class StructMember:
    name: Ident
    value: AstNode[Expr]


@dataclass
class StructTypeMember:
    name: Ident
    size: Optional[AstNode[Expr]]
    type_name: AstNode[TypeName]
    format: Optional[AstNode[str]]


@dataclass
class TlmChannelIdentifier:
    component_instance: AstNode[QualIdent]
    channel_name: AstNode[Ident]
