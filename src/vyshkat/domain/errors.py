class DomainError(ValueError):
    pass


class DuplicateInventoryNumberError(DomainError):
    def __init__(self, inventory_number: int) -> None:
        super().__init__(f"инвентарный номер {inventory_number} уже занят")
        self.inventory_number = inventory_number
