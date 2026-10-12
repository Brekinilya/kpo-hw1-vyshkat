import pytest

from tests.support import make_bicycle, make_scooter
from vyshkat.domain.errors import DomainError
from vyshkat.domain.interfaces import IEnergyConsumer, IInventory
from vyshkat.domain.inventory import InventoryItem
from vyshkat.domain.things import ChargingCabinet, DockStation, Helmet, PoweredThing, Thing
from vyshkat.domain.vehicles import ElectricBike, ElectricVehicle, Scooter, Vehicle

VALID_SCOOTER = {
    "name": "Самокат",
    "inventory_number": 101,
    "simplicity": 7,
    "wear_percent": 10,
    "daily_energy_kwh": 0.5,
}


def test_electric_transport_consumes_energy():
    scooter = make_scooter(energy=0.45)
    ebike = ElectricBike("Электровел", 301, 6, 20, 0.9)

    assert isinstance(scooter, IEnergyConsumer)
    assert isinstance(ebike, IEnergyConsumer)
    assert scooter.daily_energy_kwh == 0.45
    assert ebike.daily_energy_kwh == 0.9


def test_powered_things_consume_energy():
    dock = DockStation("Док-станция", 601, 1.2)
    cabinet = ChargingCabinet("Шкаф", 701, 3)

    assert isinstance(dock, IEnergyConsumer)
    assert cabinet.daily_energy_kwh == 3.0


def test_bicycle_and_helmet_are_inventoried_but_consume_no_energy():
    for item in (make_bicycle(), Helmet("Шлем", 501)):
        assert isinstance(item, IInventory)
        assert not isinstance(item, IEnergyConsumer)


def test_name_is_trimmed():
    assert Helmet("  Шлем M  ", 501).name == "Шлем M"


def test_kind_is_available_through_inventory_interface():
    items: list[IInventory] = [make_scooter(), make_bicycle(), DockStation("Док", 601, 1)]

    assert [item.kind for item in items] == ["Электросамокат", "Велосипед", "Док-станция"]


@pytest.mark.parametrize(
    ("base", "arguments"),
    [
        (InventoryItem, ("Объект", 1)),
        (Vehicle, ("Транспорт", 1, 7, 10)),
        (ElectricVehicle, ("Электротранспорт", 1, 7, 10, 0.5)),
        (Thing, ("Вещь", 1)),
        (PoweredThing, ("Оборудование", 1, 0.5)),
    ],
)
def test_base_classes_without_kind_cannot_be_instantiated(base, arguments):
    with pytest.raises(TypeError, match="abstract"):
        base(*arguments)


@pytest.mark.parametrize(
    ("simplicity", "expected"),
    [(1, False), (5, False), (6, True), (10, True)],
)
def test_beginner_rule_uses_simplicity_threshold(simplicity, expected):
    assert make_scooter(simplicity=simplicity).is_suitable_for_beginners() is expected


@pytest.mark.parametrize(
    "override",
    [
        {"name": "   "},
        {"inventory_number": 0},
        {"inventory_number": True},
        {"simplicity": 0},
        {"simplicity": 11},
        {"simplicity": "7"},
        {"wear_percent": -1},
        {"wear_percent": 101},
        {"daily_energy_kwh": -0.1},
        {"daily_energy_kwh": float("nan")},
        {"daily_energy_kwh": float("inf")},
    ],
)
def test_vehicle_rejects_invalid_values(override):
    with pytest.raises(DomainError):
        Scooter(**(VALID_SCOOTER | override))


def test_powered_thing_rejects_negative_energy():
    with pytest.raises(DomainError, match="Суточный расход"):
        DockStation("Док-станция", 601, -1)
