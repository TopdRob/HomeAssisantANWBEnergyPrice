import pytest

from homeassistant import config_entries
from homeassistant.const import SOURCE_RECONFIGURE, SOURCE_USER

from custom_components.anwb_energie.const import (
    CONF_ELECTRICITY,
    CONF_GAS,
    CONF_PRICE_UNIT,
    DOMAIN,
    PRICE_UNIT_CENTS,
)


async def test_user_flow_creates_entry(hass) -> None:
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )

    assert result["type"] is config_entries.FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_ELECTRICITY: True,
            CONF_GAS: False,
            CONF_PRICE_UNIT: PRICE_UNIT_CENTS,
        },
    )

    assert result["type"] is config_entries.FlowResultType.CREATE_ENTRY
    assert result["title"] == "ANWB Energie"
    assert result["data"][CONF_ELECTRICITY] is True


async def test_user_flow_requires_an_energy_type(hass) -> None:
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_ELECTRICITY: False,
            CONF_GAS: False,
            CONF_PRICE_UNIT: PRICE_UNIT_CENTS,
        },
    )

    assert result["type"] is config_entries.FlowResultType.FORM
    assert result["errors"] == {"base": "at_least_one"}


async def test_user_flow_allows_only_one_entry(hass, config_entry) -> None:
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )

    assert result["type"] is config_entries.FlowResultType.ABORT
    assert result["reason"] == "single_instance_allowed"


async def test_reconfigure_flow_shows_existing_values(hass, config_entry) -> None:
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={
            "source": SOURCE_RECONFIGURE,
            "entry_id": config_entry.entry_id,
        },
    )

    assert result["type"] is config_entries.FlowResultType.FORM
    assert result["step_id"] == "reconfigure"


async def test_options_flow_updates_existing_entry(hass, config_entry) -> None:
    result = await hass.config_entries.options.async_init(
        config_entry.entry_id,
        context={"source": SOURCE_USER},
    )

    assert result["type"] is config_entries.FlowResultType.FORM
    assert result["step_id"] == "init"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_ELECTRICITY: False,
            CONF_GAS: True,
            CONF_PRICE_UNIT: PRICE_UNIT_CENTS,
        },
    )

    assert result["type"] is config_entries.FlowResultType.CREATE_ENTRY
    assert result["result"][CONF_ELECTRICITY] is False
    assert hass.config_entries.async_get_entry(config_entry.entry_id) is config_entry


@pytest.fixture
def config_entry(hass):
    """Provide a configured entry for tests that need an existing entry."""
    entry = config_entries.ConfigEntry(
        version=1,
        minor_version=1,
        domain=DOMAIN,
        title="ANWB Energie",
        data={
            CONF_ELECTRICITY: True,
            CONF_GAS: True,
            CONF_PRICE_UNIT: PRICE_UNIT_CENTS,
        },
        source=SOURCE_USER,
        entry_id="anwb-energy-test",
        options={},
    )
    hass.config_entries.async_add(entry)
    return entry