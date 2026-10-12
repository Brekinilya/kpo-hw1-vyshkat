from abc import ABC, abstractmethod
from dataclasses import dataclass

from vyshkat.domain.validation import require_int_in_range
from vyshkat.domain.vehicles import Vehicle

DEFAULT_MAX_WEAR_PERCENT = 40


@dataclass(frozen=True)
class InspectionResult:
    approved: bool
    reason: str


class IServiceCenter(ABC):
    @abstractmethod
    def inspect(self, vehicle: Vehicle) -> InspectionResult: ...


class ServiceCenter(IServiceCenter):
    def __init__(self, max_wear_percent: int = DEFAULT_MAX_WEAR_PERCENT) -> None:
        self._max_wear_percent = require_int_in_range(
            max_wear_percent, "Допустимый износ, %", 0, 100
        )

    def inspect(self, vehicle: Vehicle) -> InspectionResult:
        if vehicle.wear_percent > self._max_wear_percent:
            return InspectionResult(
                approved=False,
                reason=f"износ {vehicle.wear_percent}% выше допустимых {self._max_wear_percent}%",
            )
        return InspectionResult(approved=True, reason="техосмотр пройден")
