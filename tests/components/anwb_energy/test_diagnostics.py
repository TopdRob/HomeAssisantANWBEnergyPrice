from types import SimpleNamespace

from homeassistant.config_entries import ConfigEntry

from custom_components.anwb_energy.const import DOMAIN
from custom_components.anwb_energy.diagnostics import (
    async_get_config_entry_diagnostics,
)


async def test_config_entry_diagnostics_returns_non_sensitive_summary(hass) -> None:
    entry = ConfigEntry(
        version=1,
        minor_version=1,
        domain=DOMAIN,
        title="ANWB Energy",
        data={"electricity": True},
        source="user",
        entry_id="anwb-energy-diagnostics-test",
        options={},
    )
    hass.data[DOMAIN] = {
        entry.entry_id: {
            "electricity": SimpleNamespace(
                data={
                    "hourly": {"2026-09-24T10:00:00+00:00": {"market_price": 10}},
                    "current": {"market_price": 10},
                    "next": {"market_price": 11},
                    "market_price_min": 10,
                    "market_price_max": 11,
                    "market_price_avg": 10.5,
                    "all_in_price_min": 15,
                    "all_in_price_max": 16,
                    "all_in_price_avg": 15.5,
                }
            )
        }
    }

    result = await async_get_config_entry_diagnostics(hass, entry)

    assert result["electricity"]["has_data"] is True
    assert result["electricity"]["hour_count"] == 1
    assert result["electricity"]["market_price_min"] == 10
    assert "hourly" not in result["electricity"]
    assert "api_url" not in result["electricity"]