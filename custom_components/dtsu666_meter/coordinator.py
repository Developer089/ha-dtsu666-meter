"""DataUpdateCoordinator: polls the DTSU666 over Modbus TCP."""

from __future__ import annotations

import logging
import struct
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from pymodbus.client import AsyncModbusTcpClient
from pymodbus.exceptions import ModbusException

from .const import DOMAIN, FIELD_MAP, REGISTER_BLOCKS

_LOGGER = logging.getLogger(__name__)


def _decode_float32(registers: list[int], offset: int) -> float:
    """Decode a big-endian (byte + word) IEEE-754 FLOAT32 from two registers.

    Done with struct rather than pymodbus' convert_from_registers so the code
    is immune to the payload/converter API churn across pymodbus 3.9–3.11.
    Matches the byte/word order verified against the physical meter.
    """
    hi, lo = registers[offset], registers[offset + 1]
    return struct.unpack(">f", struct.pack(">HH", hi, lo))[0]


class Dtsu666Coordinator(DataUpdateCoordinator[dict[str, float]]):
    """Reads every register block once per ``scan_interval``."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        host: str,
        port: int,
        slave_id: int,
        scan_interval: int,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            config_entry=config_entry,
            update_interval=timedelta(seconds=scan_interval),
        )
        self._host = host
        self._port = port
        self._slave_id = slave_id
        self._client = AsyncModbusTcpClient(host, port=port, timeout=5)

    async def _read_holding(self, address: int, count: int):
        """Read holding registers, tolerating the slave/device_id kwarg rename
        across pymodbus versions (3.9 used ``slave=``, 3.11 ``device_id=``)."""
        try:
            return await self._client.read_holding_registers(
                address, count=count, device_id=self._slave_id
            )
        except TypeError:
            return await self._client.read_holding_registers(
                address, count=count, slave=self._slave_id
            )

    async def _async_update_data(self) -> dict[str, float]:
        try:
            if not self._client.connected:
                await self._client.connect()
            if not self._client.connected:
                raise UpdateFailed(
                    f"Cannot connect to DTSU666 at {self._host}:{self._port}"
                )

            raw_blocks: dict[int, list[int]] = {}
            failures = 0
            for block in REGISTER_BLOCKS:
                try:
                    rr = await self._read_holding(block.address, block.count)
                except (ModbusException, ConnectionError, OSError) as err:
                    failures += 1
                    _LOGGER.debug(
                        "Block 0x%04X read error: %s", block.address, err
                    )
                    continue
                if rr.isError() or len(rr.registers) < block.count:
                    failures += 1
                    _LOGGER.debug(
                        "Block 0x%04X bad response: %s", block.address, rr
                    )
                    continue
                # All-zero block = converter/comm glitch, not a real reading.
                if not any(rr.registers):
                    failures += 1
                    continue
                raw_blocks[block.address] = rr.registers

            if not raw_blocks:
                raise UpdateFailed("All register blocks failed to read")

            data: dict[str, float] = {}
            for key, (block_addr, offset, scale) in FIELD_MAP.items():
                regs = raw_blocks.get(block_addr)
                if regs is None or offset + 2 > len(regs):
                    continue
                try:
                    data[key] = round(_decode_float32(regs, offset) * scale, 3)
                except (struct.error, IndexError):
                    continue

            if failures:
                _LOGGER.debug("%d/%d blocks failed this cycle",
                              failures, len(REGISTER_BLOCKS))
            return data

        except ModbusException as err:
            raise UpdateFailed(f"Modbus exception: {err}") from err
        except (ConnectionError, OSError) as err:
            raise UpdateFailed(f"Connection error: {err}") from err

    async def async_shutdown(self) -> None:
        """Close the Modbus socket on unload."""
        self._client.close()
        await super().async_shutdown()
