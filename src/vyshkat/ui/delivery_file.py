import json
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from vyshkat.application.intake import Intake, IntakeOutcome

Receiver = Callable[[str, Mapping[str, Any]], IntakeOutcome]


class DeliveryFileError(Exception):
    pass


@dataclass(frozen=True)
class DeliveryLine:
    source: str
    outcome: IntakeOutcome


class DeliveryFileLoader:
    def __init__(self, intake: Intake) -> None:
        self._intake = intake

    def load(self, path: Path) -> list[DeliveryLine]:
        data = _read_json_object(path)
        vehicles = _section(data, "vehicles")
        things = _section(data, "things")
        return [
            *_receive_all("vehicles", vehicles, self._intake.receive_vehicle),
            *_receive_all("things", things, self._intake.receive_thing),
        ]


def _read_json_object(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except FileNotFoundError as error:
        raise DeliveryFileError(f"файл не найден: {path}") from error
    except OSError as error:
        raise DeliveryFileError(f"не удалось прочитать файл: {path}") from error
    except UnicodeDecodeError as error:
        raise DeliveryFileError("файл должен быть в кодировке UTF-8") from error
    except json.JSONDecodeError as error:
        raise DeliveryFileError(
            f"некорректный JSON: строка {error.lineno}, позиция {error.colno}"
        ) from error
    if not isinstance(data, dict):
        raise DeliveryFileError("ожидается JSON-объект с разделами vehicles и things")
    return data


def _section(data: Mapping[str, Any], key: str) -> list[Any]:
    records = data.get(key, [])
    if not isinstance(records, list):
        raise DeliveryFileError(f"раздел {key} должен быть списком")
    return records


def _receive_all(section: str, records: Sequence[Any], receive: Receiver) -> list[DeliveryLine]:
    return [
        DeliveryLine(source=f"{section}, запись {position}", outcome=_receive(record, receive))
        for position, record in enumerate(records, start=1)
    ]


def _receive(record: Any, receive: Receiver) -> IntakeOutcome:
    if not isinstance(record, dict) or not isinstance(record.get("type"), str):
        return IntakeOutcome(accepted=False, reason="запись должна быть объектом с полем type")
    fields = {key: value for key, value in record.items() if key != "type"}
    return receive(record["type"], fields)
