from vyshkat.domain.service_center import InspectionResult, IServiceCenter
from vyshkat.domain.vehicles import Bicycle, Scooter, Vehicle


class FakeServiceCenter(IServiceCenter):
    def __init__(self, approve: bool = True) -> None:
        self.approve = approve
        self.inspected: list[Vehicle] = []

    def inspect(self, vehicle: Vehicle) -> InspectionResult:
        self.inspected.append(vehicle)
        return InspectionResult(approved=self.approve, reason="решение тестового техосмотра")


def make_scooter(
    number: int = 101, simplicity: int = 7, wear: int = 10, energy: float = 0.5
) -> Scooter:
    return Scooter("Самокат", number, simplicity, wear, energy)


def make_bicycle(number: int = 201, simplicity: int = 9, wear: int = 10) -> Bicycle:
    return Bicycle("Велосипед", number, simplicity, wear)
