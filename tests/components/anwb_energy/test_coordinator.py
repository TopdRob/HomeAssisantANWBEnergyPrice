from datetime import datetime

from homeassistant.util import dt as dt_util

from custom_components.anwb_energy.coordinator import ANWBEnergyCoordinator


def test_parse_calculates_statistics_and_extreme_hours() -> None:
    coordinator = ANWBEnergyCoordinator.__new__(ANWBEnergyCoordinator)
    now = dt_util.parse_datetime("2026-09-24T10:30:00+02:00")
    assert now is not None

    result = coordinator._parse(
        {
            "data": [
                {
                    "date": "2026-09-24T08:00:00+02:00",
                    "values": {"marktprijs": 20, "allInPrijs": 25},
                },
                {
                    "date": "2026-09-24T09:00:00+02:00",
                    "values": {"marktprijs": 10, "allInPrijs": 15},
                },
                {
                    "date": "2026-09-24T10:00:00+02:00",
                    "values": {"marktprijs": 30, "allInPrijs": 35},
                },
            ]
        },
        now,
    )

    assert result["market_price_min"] == 10
    assert result["market_price_max"] == 30
    assert result["all_in_price_min"] == 15
    assert result["all_in_price_max"] == 35
    assert dt_util.parse_datetime(
        result["market_price_cheapest_hour"]["time"]
    ).hour == 7
    assert dt_util.parse_datetime(
        result["all_in_price_most_expensive_hour"]["time"]
    ).hour == 8


def test_parse_uses_api_statistics_when_available() -> None:
    coordinator = ANWBEnergyCoordinator.__new__(ANWBEnergyCoordinator)
    now = datetime.fromisoformat("2026-09-24T10:30:00+02:00")

    result = coordinator._parse(
        {
            "data": [
                {
                    "date": "2026-09-24T10:00:00+02:00",
                    "values": {"marktprijs": 20, "allInPrijs": 25},
                }
            ],
            "statistics": {
                "min": {"marktprijs": 19, "allInPrijs": 24},
                "max": {"marktprijs": 21, "allInPrijs": 26},
                "average": {"marktprijs": 20, "allInPrijs": 25},
            },
        },
        now,
    )

    assert result["market_price_min"] == 19
    assert result["market_price_max"] == 21
    assert result["market_price_avg"] == 20
    assert result["all_in_price_min"] == 24
    assert result["all_in_price_max"] == 26
    assert result["all_in_price_avg"] == 25