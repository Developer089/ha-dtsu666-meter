"""Config and options flow for the DTSU666 Modbus TCP integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_SCAN_INTERVAL
from homeassistant.core import callback
from homeassistant.exceptions import HomeAssistantError

from pymodbus.client import AsyncModbusTcpClient

from .const import (
    CONF_SLAVE_ID,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SLAVE_ID,
    DOMAIN,
    MAX_SCAN_INTERVAL,
    MIN_SCAN_INTERVAL,
)


class CannotConnect(HomeAssistantError):
    """Raised when the meter cannot be reached."""


async def _validate(host: str, port: int, slave_id: int) -> None:
    """Open a Modbus TCP session and read one register to prove it works."""
    client = AsyncModbusTcpClient(host, port=port, timeout=5)
    try:
        await client.connect()
        if not client.connected:
            raise CannotConnect
        try:
            rr = await client.read_holding_registers(
                0x2000, count=2, device_id=slave_id
            )
        except TypeError:
            rr = await client.read_holding_registers(
                0x2000, count=2, slave=slave_id
            )
        if rr.isError():
            raise CannotConnect
    except (ConnectionError, OSError) as err:
        raise CannotConnect from err
    finally:
        client.close()


def _user_schema() -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_HOST): str,
            vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
            vol.Required(CONF_SLAVE_ID, default=DEFAULT_SLAVE_ID): int,
            vol.Required(
                CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL
            ): vol.All(
                vol.Coerce(float),
                vol.Range(min=MIN_SCAN_INTERVAL, max=MAX_SCAN_INTERVAL),
            ),
        }
    )


class Dtsu666ConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the initial UI configuration."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            await self.async_set_unique_id(
                f"{user_input[CONF_HOST]}:{user_input[CONF_PORT]}:"
                f"{user_input[CONF_SLAVE_ID]}"
            )
            self._abort_if_unique_id_configured()
            try:
                await _validate(
                    user_input[CONF_HOST],
                    user_input[CONF_PORT],
                    user_input[CONF_SLAVE_ID],
                )
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=f"DTSU666 ({user_input[CONF_HOST]})",
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user", data_schema=_user_schema(), errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return Dtsu666OptionsFlow()


class Dtsu666OptionsFlow(OptionsFlow):
    """Allow changing the scan interval after setup."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current = self.config_entry.options.get(
            CONF_SCAN_INTERVAL,
            self.config_entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
        )
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_SCAN_INTERVAL, default=current
                    ): vol.All(
                        vol.Coerce(float),
                        vol.Range(min=MIN_SCAN_INTERVAL, max=MAX_SCAN_INTERVAL),
                    )
                }
            ),
        )
