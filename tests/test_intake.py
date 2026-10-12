import pytest

from tests.support import FakeServiceCenter
from vyshkat.application.catalog import DEFAULT_CATALOG, Catalog
from vyshkat.application.intake import Intake
from vyshkat.domain.park import Park
from vyshkat.domain.things import DockStation
from vyshkat.domain.vehicles import ElectricVehicle, Scooter

SCOOTER_FIELDS = {
    "name": "ВышКат Lite",
    "inventory_number": 101,
    "simplicity": 8,
    "wear_percent": 10,
    "daily_energy_kwh": 0.45,
}


@pytest.fixture
def park():
    return Park(FakeServiceCenter())


def test_vehicle_is_created_by_catalog_key(park):
    outcome = Intake(park, DEFAULT_CATALOG).receive_vehicle("scooter", SCOOTER_FIELDS)

    assert outcome.accepted
    assert isinstance(outcome.item, Scooter)
    assert park.vehicles == (outcome.item,)


def test_unknown_vehicle_kind_is_rejected(park):
    outcome = Intake(park, DEFAULT_CATALOG).receive_vehicle("tank", SCOOTER_FIELDS)

    assert not outcome.accepted
    assert "tank" in outcome.reason
    assert outcome.item is None


def test_extra_field_is_named(park):
    outcome = Intake(park, DEFAULT_CATALOG).receive_vehicle("bicycle", SCOOTER_FIELDS)

    assert not outcome.accepted
    assert outcome.reason == "вид «Велосипед» — лишние поля: daily_energy_kwh"
    assert park.vehicles == ()


def test_misspelled_field_is_reported_as_missing_and_extra(park):
    fields = {key: value for key, value in SCOOTER_FIELDS.items() if key != "simplicity"}
    fields["simplicty"] = 8

    outcome = Intake(park, DEFAULT_CATALOG).receive_vehicle("scooter", fields)

    assert outcome.reason == (
        "вид «Электросамокат» — не хватает полей: simplicity; лишние поля: simplicty"
    )


def test_bug_inside_constructor_is_not_hidden_as_user_error(park):
    class BrokenScooter(Scooter):
        def __init__(self, name, inventory_number, simplicity, wear_percent, daily_energy_kwh):
            raise TypeError("ошибка программиста")

    catalog = Catalog(vehicles={"broken": BrokenScooter}, things={})

    with pytest.raises(TypeError, match="ошибка программиста"):
        Intake(park, catalog).receive_vehicle("broken", SCOOTER_FIELDS)


def test_invalid_value_is_explained(park):
    fields = SCOOTER_FIELDS | {"simplicity": 11}

    outcome = Intake(park, DEFAULT_CATALOG).receive_vehicle("scooter", fields)

    assert not outcome.accepted
    assert "Простота" in outcome.reason


def test_inspection_rejection_is_reported_with_item():
    park = Park(FakeServiceCenter(approve=False))

    outcome = Intake(park, DEFAULT_CATALOG).receive_vehicle("scooter", SCOOTER_FIELDS)

    assert not outcome.accepted
    assert outcome.reason == "решение тестового техосмотра"
    assert isinstance(outcome.item, Scooter)
    assert park.vehicles == ()


def test_duplicate_vehicle_number_is_reported(park):
    intake = Intake(park, DEFAULT_CATALOG)
    intake.receive_vehicle("scooter", SCOOTER_FIELDS)

    outcome = intake.receive_vehicle("scooter", SCOOTER_FIELDS)

    assert not outcome.accepted
    assert "101" in outcome.reason
    assert len(park.vehicles) == 1


def test_thing_is_registered_by_catalog_key(park):
    fields = {"name": "Док-станция", "inventory_number": 601, "daily_energy_kwh": 1.2}

    outcome = Intake(park, DEFAULT_CATALOG).receive_thing("dock", fields)

    assert outcome.accepted
    assert isinstance(outcome.item, DockStation)
    assert park.things == (outcome.item,)


def test_unknown_thing_kind_is_rejected(park):
    outcome = Intake(park, DEFAULT_CATALOG).receive_thing("sofa", {})

    assert not outcome.accepted
    assert park.things == ()


def test_invalid_and_duplicate_things_are_reported(park):
    intake = Intake(park, DEFAULT_CATALOG)
    intake.receive_thing("helmet", {"name": "Шлем", "inventory_number": 501})

    invalid = intake.receive_thing("helmet", {"name": "", "inventory_number": 502})
    duplicate = intake.receive_thing("helmet", {"name": "Шлем L", "inventory_number": 501})

    assert not invalid.accepted
    assert not duplicate.accepted
    assert len(park.things) == 1


def test_new_vehicle_kind_needs_only_a_class_and_a_catalog_entry(park):
    class Segway(ElectricVehicle):
        kind = "Сегвей"

    catalog = Catalog(
        vehicles={**DEFAULT_CATALOG.vehicles, "segway": Segway},
        things=DEFAULT_CATALOG.things,
    )
    fields = SCOOTER_FIELDS | {"daily_energy_kwh": 0.3}

    outcome = Intake(park, catalog).receive_vehicle("segway", fields)

    assert outcome.accepted
    assert park.daily_energy_kwh() == pytest.approx(0.3)
