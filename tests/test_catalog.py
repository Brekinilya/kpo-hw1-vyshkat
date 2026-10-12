from typing import Any

import pytest

from vyshkat.application.catalog import DEFAULT_CATALOG, Catalog
from vyshkat.domain.things import Helmet
from vyshkat.domain.vehicles import Bicycle


def test_catalog_cannot_be_changed_after_creation():
    vehicles: Any = DEFAULT_CATALOG.vehicles

    with pytest.raises(TypeError):
        vehicles["tank"] = Bicycle


def test_catalog_does_not_follow_changes_of_source_dict():
    source = {"helmet": Helmet}
    catalog = Catalog(vehicles={}, things=source)

    source.clear()

    assert dict(catalog.things) == {"helmet": Helmet}
