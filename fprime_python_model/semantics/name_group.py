from enum import Enum
from typing import List


class NameGroup(Enum):
    PORT_INTERFACE_INSTANCE = "component instance or topology"
    COMPONENT = "component"
    PORT = "port"
    STATE_MACHINE = "state machine"
    TOPOLOGY = "topology"
    PORT_INTERFACE = "interface"
    TYPE = "type"
    VALUE = "constant"

    def __str__(self):
        return self.value


name_groups: List[NameGroup] = [
    NameGroup.COMPONENT,
    NameGroup.PORT,
    NameGroup.STATE_MACHINE,
    NameGroup.PORT_INTERFACE_INSTANCE,
    NameGroup.PORT_INTERFACE,
    NameGroup.TYPE,
    NameGroup.VALUE,
]
