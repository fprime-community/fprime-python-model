from enum import Enum
from typing import List


class StateMachineNameGroup(Enum):
    ACTION = "Action"
    GUARD = "Guard"
    SIGNAL = "Signal"
    STATE = "State"


name_groups: List[StateMachineNameGroup] = [
    StateMachineNameGroup.ACTION,
    StateMachineNameGroup.GUARD,
    StateMachineNameGroup.SIGNAL,
    StateMachineNameGroup.STATE,
]
