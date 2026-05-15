"""Sensor entities for the DTSU666 energy meter."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    UnitOfApparentPower,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfFrequency,
    UnitOfPower,
    UnitOfReactivePower,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import Dtsu666ConfigEntry
from .const import DOMAIN, MANUFACTURER, MODEL
from .coordinator import Dtsu666Coordinator


@dataclass(frozen=True, kw_only=True)
class Dtsu666SensorDescription(SensorEntityDescription):
    """Sensor description carrying the coordinator data key."""

    value_key: str


def _v(key: str) -> Dtsu666SensorDescription:
    return Dtsu666SensorDescription(
        key=key,
        value_key=key,
        translation_key=key,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        suggested_display_precision=1,
    )


def _a(key: str) -> Dtsu666SensorDescription:
    return Dtsu666SensorDescription(
        key=key,
        value_key=key,
        translation_key=key,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        suggested_display_precision=2,
    )


def _w(key: str) -> Dtsu666SensorDescription:
    return Dtsu666SensorDescription(
        key=key,
        value_key=key,
        translation_key=key,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        suggested_display_precision=1,
    )


def _var(key: str) -> Dtsu666SensorDescription:
    return Dtsu666SensorDescription(
        key=key,
        value_key=key,
        translation_key=key,
        device_class=SensorDeviceClass.REACTIVE_POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfReactivePower.VOLT_AMPERE_REACTIVE,
        suggested_display_precision=1,
    )


def _va(key: str) -> Dtsu666SensorDescription:
    return Dtsu666SensorDescription(
        key=key,
        value_key=key,
        translation_key=key,
        device_class=SensorDeviceClass.APPARENT_POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfApparentPower.VOLT_AMPERE,
        suggested_display_precision=1,
    )


def _pf(key: str) -> Dtsu666SensorDescription:
    return Dtsu666SensorDescription(
        key=key,
        value_key=key,
        translation_key=key,
        device_class=SensorDeviceClass.POWER_FACTOR,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=3,
    )


def _energy(key: str) -> Dtsu666SensorDescription:
    return Dtsu666SensorDescription(
        key=key,
        value_key=key,
        translation_key=key,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        suggested_display_precision=2,
    )


SENSORS: tuple[Dtsu666SensorDescription, ...] = (
    _v("voltage_l1_l2"),
    _v("voltage_l2_l3"),
    _v("voltage_l3_l1"),
    _v("voltage_l1"),
    _v("voltage_l2"),
    _v("voltage_l3"),
    _a("current_l1"),
    _a("current_l2"),
    _a("current_l3"),
    _w("active_power_total"),
    _w("active_power_l1"),
    _w("active_power_l2"),
    _w("active_power_l3"),
    _var("reactive_power_total"),
    _var("reactive_power_l1"),
    _var("reactive_power_l2"),
    _var("reactive_power_l3"),
    _va("apparent_power_total"),
    _va("apparent_power_l1"),
    _va("apparent_power_l2"),
    _va("apparent_power_l3"),
    _pf("power_factor_total"),
    _pf("power_factor_l1"),
    _pf("power_factor_l2"),
    _pf("power_factor_l3"),
    Dtsu666SensorDescription(
        key="frequency",
        value_key="frequency",
        translation_key="frequency",
        device_class=SensorDeviceClass.FREQUENCY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfFrequency.HERTZ,
        suggested_display_precision=2,
    ),
    _energy("energy_import_total"),
    _energy("energy_export_total"),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: Dtsu666ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Create one entity per register from the verified map."""
    coordinator = entry.runtime_data
    async_add_entities(
        Dtsu666Sensor(coordinator, entry.entry_id, desc) for desc in SENSORS
    )


class Dtsu666Sensor(CoordinatorEntity[Dtsu666Coordinator], SensorEntity):
    """A single decoded DTSU666 measurement."""

    _attr_has_entity_name = True
    entity_description: Dtsu666SensorDescription

    def __init__(
        self,
        coordinator: Dtsu666Coordinator,
        entry_id: str,
        description: Dtsu666SensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            name=MODEL,
            manufacturer=MANUFACTURER,
            model=MODEL,
        )

    @property
    def native_value(self) -> float | None:
        return self.coordinator.data.get(self.entity_description.value_key)

    @property
    def available(self) -> bool:
        return (
            super().available
            and self.entity_description.value_key in self.coordinator.data
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        self.async_write_ha_state()
