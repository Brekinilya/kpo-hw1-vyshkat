from tests.support import FakeServiceCenter, make_scooter
from vyshkat.container import Container
from vyshkat.ui.console import ConsoleApp


def test_container_wires_real_service_center():
    park = Container().park()

    assert park.admit_vehicle(make_scooter(number=1, wear=10)).approved
    assert not park.admit_vehicle(make_scooter(number=2, wear=90)).approved


def test_service_center_is_replaced_through_container():
    container = Container()
    fake = FakeServiceCenter(approve=False)

    with container.service_center.override(fake):
        park = container.park()
        scooter = make_scooter(wear=0)
        result = park.admit_vehicle(scooter)

    assert not result.approved
    assert fake.inspected == [scooter]


def test_intake_and_park_share_one_instance():
    container = Container()

    container.intake().receive_thing("helmet", {"name": "Шлем", "inventory_number": 501})

    assert [thing.inventory_number for thing in container.park().things] == [501]


def test_container_builds_console():
    assert isinstance(Container().console(), ConsoleApp)
