from datetime import datetime

import pytest
from homeassistant.util import dt as dt_util

from custom_components.anwb_energy.services import _parse_boundary


def test_parse_boundary_accepts_local_date() -> None:
    result = _parse_boundary("2026-09-24", dt_util.now())

    assert result.date().isoformat() == "2026-09-24"
    assert result.hour == 0
    assert result.minute == 0


def test_parse_boundary_preserves_timezone_for_timestamp() -> None:
    default = datetime.fromisoformat("2026-09-24T00:00:00+02:00")

    result = _parse_boundary("2026-09-24T14:30:00+02:00", default)

    assert result.timestamp() == default.replace(hour=14, minute=30).timestamp()


def test_parse_boundary_rejects_invalid_value() -> None:
    with pytest.raises(Exception):
        _parse_boundary("not-a-date", dt_util.now())