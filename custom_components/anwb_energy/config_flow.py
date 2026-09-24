import voluptuous as vol

from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry, OptionsFlowWithReload
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.selector import SelectSelector, SelectSelectorConfig, SelectSelectorMode

from .const import (
    DOMAIN,
    CONF_ELECTRICITY,
    CONF_GAS,
    CONF_PRICE_UNIT,
    PRICE_UNIT_CENTS,
    PRICE_UNIT_EUROS,
)


class ANWBEnergyConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlowWithReload:
        return ANWBEnergyOptionsFlow()

    async def async_step_user(self, user_input=None) -> FlowResult:
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            if not user_input.get(CONF_ELECTRICITY) and not user_input.get(CONF_GAS):
                return self.async_show_form(
                    step_id="user",
                    data_schema=self._schema(),
                    errors={"base": "at_least_one"},
                )
            return self.async_create_entry(title="ANWB Energy", data=user_input)

        return self.async_show_form(step_id="user", data_schema=self._schema())

    async def async_step_reconfigure(self, user_input=None) -> FlowResult:
        entry = self._get_reconfigure_entry()
        current = {**entry.data, **entry.options}

        if user_input is not None:
            if not user_input.get(CONF_ELECTRICITY) and not user_input.get(CONF_GAS):
                return self.async_show_form(
                    step_id="reconfigure",
                    data_schema=self._schema(current),
                    errors={"base": "at_least_one"},
                )

            registry = er.async_get(self.hass)
            for entity in er.async_entries_for_config_entry(registry, entry.entry_id):
                if entity.domain == "sensor":
                    registry.async_update(entity.entity_id, display_precision=2)

            return self.async_update_reload_and_abort(entry, data_updates=user_input)

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=self._schema(current),
        )

    @staticmethod
    def _schema(current: dict | None = None) -> vol.Schema:
        current = current or {}
        return vol.Schema(
            {
                vol.Required(
                    CONF_ELECTRICITY,
                    default=current.get(CONF_ELECTRICITY, True),
                ): bool,
                vol.Required(CONF_GAS, default=current.get(CONF_GAS, True)): bool,
                vol.Required(
                    CONF_PRICE_UNIT,
                    default=current.get(CONF_PRICE_UNIT, PRICE_UNIT_CENTS),
                ): SelectSelector(
                    SelectSelectorConfig(
                        options=[PRICE_UNIT_CENTS, PRICE_UNIT_EUROS],
                        translation_key=CONF_PRICE_UNIT,
                        mode=SelectSelectorMode.LIST,
                    )
                ),
            }
        )


class ANWBEnergyOptionsFlow(OptionsFlowWithReload):
    async def async_step_init(self, user_input=None) -> FlowResult:
        if user_input is not None:
            if not user_input.get(CONF_ELECTRICITY) and not user_input.get(CONF_GAS):
                return self.async_show_form(
                    step_id="init",
                    data_schema=self._schema(),
                    errors={"base": "at_least_one"},
                )
            return self.async_create_entry(data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=self._schema(
                {**self.config_entry.data, **self.config_entry.options}
            ),
        )

    @staticmethod
    def _schema(current: dict | None = None) -> vol.Schema:
        current = current or {}
        return vol.Schema(
            {
                vol.Required(
                    CONF_ELECTRICITY,
                    default=current.get(CONF_ELECTRICITY, True),
                ): bool,
                vol.Required(CONF_GAS, default=current.get(CONF_GAS, True)): bool,
                vol.Required(
                    CONF_PRICE_UNIT,
                    default=current.get(CONF_PRICE_UNIT, PRICE_UNIT_CENTS),
                ): SelectSelector(
                    SelectSelectorConfig(
                        options=[PRICE_UNIT_CENTS, PRICE_UNIT_EUROS],
                        translation_key=CONF_PRICE_UNIT,
                        mode=SelectSelectorMode.LIST,
                    )
                ),
            }
        )
