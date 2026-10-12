from unittest.mock import create_autospec

import pytest

from tests.support import FakeServiceCenter, make_bicycle, make_scooter
from vyshkat.domain.errors import DuplicateInventoryNumberError
from vyshkat.domain.park import Park
from vyshkat.domain.service_center import InspectionResult, IServiceCenter
from vyshkat.domain.things import ChargingCabinet, DockStation, Helmet
from vyshkat.domain.vehicles import ElectricBike


def test_vehicle_approved_by_service_center_joins_park():
    center = FakeServiceCenter(approve=True)
    park = Park(center)
    scooter = make_scooter()

    result = park.admit_vehicle(scooter)

    assert result.approved
    assert park.vehicles == (scooter,)
    assert center.inspected == [scooter]


def test_vehicle_rejected_by_service_center_stays_out():
    park = Park(FakeServiceCenter(approve=False))

    result = park.admit_vehicle(make_scooter())

    assert not result.approved
    assert park.vehicles == ()


def test_park_follows_service_center_decision():
    center = create_autospec(IServiceCenter, instance=True)
    center.inspect.return_value = InspectionResult(approved=False, reason="тормоза неисправны")
    park = Park(center)
    scooter = make_scooter()

    result = park.admit_vehicle(scooter)

    center.inspect.assert_called_once_with(scooter)
    assert result.reason == "тормоза неисправны"
    assert park.vehicles == ()


def test_duplicate_number_is_refused_before_inspection():
    center = FakeServiceCenter()
    park = Park(center)
    park.admit_vehicle(make_scooter(number=101))

    with pytest.raises(DuplicateInventoryNumberError):
        park.admit_vehicle(make_bicycle(number=101))
    assert len(center.inspected) == 1


def test_inventory_numbers_are_unique_across_vehicles_and_things():
    park = Park(FakeServiceCenter())
    park.register_thing(Helmet("Шлем M", 501))

    with pytest.raises(DuplicateInventoryNumberError):
        park.admit_vehicle(make_scooter(number=501))
    with pytest.raises(DuplicateInventoryNumberError):
        park.register_thing(Helmet("Шлем L", 501))


def test_things_are_registered_without_inspection():
    center = FakeServiceCenter(approve=False)
    park = Park(center)
    helmet = Helmet("Шлем", 501)

    park.register_thing(helmet)

    assert park.things == (helmet,)
    assert center.inspected == []


def test_daily_energy_sums_only_energy_consumers():
    park = Park(FakeServiceCenter())
    park.admit_vehicle(make_scooter(number=101, energy=0.5))
    park.admit_vehicle(ElectricBike("Электровел", 301, 6, 20, 0.75))
    park.admit_vehicle(make_bicycle(number=201))
    park.register_thing(Helmet("Шлем", 501))
    park.register_thing(DockStation("Док-станция", 601, 1.2))
    park.register_thing(ChargingCabinet("Шкаф", 701, 3.5))

    assert park.daily_energy_kwh() == pytest.approx(5.95)


def test_report_counts_units_and_energy():
    park = Park(FakeServiceCenter())
    park.admit_vehicle(make_scooter(number=101, energy=0.5))
    park.admit_vehicle(make_bicycle(number=201))
    park.register_thing(DockStation("Док-станция", 601, 1.5))

    report = park.report()

    assert (report.vehicle_count, report.thing_count, report.total_count) == (2, 1, 3)
    assert report.daily_energy_kwh == pytest.approx(2.0)


def test_empty_park_report():
    report = Park(FakeServiceCenter()).report()

    assert report.total_count == 0
    assert report.daily_energy_kwh == 0


def test_beginner_list_contains_only_simple_vehicles():
    park = Park(FakeServiceCenter())
    simple_scooter = make_scooter(number=1, simplicity=6)
    hard_scooter = make_scooter(number=2, simplicity=5)
    bicycle = make_bicycle(number=3, simplicity=9)
    for vehicle in (simple_scooter, hard_scooter, bicycle):
        park.admit_vehicle(vehicle)

    assert park.beginner_friendly_vehicles() == (simple_scooter, bicycle)


def test_inventory_lists_vehicles_and_things_by_number():
    park = Park(FakeServiceCenter())
    helmet = Helmet("Шлем", 5)
    scooter = make_scooter(number=7)
    bicycle = make_bicycle(number=1)
    park.register_thing(helmet)
    park.admit_vehicle(scooter)
    park.admit_vehicle(bicycle)

    assert park.inventory() == (bicycle, helmet, scooter)
