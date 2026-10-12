from vyshkat.domain.interfaces import IEnergyConsumer
from vyshkat.domain.inventory import InventoryItem
from vyshkat.domain.validation import require_int_in_range, require_non_negative_number

BEGINNER_MIN_SIMPLICITY = 6


class Vehicle(InventoryItem):
    def __init__(
        self, name: str, inventory_number: int, simplicity: int, wear_percent: int
    ) -> None:
        super().__init__(name, inventory_number)
        self._simplicity = require_int_in_range(simplicity, "Простота для новичка", 1, 10)
        self._wear_percent = require_int_in_range(wear_percent, "Износ, %", 0, 100)

    @property
    def simplicity(self) -> int:
        return self._simplicity

    @property
    def wear_percent(self) -> int:
        return self._wear_percent

    def is_suitable_for_beginners(self) -> bool:
        return self._simplicity >= BEGINNER_MIN_SIMPLICITY


class ElectricVehicle(Vehicle, IEnergyConsumer):
    def __init__(
        self,
        name: str,
        inventory_number: int,
        simplicity: int,
        wear_percent: int,
        daily_energy_kwh: float,
    ) -> None:
        super().__init__(name, inventory_number, simplicity, wear_percent)
        self._daily_energy_kwh = require_non_negative_number(
            daily_energy_kwh, "Суточный расход энергии, кВт·ч"
        )

    @property
    def daily_energy_kwh(self) -> float:
        return self._daily_energy_kwh


class Bicycle(Vehicle):
    kind = "Велосипед"


class Scooter(ElectricVehicle):
    kind = "Электросамокат"


class ElectricBike(ElectricVehicle):
    kind = "Электровелосипед"
