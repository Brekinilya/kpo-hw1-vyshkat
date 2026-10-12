from dataclasses import dataclass

from vyshkat.domain.errors import DuplicateInventoryNumberError
from vyshkat.domain.interfaces import IEnergyConsumer, IInventory
from vyshkat.domain.service_center import InspectionResult, IServiceCenter
from vyshkat.domain.things import Thing
from vyshkat.domain.vehicles import Vehicle


@dataclass(frozen=True)
class FleetReport:
    vehicle_count: int
    thing_count: int
    daily_energy_kwh: float

    @property
    def total_count(self) -> int:
        return self.vehicle_count + self.thing_count


class Park:
    def __init__(self, service_center: IServiceCenter) -> None:
        self._service_center = service_center
        self._vehicles: list[Vehicle] = []
        self._things: list[Thing] = []

    @property
    def vehicles(self) -> tuple[Vehicle, ...]:
        return tuple(self._vehicles)

    @property
    def things(self) -> tuple[Thing, ...]:
        return tuple(self._things)

    def inventory(self) -> tuple[IInventory, ...]:
        items: list[IInventory] = [*self._vehicles, *self._things]
        return tuple(sorted(items, key=lambda item: item.inventory_number))

    def admit_vehicle(self, vehicle: Vehicle) -> InspectionResult:
        self._ensure_number_is_free(vehicle)
        result = self._service_center.inspect(vehicle)
        if result.approved:
            self._vehicles.append(vehicle)
        return result

    def register_thing(self, thing: Thing) -> None:
        self._ensure_number_is_free(thing)
        self._things.append(thing)

    def beginner_friendly_vehicles(self) -> tuple[Vehicle, ...]:
        return tuple(vehicle for vehicle in self._vehicles if vehicle.is_suitable_for_beginners())

    def daily_energy_kwh(self) -> float:
        return sum(
            item.daily_energy_kwh for item in self.inventory() if isinstance(item, IEnergyConsumer)
        )

    def report(self) -> FleetReport:
        return FleetReport(
            vehicle_count=len(self._vehicles),
            thing_count=len(self._things),
            daily_energy_kwh=self.daily_energy_kwh(),
        )

    def _ensure_number_is_free(self, candidate: IInventory) -> None:
        if any(item.inventory_number == candidate.inventory_number for item in self.inventory()):
            raise DuplicateInventoryNumberError(candidate.inventory_number)
