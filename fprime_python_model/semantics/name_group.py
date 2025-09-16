from enum import Enum
from typing import List


class NameGroup(Enum):
    COMPONENT_INSTANCE = "ComponentInstance"
    COMPONENT = "Component"
    PORT = "Port"
    STATE_MACHINE = "StateMachine"
    TOPOLOGY = "Topology"
    INTERFACE = "Interface"
    TYPE = "Type"
    VALUE = "Value"


name_groups: List[NameGroup] = [
    NameGroup.COMPONENT_INSTANCE,
    NameGroup.COMPONENT,
    NameGroup.PORT,
    NameGroup.STATE_MACHINE,
    NameGroup.TOPOLOGY,
    NameGroup.INTERFACE,
    NameGroup.TYPE,
    NameGroup.VALUE,
]
