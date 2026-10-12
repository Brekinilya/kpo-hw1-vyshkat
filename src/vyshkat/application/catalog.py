from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from vyshkat.domain.things import ChargingCabinet, DockStation, Helmet, Thing
from vyshkat.domain.vehicles import Bicycle, ElectricBike, Scooter, Vehicle


@dataclass(frozen=True)
class Catalog:
    vehicles: Mapping[str, type[Vehicle]]
    things: Mapping[str, type[Thing]]

    def __post_init__(self) -> None:
        object.__setattr__(self, "vehicles", MappingProxyType(dict(self.vehicles)))
        object.__setattr__(self, "things", MappingProxyType(dict(self.things)))


DEFAULT_CATALOG = Catalog(
    vehicles={
        "scooter": Scooter,
        "bicycle": Bicycle,
        "ebike": ElectricBike,
    },
    things={
        "helmet": Helmet,
        "dock": DockStation,
        "cabinet": ChargingCabinet,
    },
)
