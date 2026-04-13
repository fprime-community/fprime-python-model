from typing import Optional
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Location:
    file: Path
    pos: str
    including_loc: Optional["Location"]

    def __hash__(self):
        return hash((self.path, self.pos, self.including_loc))

    def __str__(self):
        includes_str = ""
        if self.including_loc:
            includes_str = (
                f"\nincluded at {self.including_loc.path}:{self.including_loc.pos}"
            )
        return f"{self.path}:{self.pos}{includes_str}"
