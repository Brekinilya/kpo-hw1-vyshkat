import json

import pytest

from tests.support import FakeServiceCenter
from vyshkat.application.catalog import DEFAULT_CATALOG
from vyshkat.application.intake import Intake
from vyshkat.domain.park import Park
from vyshkat.ui.console import ConsoleApp
from vyshkat.ui.delivery_file import DeliveryFileLoader

ADD_LITE_SCOOTER = ("1", "1", "ВышКат Lite", "101", "8", "10", "0,45")
ADD_HARD_SCOOTER = ("1", "1", "ВышКат Pro", "102", "5", "20", "0.6")
ADD_BICYCLE = ("1", "2", "Городской", "201", "9", "10")
ADD_HELMET = ("2", "1", "Шлем M", "501")
ADD_DOCK = ("2", "2", "Док-станция", "601", "1.2")


class ScriptedConsole:
    def __init__(self, answers: list[str]) -> None:
        self._answers = iter(answers)
        self.lines: list[str] = []

    def read(self, prompt: str) -> str:
        self.lines.append(prompt)
        try:
            return next(self._answers)
        except StopIteration:
            raise EOFError from None

    def write(self, text: str) -> None:
        self.lines.append(text)

    @property
    def output(self) -> str:
        return "\n".join(self.lines)


def run_app(*steps: tuple[str, ...], approve: bool = True) -> tuple[str, Park]:
    park = Park(FakeServiceCenter(approve))
    intake = Intake(park, DEFAULT_CATALOG)
    console = ScriptedConsole([answer for step in steps for answer in step] + ["0"])
    app = ConsoleApp(
        park, intake, DeliveryFileLoader(intake), DEFAULT_CATALOG, console.read, console.write
    )
    app.run()
    return console.output, park


def test_scooter_is_admitted_through_menu():
    output, park = run_app(ADD_LITE_SCOOTER)

    assert "[принято] Электросамокат «ВышКат Lite» №101" in output
    assert park.daily_energy_kwh() == pytest.approx(0.45)


def test_bicycle_is_not_asked_for_energy():
    output, park = run_app(ADD_BICYCLE)

    assert "Суточный расход энергии" not in output
    assert len(park.vehicles) == 1


def test_inspection_rejection_is_shown():
    output, park = run_app(ADD_LITE_SCOOTER, approve=False)

    assert "[отказ]" in output
    assert park.vehicles == ()


def test_invalid_value_is_shown_without_crash():
    output, park = run_app(("1", "2", "Городской", "201", "11", "10"))

    assert "[отказ] Простота для новичка: ожидается целое число от 1 до 10" in output
    assert park.vehicles == ()


def test_number_prompts_repeat_until_valid():
    output, park = run_app(("1", "1", "Самокат", "abc", "101", "8", "10", "много", "0.5"))

    assert "Введите целое число." in output
    assert "Введите число, например 0.5." in output
    assert len(park.vehicles) == 1


def test_things_are_registered_and_powered_ones_ask_for_energy():
    output, park = run_app(ADD_HELMET, ADD_DOCK)

    assert "[принято] Шлем «Шлем M» №501 — поставлено на баланс" in output
    assert [thing.kind for thing in park.things] == ["Шлем", "Док-станция"]
    assert park.daily_energy_kwh() == pytest.approx(1.2)


def test_duplicate_number_is_reported():
    output, park = run_app(ADD_HELMET, ("1", "2", "Велосипед", "501", "9", "10"))

    assert "номер 501 уже занят" in output
    assert park.vehicles == ()


def test_unknown_menu_item_and_kind():
    output, _ = run_app(("9",), ("1", "7"), ("2", "x"))

    assert "Нет такого пункта меню." in output
    assert output.count("Нет такого вида.") == 2


def test_report_shows_units_and_energy():
    output, _ = run_app(ADD_LITE_SCOOTER, ADD_DOCK, ("4",))

    assert "Техника на балансе: 1 ед." in output
    assert "Вещи на балансе: 1 ед." in output
    assert "Всего: 2 ед." in output
    assert "1.65 кВт·ч" in output


def test_beginner_list_shows_only_simple_vehicles():
    output, _ = run_app(("5",), ADD_LITE_SCOOTER, ADD_HARD_SCOOTER, ("5",))

    assert "Техники для новичков пока нет." in output
    beginners = output.rsplit("Простота", 1)[1]
    assert "ВышКат Lite" in beginners
    assert "ВышКат Pro" not in beginners


def test_inventory_lists_vehicles_and_things_by_number():
    output, _ = run_app(("6",), ADD_HELMET, ADD_BICYCLE, ("6",))

    assert "На балансе пока ничего нет." in output
    table = output.split("Инвентарная ведомость: 2 ед.\n", 1)[1].splitlines()[:3]
    assert table == [
        "№    Вид        Наименование",
        "201  Велосипед  Городской",
        "501  Шлем       Шлем M",
    ]


def test_delivery_is_loaded_from_file(tmp_path):
    path = tmp_path / "delivery.json"
    path.write_text(
        json.dumps(
            {
                "vehicles": [{"type": "bicycle", "name": "Велосипед"}],
                "things": [{"type": "helmet", "name": "Шлем", "inventory_number": 501}],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    output, park = run_app(("3", f'"{path}"'))

    assert "vehicles, запись 1: [отказ] вид «Велосипед» — не хватает полей:" in output
    assert "things, запись 1: [принято] Шлем «Шлем» №501" in output
    assert "Принято 1 из 2." in output
    assert len(park.things) == 1


def test_delivery_file_errors_are_shown(tmp_path):
    output, _ = run_app(("3", str(tmp_path / "absent.json")))

    assert "Ошибка: файл не найден" in output


def test_end_of_input_finishes_session():
    park = Park(FakeServiceCenter())
    intake = Intake(park, DEFAULT_CATALOG)
    console = ScriptedConsole(["1", "1"])
    app = ConsoleApp(
        park, intake, DeliveryFileLoader(intake), DEFAULT_CATALOG, console.read, console.write
    )

    app.run()

    assert console.lines[-1] == "Работа завершена."
