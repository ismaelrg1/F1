from typing import Protocol


class PowerupRepository(Protocol):
    def list_powerups(self):
        ...
