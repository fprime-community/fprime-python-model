from typing import TypeAlias, List
from dataclasses import dataclass

UnqualifiedName: TypeAlias = str

@dataclass
class QualifiedName:
    qualifier: List[UnqualifiedName]
    base: UnqualifiedName

    def __str__(self):
        return ".".join(self.qualifier + [self.base])

