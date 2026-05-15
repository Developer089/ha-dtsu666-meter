"""Constants and the verified DTSU666 Modbus register map.

Register map cross-checked against:
  * a real CHINT DTSU666 read over Modbus TCP — values confirmed against the
    meter display,
  * lmatula/ha_chint_pm and elfabriceu/DTSU666-Modbus (GitHub),
  * the original CHINT "dtsu666_series" manufacturer manual.

All measured quantities are IEEE-754 FLOAT32 spanning 2 holding registers
(function code 0x03), big-endian byte AND word order (no swap).
"""

from __future__ import annotations

from dataclasses import dataclass

DOMAIN = "dtsu666_meter"

CONF_SLAVE_ID = "slave_id"

DEFAULT_PORT = 502
DEFAULT_SLAVE_ID = 4          # common DTSU666 default; configurable in the UI
DEFAULT_SCAN_INTERVAL = 1.0   # seconds (float — sub-second is allowed)
MIN_SCAN_INTERVAL = 0.2       # 200 ms
MAX_SCAN_INTERVAL = 600.0

MANUFACTURER = "CHINT"
MODEL = "DTSU666"


@dataclass(frozen=True)
class RegisterBlock:
    """A single contiguous holding-register read."""

    address: int
    count: int


# Contiguous blocks read once per poll. Splitting on the register gaps keeps
# each request small and lets one failing block degrade gracefully instead of
# taking the whole update down.
REGISTER_BLOCKS: tuple[RegisterBlock, ...] = (
    RegisterBlock(0x2000, 42),  # voltages, currents, active/reactive/apparent P
    RegisterBlock(0x202A, 8),   # power factors (total + L1..L3)
    RegisterBlock(0x2044, 2),   # frequency
    RegisterBlock(0x401E, 12),  # energy: import @ off 0, export @ off 10
)

# value_key -> (block start address, register offset within block, scale).
# Decoded value = raw_float32 * scale.
FIELD_MAP: dict[str, tuple[int, int, float]] = {
    # Line-to-line voltages
    "voltage_l1_l2": (0x2000, 0, 0.1),
    "voltage_l2_l3": (0x2000, 2, 0.1),
    "voltage_l3_l1": (0x2000, 4, 0.1),
    # Phase voltages
    "voltage_l1": (0x2000, 6, 0.1),
    "voltage_l2": (0x2000, 8, 0.1),
    "voltage_l3": (0x2000, 10, 0.1),
    # Currents
    "current_l1": (0x2000, 12, 0.001),
    "current_l2": (0x2000, 14, 0.001),
    "current_l3": (0x2000, 16, 0.001),
    # Active power (negative total typically = export to grid)
    "active_power_total": (0x2000, 18, 0.1),
    "active_power_l1": (0x2000, 20, 0.1),
    "active_power_l2": (0x2000, 22, 0.1),
    "active_power_l3": (0x2000, 24, 0.1),
    # Reactive power
    "reactive_power_total": (0x2000, 26, 0.1),
    "reactive_power_l1": (0x2000, 28, 0.1),
    "reactive_power_l2": (0x2000, 30, 0.1),
    "reactive_power_l3": (0x2000, 32, 0.1),
    # Apparent power
    "apparent_power_total": (0x2000, 34, 0.1),
    "apparent_power_l1": (0x2000, 36, 0.1),
    "apparent_power_l2": (0x2000, 38, 0.1),
    "apparent_power_l3": (0x2000, 40, 0.1),
    # Power factors
    "power_factor_total": (0x202A, 0, 0.001),
    "power_factor_l1": (0x202A, 2, 0.001),
    "power_factor_l2": (0x202A, 4, 0.001),
    "power_factor_l3": (0x202A, 6, 0.001),
    # Frequency
    "frequency": (0x2044, 0, 0.01),
    # Energy counters (raw float is already in kWh)
    "energy_import_total": (0x401E, 0, 1.0),
    "energy_export_total": (0x401E, 10, 1.0),
}
