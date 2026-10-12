import inspect
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from vyshkat.application.catalog import Catalog
from vyshkat.domain.errors import DomainError, DuplicateInventoryNumberError
from vyshkat.domain.interfaces import IInventory
from vyshkat.domain.inventory import InventoryItem
from vyshkat.domain.park import Park


@dataclass(frozen=True)
class IntakeOutcome:
    accepted: bool
    reason: str
    item: IInventory | None = None


class Intake:
    def __init__(self, park: Park, catalog: Catalog) -> None:
        self._park = park
        self._catalog = catalog

    def receive_vehicle(self, kind: str, fields: Mapping[str, Any]) -> IntakeOutcome:
        vehicle_type = self._catalog.vehicles.get(kind)
        if vehicle_type is None:
            return IntakeOutcome(accepted=False, reason=f"неизвестный вид техники «{kind}»")
        try:
            vehicle = _build(vehicle_type, fields)
        except DomainError as error:
            return IntakeOutcome(accepted=False, reason=str(error))
        try:
            inspection = self._park.admit_vehicle(vehicle)
        except DuplicateInventoryNumberError as error:
            return IntakeOutcome(accepted=False, reason=str(error), item=vehicle)
        return IntakeOutcome(accepted=inspection.approved, reason=inspection.reason, item=vehicle)

    def receive_thing(self, kind: str, fields: Mapping[str, Any]) -> IntakeOutcome:
        thing_type = self._catalog.things.get(kind)
        if thing_type is None:
            return IntakeOutcome(accepted=False, reason=f"неизвестный вид вещи «{kind}»")
        try:
            thing = _build(thing_type, fields)
        except DomainError as error:
            return IntakeOutcome(accepted=False, reason=str(error))
        try:
            self._park.register_thing(thing)
        except DuplicateInventoryNumberError as error:
            return IntakeOutcome(accepted=False, reason=str(error), item=thing)
        return IntakeOutcome(accepted=True, reason="поставлено на баланс", item=thing)


def _build[T: InventoryItem](item_type: type[T], fields: Mapping[str, Any]) -> T:
    parameters = inspect.signature(item_type).parameters
    missing = [
        name
        for name, parameter in parameters.items()
        if parameter.default is parameter.empty and name not in fields
    ]
    unexpected = [name for name in fields if name not in parameters]
    problems = []
    if missing:
        problems.append(f"не хватает полей: {', '.join(missing)}")
    if unexpected:
        problems.append(f"лишние поля: {', '.join(unexpected)}")
    if problems:
        raise DomainError(f"вид «{item_type.kind}» — {'; '.join(problems)}")
    return item_type(**fields)
