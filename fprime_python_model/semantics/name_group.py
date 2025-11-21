from enum import Enum
from typing import List


class NameGroup(Enum):
    COMPONENT_INSTANCE = "component instance"
    COMPONENT = "component"
    PORT = "port"
    STATE_MACHINE = "state machine"
    TOPOLOGY = "topology"
    INTERFACE = "interface"
    TYPE = "type"
    VALUE = "constant"

    def __str__(self):
        return self.value


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
