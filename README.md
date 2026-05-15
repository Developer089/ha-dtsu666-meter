# DTSU666 Energy Meter — Home Assistant integration (Modbus TCP)

Home Assistant integration that reads a **CHINT DTSU666 / DTSU666-H** three-phase
energy meter over **Modbus TCP** — directly or through an RS485-to-TCP gateway
(default Modbus port `502`, slave/unit ID `4`).

It exposes 28 sensors (voltages, currents, active/reactive/apparent power per
phase and total, power factor, frequency, and import/export energy counters)
ready for the Home Assistant **Energy Dashboard**.

> The register map is **not guessed**: it was verified against a physical
> CHINT DTSU666 and cross-checked against `lmatula/ha_chint_pm`,
> `elfabriceu/DTSU666-Modbus` and the CHINT manual.

## Two ways to install

### A) Custom integration (recommended) — UI config, robust

1. Copy `custom_components/dtsu666_meter/` into your HA `config/custom_components/`
   (or add this repo as a HACS custom repository, category *Integration*).
   HACS custom repository URL: `https://github.com/Developer089/ha-dtsu666-meter`
2. Restart Home Assistant.
3. **Settings → Devices & Services → Add Integration → "DTSU666"**.
4. Enter host / port / slave ID / polling interval. Connection is validated
   before the entry is created.

Defaults: port `502`, slave ID `4`, scan interval `10 s`. The scan interval can
be changed later via the integration's **Configure** (options) button.

### B) YAML package (no Python, built-in `modbus`)

Copy `yaml_package/dtsu666_modbus.yaml` into `config/packages/`, enable packages
in `configuration.yaml`:

```yaml
homeassistant:
  packages: !include_dir_named packages
```

Edit host/port/slave at the top of the file and restart. Fewer features (no UI,
no graceful per-block degradation) but zero custom code.

## Register map (FC03 holding, FLOAT32, big-endian byte+word, no swap)

| Quantity | Address | Scale | Unit |
|---|---|---|---|
| Voltage L1-L2 / L2-L3 / L3-L1 | 0x2000 / 0x2002 / 0x2004 | ×0.1 | V |
| Voltage L1 / L2 / L3 | 0x2006 / 0x2008 / 0x200A | ×0.1 | V |
| Current L1 / L2 / L3 | 0x200C / 0x200E / 0x2010 | ×0.001 | A |
| Active power total / L1 / L2 / L3 | 0x2012 / 0x2014 / 0x2016 / 0x2018 | ×0.1 | W |
| Reactive power total / L1 / L2 / L3 | 0x201A / 0x201C / 0x201E / 0x2020 | ×0.1 | var |
| Apparent power total / L1 / L2 / L3 | 0x2022 / 0x2024 / 0x2026 / 0x2028 | ×0.1 | VA |
| Power factor total / L1 / L2 / L3 | 0x202A / 0x202C / 0x202E / 0x2030 | ×0.001 | – |
| Frequency | 0x2044 | ×0.01 | Hz |
| Energy imported | 0x401E | ×1 | kWh |
| Energy exported | 0x4028 | ×1 | kWh |

Negative `Active power total` = export to grid. The integration reads the map in
4 contiguous blocks per cycle; a single failing block degrades only its own
sensors instead of taking the whole device offline.

## Energy Dashboard

`energy_import_total` and `energy_export_total` are `device_class: energy`,
`state_class: total_increasing`, kWh — add them as **Grid consumption** and
**Return to grid** in *Settings → Dashboards → Energy*.

## Requirements

- Home Assistant 2024.12+ (uses `entry.runtime_data`, `OptionsFlow` without
  passing the entry, modern typing).
- `pymodbus` 3.9–3.11 — Home Assistant ships its own pinned version; the
  integration decodes FLOAT32 with `struct` so it does not depend on the
  pymodbus payload/converter API that changed across 3.9 → 3.11.

## Troubleshooting

- **Cannot connect**: verify host/port and that the slave/unit ID matches the
  meter (this integration defaults to `4`; other installs commonly use `1` or
  `11`). Only one Modbus master can talk to the gateway at a time.
- **Nonsensical values**: would indicate a word-order mismatch — this map is
  big-endian word order, confirmed against the physical meter; no `swap`.
- Enable debug logging:

```yaml
logger:
  logs:
    custom_components.dtsu666_meter: debug
```

## License

MIT — see `LICENSE`.
