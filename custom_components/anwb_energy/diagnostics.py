from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    coordinators = hass.data.get(DOMAIN, {}).get(entry.entry_id, {})
    result: dict[str, Any] = {}
    for resource, coordinator in coordinators.items():
        data = coordinator.data or {}
        result[resource] = {
            "has_data": coordinator.data is not None,
            "hour_count": len(data.get("hourly", {})),
            "current": data.get("current"),
            "next": data.get("next"),
            "market_price_min": data.get("market_price_min"),
            "market_price_max": data.get("market_price_max"),
            "market_price_avg": data.get("market_price_avg"),
            "all_in_price_min": data.get("all_in_price_min"),
            "all_in_price_max": data.get("all_in_price_max"),
            "all_in_price_avg": data.get("all_in_price_avg"),
        }
    return result
