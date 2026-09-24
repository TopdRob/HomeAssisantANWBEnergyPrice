"""Provide ANWB Energie system health information."""

from typing import Any

from homeassistant.components import system_health
from homeassistant.core import HomeAssistant, callback

from .const import DOMAIN


@callback
def async_register(
    hass: HomeAssistant, register: system_health.SystemHealthRegistration
) -> None:
    """Register system health callbacks."""
    register.async_register_info(system_health_info)


async def system_health_info(hass: HomeAssistant) -> dict[str, Any]:
    """Return non-sensitive integration status information."""
    entries = hass.data.get(DOMAIN, {})
    coordinators = next(iter(entries.values()), {})

    return {
        "configured_resources": ", ".join(sorted(coordinators)) or "none",
        "resources_with_data": ", ".join(
            sorted(
                resource
                for resource, coordinator in coordinators.items()
                if coordinator.data
            )
        )
        or "none",
        "hour_count": sum(
            len((coordinator.data or {}).get("hourly", {}))
            for coordinator in coordinators.values()
        ),
        "last_update_success": (
            all(coordinator.last_update_success for coordinator in coordinators.values())
            if coordinators
            else False
        ),
    }
