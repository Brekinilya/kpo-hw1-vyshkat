from vyshkat.domain.interfaces import IEnergyConsumer
from vyshkat.domain.inventory import InventoryItem
from vyshkat.domain.validation import require_non_negative_number


class Thing(InventoryItem):
    pass


class PoweredThing(Thing, IEnergyConsumer):
    def __init__(self, name: str, inventory_number: int, daily_energy_kwh: float) -> None:
        super().__init__(name, inventory_number)
        self._daily_energy_kwh = require_non_negative_number(
            daily_energy_kwh, "Суточный расход энергии, кВт·ч"
        )

    @property
    def daily_energy_kwh(self) -> float:
        return self._daily_energy_kwh


class Helmet(Thing):
    kind = "Шлем"


class DockStation(PoweredThing):
    kind = "Док-станция"


class ChargingCabinet(PoweredThing):
    kind = "Зарядный шкаф"
