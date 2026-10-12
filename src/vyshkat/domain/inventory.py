from typing import ClassVar

from vyshkat.domain.interfaces import IInventory
from vyshkat.domain.validation import require_name, require_positive_int


class InventoryItem(IInventory):
    kind: ClassVar[str]

    def __init__(self, name: str, inventory_number: int) -> None:
        self._name = require_name(name)
        self._inventory_number = require_positive_int(inventory_number, "Инвентарный номер")

    @property
    def name(self) -> str:
        return self._name

    @property
    def inventory_number(self) -> int:
        return self._inventory_number
