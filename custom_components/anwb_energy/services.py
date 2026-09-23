from __future__ import annotations

from datetime import datetime, time

import voluptuous as vol

from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse
from homeassistant.exceptions import ServiceValidationError
from homeassistant.util import dt as dt_util

from .const import DOMAIN, RESOURCE_ELECTRICITY, RESOURCE_GAS

SERVICE_GET_PRICES = "get_prices"
ATTR_RESOURCE = "resource"
ATTR_PRICE_TYPE = "price_type"
ATTR_START = "start"
ATTR_END = "end"

SERVICE_SCHEMA = vol.Schema(
    {
        vol.Optional(ATTR_RESOURCE, default=RESOURCE_ELECTRICITY): vol.Any(
            None,
            vol.In([RESOURCE_ELECTRICITY, RESOURCE_GAS]),
        ),
        vol.Optional(ATTR_PRICE_TYPE, default="market"): vol.In(
            ["market", "all_in"]
        ),
        vol.Optional(ATTR_START): str,
        vol.Optional(ATTR_END): str,
    }
)


def _parse_boundary(value: str | None, default: datetime) -> datetime:
    if value is None:
        return default
    parsed = dt_util.parse_datetime(value)
    if parsed is None:
        parsed_date = dt_util.parse_date(value)
        if parsed_date is None:
            raise ServiceValidationError(f"Invalid date: {value}")
        local_midnight = datetime.combine(
            parsed_date,
            time.min,
            tzinfo=dt_util.get_default_time_zone(),
        )
        return local_midnight
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=dt_util.get_default_time_zone())
    return dt_util.as_local(parsed)


async def _async_get_prices(call: ServiceCall) -> dict:
    entries = call.hass.data.get(DOMAIN, {})
    if not entries:
        raise ServiceValidationError("ANWB Energy is not configured")

    coordinators = next(iter(entries.values()))
    resource = call.data.get(ATTR_RESOURCE)
    if resource is None:
        available_resources = [
            resource_name
            for resource_name, coordinator in coordinators.items()
            if coordinator.data is not None
        ]
        if len(available_resources) != 1:
            raise ServiceValidationError(
                "Specify resource as electricity or gas when both are configured"
            )
        resource = available_resources[0]

    coordinator = coordinators.get(resource)
    if coordinator is None or coordinator.data is None:
        raise ServiceValidationError(f"No data available for {resource}")

    now = dt_util.now()
    start = _parse_boundary(call.data.get(ATTR_START), dt_util.start_of_local_day(now))
    end = _parse_boundary(call.data.get(ATTR_END), start.replace(hour=23, minute=59, second=59))
    if end <= start:
        raise ServiceValidationError("The end must be after the start")

    price_key = "market_price" if call.data[ATTR_PRICE_TYPE] == "market" else "all_in_price"
    prices = []
    for timestamp, values in coordinator.data["hourly"].items():
        timestamp_dt = dt_util.parse_datetime(timestamp)
        if timestamp_dt is None or not start <= timestamp_dt < end:
            continue
        prices.append(
            {
                "timestamp": timestamp,
                "price": values[price_key],
                "market_price": values["market_price"],
                "all_in_price": values["all_in_price"],
            }
        )

    return {"prices": prices}


def async_setup_services(hass: HomeAssistant) -> None:
    hass.services.async_register(
        DOMAIN,
        SERVICE_GET_PRICES,
        _async_get_prices,
        schema=SERVICE_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
