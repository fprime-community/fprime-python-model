from enum import Enum
from typing import List


class StateMachineNameGroup(Enum):
    ACTION = "action"
    GUARD = "guard"
    SIGNAL = "signal"
    STATE = "state"

    def __str__(self):
        return self.value


name_groups: List[StateMachineNameGroup] = [
    StateMachineNameGroup.ACTION,
    StateMachineNameGroup.GUARD,
    StateMachineNameGroup.SIGNAL,
    StateMachineNameGroup.STATE,
]
