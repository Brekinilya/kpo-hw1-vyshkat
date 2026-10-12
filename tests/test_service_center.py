import pytest

from tests.support import make_bicycle, make_scooter
from vyshkat.domain.errors import DomainError
from vyshkat.domain.service_center import DEFAULT_MAX_WEAR_PERCENT, ServiceCenter


def test_vehicle_at_wear_limit_passes_inspection():
    result = ServiceCenter(max_wear_percent=40).inspect(make_scooter(wear=40))

    assert result.approved


def test_worn_vehicle_is_rejected_with_reason():
    result = ServiceCenter(max_wear_percent=40).inspect(make_scooter(wear=41))

    assert not result.approved
    assert "41%" in result.reason


def test_default_wear_limit():
    center = ServiceCenter()

    assert center.inspect(make_bicycle(wear=DEFAULT_MAX_WEAR_PERCENT)).approved
    assert not center.inspect(make_bicycle(wear=DEFAULT_MAX_WEAR_PERCENT + 1)).approved


@pytest.mark.parametrize("limit", [-1, 101])
def test_wear_limit_must_be_a_percentage(limit):
    with pytest.raises(DomainError):
        ServiceCenter(max_wear_percent=limit)
