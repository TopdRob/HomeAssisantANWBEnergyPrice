from datetime import timedelta, datetime, timezone
import logging

import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, API_INTERVAL

_LOGGER = logging.getLogger(__name__)

HEADERS = {
    "accept": "application/json",
    "accept-language": "nl,en;q=0.9",
    "origin": "https://www.anwb.nl",
    "referer": "https://www.anwb.nl/",
    "user-agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/150.0.0.0 Safari/537.36 Edg/150.0.0.0"
    ),
}
REQUEST_TIMEOUT = aiohttp.ClientTimeout(total=30)


class ANWBEnergyCoordinator(DataUpdateCoordinator):
    def __init__(
        self,
        hass: HomeAssistant,
        api_url: str,
        resource: str,
        config_entry: ConfigEntry,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{resource}",
            update_interval=timedelta(hours=1),
            config_entry=config_entry,
        )
        self._api_url = api_url
        self._resource = resource

    async def _async_update_data(self) -> dict:
        now = datetime.now(timezone.utc)
        # Fetch yesterday 23:00 UTC → today 24:00 UTC (covers full NL local day)
        start = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(hours=1)
        end = start + timedelta(hours=25)

        params = {
            "startDate": start.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
            "endDate": end.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
            "interval": API_INTERVAL,
        }

        try:
            session = async_get_clientsession(self.hass)
            async with session.get(
                self._api_url,
                params=params,
                headers=HEADERS,
                timeout=REQUEST_TIMEOUT,
            ) as response:
                response.raise_for_status()
                raw = await response.json()
        except (aiohttp.ClientError, ValueError) as err:
            raise UpdateFailed(
                f"Error fetching ANWB {self._resource} prices: {err}"
            ) from err

        if not isinstance(raw, dict) or not isinstance(raw.get("data"), list):
            raise UpdateFailed(
                f"Invalid ANWB {self._resource} response: missing data list"
            )

        return self._parse(raw, now)

    def _parse(self, raw: dict, now: datetime) -> dict:
        entries = raw.get("data", [])

        hourly = {}
        for entry in entries:
            dt = datetime.fromisoformat(entry["date"])
            values = entry.get("values", {})
            hourly[dt] = {
                "market_price": values.get("marktprijs"),
                "all_in_price": values.get("allInPrijs"),
            }

        current_hour = now.replace(minute=0, second=0, microsecond=0)
        current = hourly.get(current_hour) or self._closest(hourly, current_hour)

        hourly_attr = {
            dt.isoformat(): vals for dt, vals in sorted(hourly.items())
        }

        market_prices = [
            v["market_price"] for v in hourly.values() if v["market_price"] is not None
        ]
        all_in_prices = [
            v["all_in_price"] for v in hourly.values() if v["all_in_price"] is not None
        ]

        statistics = raw.get("statistics")
        if not isinstance(statistics, dict):
            statistics = {}
        minimum = statistics.get("min", {})
        maximum = statistics.get("max", {})
        average = statistics.get("average", {})

        if not isinstance(minimum, dict):
            minimum = {}
        if not isinstance(maximum, dict):
            maximum = {}
        if not isinstance(average, dict):
            average = {}

        cheapest_market = min(
            hourly.items(),
            key=lambda x: x[1]["market_price"] if x[1]["market_price"] is not None else float("inf"),
            default=None,
        )
        cheapest_all_in = min(
            hourly.items(),
            key=lambda x: x[1]["all_in_price"] if x[1]["all_in_price"] is not None else float("inf"),
            default=None,
        )

        return {
            "current": current,
            "hourly": hourly_attr,
            "market_price_min": minimum.get("marktprijs", min(market_prices, default=None)),
            "market_price_max": maximum.get("marktprijs", max(market_prices, default=None)),
            "market_price_avg": average.get(
                "marktprijs",
                round(sum(market_prices) / len(market_prices), 5) if market_prices else None,
            ),
            "all_in_price_min": minimum.get("allInPrijs", min(all_in_prices, default=None)),
            "all_in_price_max": maximum.get("allInPrijs", max(all_in_prices, default=None)),
            "all_in_price_avg": average.get(
                "allInPrijs",
                round(sum(all_in_prices) / len(all_in_prices), 5) if all_in_prices else None,
            ),
            "market_price_cheapest_hour": {
                "price": cheapest_market[1]["market_price"],
                "time": cheapest_market[0].isoformat(),
            } if cheapest_market else None,
            "all_in_price_cheapest_hour": {
                "price": cheapest_all_in[1]["all_in_price"],
                "time": cheapest_all_in[0].isoformat(),
            } if cheapest_all_in else None,
        }

    @staticmethod
    def _closest(hourly: dict, target: datetime):
        if not hourly:
            return None
        closest_dt = min(hourly.keys(), key=lambda dt: abs((dt - target).total_seconds()))
        return hourly[closest_dt]
