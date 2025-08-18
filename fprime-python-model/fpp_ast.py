from abc import ABC, abstractmethod
from typing import List, TypeAlias, Optional, Tuple, override, TypeVar
from dataclasses import dataclass
from enum import Enum
from fpp_ast_node import AstNode
from error import InternalError
from fpp_locations import Locations

T = TypeVar('T')
Annotated: TypeAlias = Tuple[List[str], T, List[str]]
Ident: TypeAlias = str
type FormalParamList = List[Annotated[AstNode['FormalParam']]]
TUMember: TypeAlias = 'ModuleMember'

@dataclass
class TransUnit:
    """Translation unit"""
    members: List[TUMember]

class Binop(Enum):
    """Binary operation"""
    ADD = "+"
    DIV = "/"
    MUL = "*"
    SUB = "-"

    def __str__(self):
        return self.value

class ComponentKind(Enum):
    """Component kind"""
    ACTIVE = "active"
    PASSIVE = "passive"
    QUEUED = "queued"

    def __str__(self):
        return self.value

class QualIdent(ABC):
    """A possibly-qualified identifier"""
    @abstractmethod
    def to_ident_list(self) -> List[Ident]:
        """Convert a qualified identifier to a list of identifiers"""
        pass

@dataclass
class Unqualified(QualIdent):
    """An unqualified identifier"""
    name: Ident

    @override
    def to_ident_list(self):
        return [self.name]

@dataclass
class Qualified(QualIdent):
    """A qualified identifier"""
    qualifier: AstNode[QualIdent]
    name: AstNode[Ident]

    @override
    def to_ident_list(self):
        return self.qualifier.data.to_ident_list + [self.name.data]

def qual_ident_from_node_list(node_list: 'NodeList') -> QualIdent:
    """
    Construct a qualified identifier from a node list
    """
    split_node_list = split(node_list)
    if not split_node_list[0] and split_node_list[1]:
        return Unqualified(split_node_list[1].data)
    elif split_node_list[0] and split_node_list[1]:
        qualifier_1 = qual_ident_from_node_list(split_node_list[0])
        node = AstNode.create(qualifier_1, name(split_node_list[0])._id)
        Qualified(node, split_node_list[1])

NodeList: TypeAlias = List[AstNode[Ident]]
"""
A qualified identifier represented as a list of identifier nodes
This is useful during parsing
"""

def split(node_list: NodeList) -> Tuple[List[AstNode[Ident]], AstNode[Ident]]:
    """
    Split a qualified identifier list into qualifier and name
    """
    rev: List[NodeList] = node_list.reverse()
    if not rev:
        raise InternalError("node list should not be empty")
    else:
        return rev[1:].reverse(), rev[0]
    
def qualifier(node_list: NodeList) -> List[AstNode[Ident]]:
    """Get the qualifier"""
    split(node_list)[0]

def name(node_list: NodeList) -> AstNode[Ident]:
    """Get the unqualified name"""
    split(node_list)[1]
    

def node_from_node_list(node_list: NodeList) -> AstNode[QualIdent]:
    """Create a QualIdent node from a node list"""
    qual_id = qual_ident_from_node_list(node_list)
    node = AstNode.create(qual_id)
    loc = Locations.get(node_list[0]._id)
    Locations.put(node._id, loc)
    return node

##########################
### Definitions
##########################

@dataclass
class DefAbsType:
    name: Ident

@dataclass
class DefAliasType:
    name: Ident
    type_name: AstNode['TypeName']

@dataclass
class DefArray:
    name: Ident
    size: AstNode['Expr']
    elt_type: AstNode['TypeName']
    default: Optional[AstNode['Expr']]
    format: Optional[AstNode[str]]

@dataclass
class DefComponent:
    kind: ComponentKind
    name: Ident
    members: List['ComponentMember']

@dataclass
class DefComponentInstance:
    name: Ident
    component: AstNode[QualIdent]
    base_id: AstNode['Expr']
    impl_type: Optional[AstNode[str]]
    file: Optional[AstNode[str]]
    queue_size: Optional[AstNode['Expr']]
    stack_size: Optional[AstNode['Expr']]
    priority: Optional[AstNode['Expr']]
    cpu: Optional[AstNode['Expr']]
    init_specs: List[Annotated[AstNode['SpecInit']]]

@dataclass
class DefConstant:
    name: Ident
    value: AstNode['Expr']

@dataclass
class DefEnum:
    name: Ident
    type_name: Optional[AstNode['TypeName']]
    constants: List[Annotated[AstNode['DefEnumConstant']]]

@dataclass
class DefEnumConstant:
    name: Ident
    value: Optional[AstNode['Expr']]

@dataclass
class DefModule:
    name: Ident
    members: List['ModuleMember']

@dataclass
class DefPort:
    name: Ident
    params: FormalParamList
    return_type: Optional[AstNode['TypeName']]

@dataclass
class DefStateMachine:
    name: Ident
    members: Optional[List['StateMachineMember']]

@dataclass
class DefAction:
    name: Ident
    type_name: Optional[AstNode['TypeName']]

@dataclass
class DefChoice:
    name: Ident
    guard: AstNode[Ident]
    if_transition: AstNode['TransitionExpr']
    else_transition: AstNode['TransitionExpr']

@dataclass
class DefGuard:
    name: Ident
    type_name: Optional[AstNode['TypeName']]

@dataclass
class DefSignal:
    name: Ident
    type_name: Optional[AstNode['TypeName']]

@dataclass
class DefState:
    name: Ident
    members: List['StateMember']

@dataclass
class DefInterface:
    name: Ident
    members: List['InterfaceMember']

@dataclass
class DefStruct:
    name: Ident
    members: List[Annotated[AstNode['StructTypeMember']]]
    default: Optional['InterfaceMember']

@dataclass
class DefTopology:
    name: Ident
    members: List['TopologyMember']

##########################
### Component Member
##########################

class ComponentMemberNode(ABC):
    pass

@dataclass
class ComponentMember:
    node: Annotated[ComponentMemberNode]

@dataclass
class ComponentMemberDefAbsType(ComponentMemberNode):
    node: AstNode['DefAbsType']

@dataclass
class ComponentMemberDefAliasType(ComponentMemberNode):
    node: AstNode['DefAliasType']

@dataclass
class ComponentMemberDefArray(ComponentMemberNode):
    node: AstNode['DefArray']

@dataclass
class ComponentMemberDefConstant(ComponentMemberNode):
    node: AstNode['DefConstant']

@dataclass
class ComponentMemberDefEnum(ComponentMemberNode):
    node: AstNode['DefEnum']

##########################
### Module Member
##########################

class ModuleMemberNode(ABC):
    pass

@dataclass
class ModuleMember:
    node: Annotated[ModuleMemberNode]

@dataclass
class ModuleMemberDefAbsType(ModuleMemberNode):
    node: AstNode[DefAbsType]

@dataclass
class ModuleMemberDefAliasType(ModuleMemberNode):
    node: AstNode[DefAliasType]

@dataclass
class ModuleMemberDefArray(ModuleMemberNode):
    node: AstNode[DefArray]

@dataclass
class ModuleMemberDefComponent(ModuleMemberNode):
    node: AstNode[DefComponent]

@dataclass
class ModuleMemberDefComponentInstance(ModuleMemberNode):
    node: AstNode[DefComponentInstance]

@dataclass
class ModuleMemberDefConstant(ModuleMemberNode):
    node: AstNode[DefConstant]

@dataclass
class ModuleMemberDefEnum(ModuleMemberNode):
    node: AstNode[DefEnum]

@dataclass
class ModuleMemberDefInterface(ModuleMemberNode):
    node: AstNode['DefInterface']

@dataclass
class ModuleMemberDefModule(ModuleMemberNode):
    node: AstNode[DefModule]

@dataclass
class ModuleMemberDefPort(ModuleMemberNode):
    node: AstNode['DefPort']

@dataclass
class ModuleMemberDefStateMachine(ModuleMemberNode):
    node: AstNode['DefStateMachine']

@dataclass
class ModuleMemberDefStruct(ModuleMemberNode):
    node: AstNode['DefStruct']

@dataclass
class ModuleMemberDefTopology(ModuleMemberNode):
    node: AstNode['DefTopology']

@dataclass
class ModuleMemberSpecInclude(ModuleMemberNode):
    node: AstNode['SpecInclude']

@dataclass
class ModuleMemberSpecLoc(ModuleMemberNode):
    node: AstNode['SpecLoc']

##########################
### State Machine Member
##########################

@dataclass
class StateMachineMember:
    node: Annotated['StateMachineMemberNode']

class StateMachineMemberNode(ABC):
    pass

@dataclass
class StateMachineMemberDefAction(StateMachineMemberNode):
    node: AstNode['DefAction']

@dataclass
class StateMachineMemberDefChoice(StateMachineMemberNode):
    node: AstNode['DefChoice']

@dataclass
class StateMachineMemberDefGuard(StateMachineMemberNode):
    node: AstNode['DefGuard']

@dataclass
class StateMachineMemberDefSignal(StateMachineMemberNode):
    node: AstNode['DefSignal']

@dataclass
class StateMachineMemberDefState(StateMachineMemberNode):
    node: AstNode['DefState']

@dataclass
class StateMachineMemberDefSpecInitialTransition(StateMachineMemberNode):
    node: AstNode['SpecInitialTransition']

##########################
### State Member
##########################

@dataclass
class StateMember:
    node: Annotated['StateMemberNode']

class StateMemberNode(ABC):
    pass

@dataclass
class StateMemberDefChoice(StateMemberNode):
    node: AstNode[DefChoice]

@dataclass
class StateMemberDefState(StateMemberNode):
    node: AstNode[DefState]

@dataclass
class StateMemberSpecStateEntry(StateMemberNode):
    node: AstNode['SpecStateEntry']

@dataclass
class StateMemberSpecStateExit(StateMemberNode):
    node: AstNode['SpecStateExit']

@dataclass
class StateMemberSpecInitialTransition(StateMemberNode):
    node: AstNode['SpecInitialTransition']

@dataclass
class StateMemberSpecStateTransition(StateMemberNode):
    node: AstNode['SpecStateTransition']

##########################
### Expressions
##########################

class Expr(ABC):
    pass

@dataclass
class ExprArray(Expr):
    elts: List[AstNode[Expr]]

@dataclass
class ExprBinop(Expr):
    e1: AstNode[Expr]
    op: 'Binop'
    e2: AstNode[Expr]

@dataclass
class ExprDot(Expr):
    e: AstNode[Expr]
    id: AstNode[Ident]

@dataclass
class ExprIdent(Expr):
    value: Ident

@dataclass
class ExprLiteralBool(Expr):
    value: 'LiteralBool'

@dataclass
class ExprLiteralInt(Expr):
    value: str

@dataclass
class ExprLiteralFloat(Expr):
    value: str

@dataclass
class ExprLiteralString(Expr):
    value: str

@dataclass
class ExprParen(Expr):
    e: AstNode[Expr]

@dataclass
class ExprStruct(Expr):
    members: List[AstNode['StructMember']]

@dataclass
class ExprUnop(Expr):
    op: 'Unop'
    e: AstNode[Expr]

##########################
### Topology Member
##########################

class TopologyMemberNode(ABC):
    pass

@dataclass
class TopologyMember:
    node: Annotated[TopologyMemberNode]

@dataclass
class TopologyMemberSpecCompInstance(TopologyMemberNode):
    node: AstNode['SpecCompInstance']

@dataclass
class TopologyMemberSpecConnectionGraph(TopologyMemberNode):
    node: AstNode['SpecConnectionGraph']

@dataclass
class TopologyMemberSpecInclude(TopologyMemberNode):
    node: AstNode['SpecInclude']

@dataclass
class TopologyMemberSpecTlmPacketSet(TopologyMemberNode):
    node: AstNode['SpecTlmPacketSet']

@dataclass
class TopologyMemberSpecTopImport(TopologyMemberNode):
    node: AstNode['SpecImport']

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
    node: AstNode['SpecInclude']

@dataclass
class TlmPacketSetMemberSpecTlmPacket(TlmPacketSetMemberNode):
    node: AstNode['SpecTlmPacket']

############################
### Interface Member
############################

@dataclass
class InterfaceMember:
    node: Annotated['InterfaceMemberNode']

class InterfaceMemberNode(ABC):
    pass

@dataclass
class InterfaceMemberSpecPortInstance(InterfaceMemberNode):
    node: AstNode['SpecPortInstance']

@dataclass
class InterfaceMemberSpecImportInterface(InterfaceMemberNode):
    node: AstNode['SpecImport']

###############################
### Telemetry Packet Member
###############################

class TlmPacketMember(ABC):
    pass

@dataclass
class TlmPacketMemberSpecInclude(TlmPacketMember):
    node: AstNode['SpecInclude']

@dataclass
class TlmPacketMemberTlmChannelIdentifier(TlmPacketMember):
    node: AstNode['TlmChannelIdentifier']


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
    kind: 'SpecCommandKind'
    name: Ident
    params: FormalParamList
    opcode: Optional[AstNode[Expr]]
    priority: Optional[AstNode[Expr]]
    queueFull: Optional[AstNode[QueueFull]]
    
class SpecCommandKind(Enum):
    ASYNC = "async"
    GUARDED = "guarded"
    SYNC = "sync"

    def __str__(self):
        return self.value

@dataclass
class SpecCompInstance:
    visibility: 'Visibility'
    instance: AstNode[QualIdent]

class SpecConnectionGraph(ABC):
    pass

@dataclass
class Direct(SpecConnectionGraph):
    name: Ident
    connections: List['Connection']

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
    isUnmatch: bool
    fromPort: AstNode['PortInstanceIdentifier']
    fromIndex: Optional[AstNode[Expr]]
    toPort: AstNode['PortInstanceIdentifier']
    toIndex: Optional[AstNode[Expr]]

@dataclass
class SpecContainer:
    name: Ident
    id: Optional[AstNode[Expr]]
    default_priority: Optional[AstNode[Expr]]

@dataclass
class SpecEvent:
    name: Ident
    params: FormalParamList
    severity: 'SpecEventSeverity'

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
    kind: 'SpecLocKind'
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
    type_name: AstNode['TypeName']
    default: Optional[AstNode[Expr]]
    id: Optional[AstNode[Expr]]
    set_opcode: Optional[AstNode[Expr]]
    save_opcode: Optional[AstNode[Expr]]
    is_external: bool

class SpecPortInstance(ABC):
    pass

@dataclass
class General(SpecPortInstance):
    kind: 'GeneralKind'
    name: Ident
    size: Optional[AstNode[Expr]]
    port: Optional[AstNode[QualIdent]]
    priority: Optional[AstNode[Expr]]
    queue_full: Optional[AstNode[QueueFull]]

@dataclass
class Special(SpecPortInstance):
    input_kind: Optional['SpecialInputKind']
    kind: 'SpecialKind'
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
    record_type: AstNode['TypeName']
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
    type_name: AstNode['TypeName']
    id: Optional[AstNode[Expr]]
    update: Optional['SpecTlmChannelUpdate']
    format: Optional[AstNode[str]]
    low: List['Limit']
    high: List['Limit']

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
    members: List['TlmPacketMember']

@dataclass
class SpecTlmPacketSet:
    name: Ident
    members: List['TlmPacketSetMember']
    omitted: List[AstNode['TlmChannelIdentifier']]

@dataclass
class SpecImport:
    sym: AstNode[QualIdent]

@dataclass
class SpecInitialTransition:
    transition: AstNode['TransitionExpr']

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
    transition_or_do: 'TransitionOrDo'

Limit: TypeAlias = Tuple[AstNode['LimitKind'], AstNode[Expr]]

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
    kind: 'FormalParamKind'
    name: Ident
    typeName: AstNode[TypeName]

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
