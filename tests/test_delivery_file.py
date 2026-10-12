import json
from pathlib import Path

import pytest

from tests.support import FakeServiceCenter
from vyshkat.application.catalog import DEFAULT_CATALOG
from vyshkat.application.intake import Intake
from vyshkat.domain.park import Park
from vyshkat.domain.service_center import ServiceCenter
from vyshkat.ui.delivery_file import DeliveryFileError, DeliveryFileLoader

SAMPLE_DELIVERY = Path(__file__).resolve().parents[1] / "samples" / "delivery.json"


def make_loader(park: Park) -> DeliveryFileLoader:
    return DeliveryFileLoader(Intake(park, DEFAULT_CATALOG))


def write_json(path: Path, content: object) -> Path:
    path.write_text(json.dumps(content, ensure_ascii=False), encoding="utf-8")
    return path


def test_loads_vehicles_and_things(tmp_path):
    park = Park(FakeServiceCenter())
    path = write_json(
        tmp_path / "delivery.json",
        {
            "vehicles": [
                {
                    "type": "bicycle",
                    "name": "Велосипед",
                    "inventory_number": 201,
                    "simplicity": 9,
                    "wear_percent": 5,
                }
            ],
            "things": [{"type": "helmet", "name": "Шлем", "inventory_number": 501}],
        },
    )

    lines = make_loader(park).load(path)

    assert [line.outcome.accepted for line in lines] == [True, True]
    assert park.report().total_count == 2


def test_each_line_points_to_its_record(tmp_path):
    path = write_json(
        tmp_path / "d.json",
        {
            "vehicles": [{"type": "bicycle"}, {"type": "tank"}],
            "things": [{"type": "helmet", "name": "Шлем", "inventory_number": 501}],
        },
    )

    lines = make_loader(Park(FakeServiceCenter())).load(path)

    assert [line.source for line in lines] == [
        "vehicles, запись 1",
        "vehicles, запись 2",
        "things, запись 1",
    ]


def test_sample_delivery_passes_real_inspection():
    park = Park(ServiceCenter())

    lines = make_loader(park).load(SAMPLE_DELIVERY)

    assert len(lines) == 9
    assert sum(line.outcome.accepted for line in lines) == 8
    assert park.daily_energy_kwh() == pytest.approx(6.5)


def test_missing_sections_mean_empty_delivery(tmp_path):
    lines = make_loader(Park(FakeServiceCenter())).load(write_json(tmp_path / "d.json", {}))

    assert lines == []


def test_record_without_type_is_rejected(tmp_path):
    path = write_json(tmp_path / "d.json", {"things": [{"name": "Шлем"}, 42]})

    lines = make_loader(Park(FakeServiceCenter())).load(path)

    assert [line.outcome.accepted for line in lines] == [False, False]


def test_malformed_section_aborts_whole_delivery(tmp_path):
    park = Park(FakeServiceCenter())
    path = write_json(
        tmp_path / "d.json",
        {
            "vehicles": [
                {
                    "type": "bicycle",
                    "name": "Велосипед",
                    "inventory_number": 201,
                    "simplicity": 9,
                    "wear_percent": 5,
                }
            ],
            "things": {"type": "helmet"},
        },
    )

    with pytest.raises(DeliveryFileError, match="things"):
        make_loader(park).load(path)
    assert park.report().total_count == 0


def test_byte_order_mark_is_allowed(tmp_path):
    path = tmp_path / "d.json"
    path.write_text(json.dumps({"vehicles": []}), encoding="utf-8-sig")

    assert make_loader(Park(FakeServiceCenter())).load(path) == []


@pytest.mark.parametrize(
    ("raw", "message"),
    [
        (b"{not json", r"^некорректный JSON: строка 1, позиция 2$"),
        (b"[1, 2]", "JSON-объект"),
        ('{"things": []}'.encode("utf-16"), "UTF-8"),
    ],
)
def test_broken_file_raises_readable_error(tmp_path, raw, message):
    path = tmp_path / "d.json"
    path.write_bytes(raw)

    with pytest.raises(DeliveryFileError, match=message):
        make_loader(Park(FakeServiceCenter())).load(path)


def test_missing_file_raises_readable_error(tmp_path):
    with pytest.raises(DeliveryFileError, match=r"^файл не найден"):
        make_loader(Park(FakeServiceCenter())).load(tmp_path / "absent.json")


def test_directory_instead_of_file_raises_readable_error(tmp_path):
    with pytest.raises(DeliveryFileError, match=r"^не удалось прочитать файл"):
        make_loader(Park(FakeServiceCenter())).load(tmp_path)
