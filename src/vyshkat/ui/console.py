from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any

from vyshkat.application.catalog import Catalog
from vyshkat.application.intake import Intake, IntakeOutcome
from vyshkat.domain.interfaces import IEnergyConsumer, IInventory
from vyshkat.domain.inventory import InventoryItem
from vyshkat.domain.park import Park
from vyshkat.ui.delivery_file import DeliveryFileError, DeliveryFileLoader

Reader = Callable[[str], str]
Writer = Callable[[str], None]


class ConsoleApp:
    def __init__(
        self,
        park: Park,
        intake: Intake,
        loader: DeliveryFileLoader,
        catalog: Catalog,
        read: Reader = input,
        write: Writer = print,
    ) -> None:
        self._park = park
        self._intake = intake
        self._loader = loader
        self._catalog = catalog
        self._read = read
        self._write = write
        self._actions: dict[str, tuple[str, Callable[[], None]]] = {
            "1": ("Принять технику (с техосмотром)", self._admit_vehicle),
            "2": ("Поставить вещь на баланс", self._register_thing),
            "3": ("Загрузить поставку из JSON-файла", self._load_delivery),
            "4": ("Отчёт: число единиц и суточная энергия", self._show_report),
            "5": ("Техника для новичков", self._show_beginner_vehicles),
            "6": ("Инвентарная ведомость", self._show_inventory),
        }

    def run(self) -> None:
        self._write("ВышКат — учёт парка. Доедем до дедлайна!")
        try:
            self._loop()
        except EOFError:
            self._write("")
        self._write("Работа завершена.")

    def _loop(self) -> None:
        while True:
            self._write("")
            for key, (title, _) in self._actions.items():
                self._write(f"{key}. {title}")
            self._write("0. Выход")
            choice = self._read("> ").strip()
            if choice == "0":
                return
            action = self._actions.get(choice)
            if action is None:
                self._write("Нет такого пункта меню.")
            else:
                action[1]()

    def _admit_vehicle(self) -> None:
        chosen = self._choose_kind("Вид техники", self._catalog.vehicles)
        if chosen is None:
            return
        key, vehicle_type = chosen
        fields: dict[str, Any] = {
            "name": self._read("Наименование: "),
            "inventory_number": self._ask_int("Инвентарный номер: "),
            "simplicity": self._ask_int("Простота для новичка (1–10): "),
            "wear_percent": self._ask_int("Износ по итогам осмотра, % (0–100): "),
        }
        if issubclass(vehicle_type, IEnergyConsumer):
            fields["daily_energy_kwh"] = self._ask_float("Суточный расход энергии, кВт·ч: ")
        self._write(_format_outcome(self._intake.receive_vehicle(key, fields)))

    def _register_thing(self) -> None:
        chosen = self._choose_kind("Вид вещи", self._catalog.things)
        if chosen is None:
            return
        key, thing_type = chosen
        fields: dict[str, Any] = {
            "name": self._read("Наименование: "),
            "inventory_number": self._ask_int("Инвентарный номер: "),
        }
        if issubclass(thing_type, IEnergyConsumer):
            fields["daily_energy_kwh"] = self._ask_float("Суточный расход энергии, кВт·ч: ")
        self._write(_format_outcome(self._intake.receive_thing(key, fields)))

    def _load_delivery(self) -> None:
        raw_path = self._read("Путь к JSON-файлу: ").strip().strip('"')
        try:
            lines = self._loader.load(Path(raw_path))
        except DeliveryFileError as error:
            self._write(f"Ошибка: {error}")
            return
        for line in lines:
            self._write(f"{line.source}: {_format_outcome(line.outcome)}")
        accepted = sum(line.outcome.accepted for line in lines)
        self._write(f"Принято {accepted} из {len(lines)}.")

    def _show_report(self) -> None:
        report = self._park.report()
        self._write(f"Техника на балансе: {report.vehicle_count} ед.")
        self._write(f"Вещи на балансе: {report.thing_count} ед.")
        self._write(f"Всего: {report.total_count} ед.")
        self._write(f"Суммарное суточное энергопотребление: {report.daily_energy_kwh:.2f} кВт·ч")

    def _show_beginner_vehicles(self) -> None:
        vehicles = self._park.beginner_friendly_vehicles()
        if not vehicles:
            self._write("Техники для новичков пока нет.")
            return
        self._write_table(
            ("№", "Вид", "Наименование", "Простота"),
            [
                (str(vehicle.inventory_number), vehicle.kind, vehicle.name, str(vehicle.simplicity))
                for vehicle in vehicles
            ],
        )

    def _show_inventory(self) -> None:
        items = self._park.inventory()
        if not items:
            self._write("На балансе пока ничего нет.")
            return
        self._write(f"Инвентарная ведомость: {len(items)} ед.")
        self._write_table(
            ("№", "Вид", "Наименование"),
            [(str(item.inventory_number), item.kind, item.name) for item in items],
        )

    def _choose_kind[T: InventoryItem](
        self, title: str, options: Mapping[str, type[T]]
    ) -> tuple[str, type[T]] | None:
        keys_by_choice = {str(index): key for index, key in enumerate(options, start=1)}
        self._write(f"{title}:")
        for choice, option in keys_by_choice.items():
            self._write(f"  {choice}. {options[option].kind}")
        key = keys_by_choice.get(self._read("Номер вида: ").strip())
        if key is None:
            self._write("Нет такого вида.")
            return None
        return key, options[key]

    def _ask_int(self, prompt: str) -> int:
        while True:
            try:
                return int(self._read(prompt).strip())
            except ValueError:
                self._write("Введите целое число.")

    def _ask_float(self, prompt: str) -> float:
        while True:
            try:
                return float(self._read(prompt).strip().replace(",", "."))
            except ValueError:
                self._write("Введите число, например 0.5.")

    def _write_table(self, headers: Sequence[str], rows: Sequence[Sequence[str]]) -> None:
        widths = [max(len(cell) for cell in column) for column in zip(headers, *rows, strict=True)]
        for row in (headers, *rows):
            cells = (cell.ljust(width) for cell, width in zip(row, widths, strict=True))
            self._write("  ".join(cells).rstrip())


def _format_outcome(outcome: IntakeOutcome) -> str:
    status = "[принято]" if outcome.accepted else "[отказ]"
    if outcome.item is None:
        return f"{status} {outcome.reason}"
    return f"{status} {_describe(outcome.item)} — {outcome.reason}"


def _describe(item: IInventory) -> str:
    return f"{item.kind} «{item.name}» №{item.inventory_number}"
