from typing import Optional
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Location:
    path: Path
    pos: str
    includingLoc: Optional[str]

    def __hash__(self):
        return hash((self.path, self.pos, self.includingLoc))
