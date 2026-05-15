#!/usr/bin/env python3
"""Standalone sanity check: read the real DTSU666 with the integration's
register map + decode and print decoded values. Uses pymodbus 2.x sync API
(what the RPi has) — independent of the HA/pymodbus-3 code path.

Usage: python3 validate_against_meter.py <host> <port> <slave>
"""
import struct
import sys

from pymodbus.client.sync import ModbusTcpClient

# Mirror of custom_components/dtsu666_meter/const.py
BLOCKS = ((0x2000, 42), (0x202A, 8), (0x2044, 2), (0x401E, 12))
FIELD_MAP = {
    "voltage_l1_l2": (0x2000, 0, 0.1), "voltage_l2_l3": (0x2000, 2, 0.1),
    "voltage_l3_l1": (0x2000, 4, 0.1), "voltage_l1": (0x2000, 6, 0.1),
    "voltage_l2": (0x2000, 8, 0.1), "voltage_l3": (0x2000, 10, 0.1),
    "current_l1": (0x2000, 12, 0.001), "current_l2": (0x2000, 14, 0.001),
    "current_l3": (0x2000, 16, 0.001),
    "active_power_total": (0x2000, 18, 0.1), "active_power_l1": (0x2000, 20, 0.1),
    "active_power_l2": (0x2000, 22, 0.1), "active_power_l3": (0x2000, 24, 0.1),
    "reactive_power_total": (0x2000, 26, 0.1),
    "apparent_power_total": (0x2000, 34, 0.1),
    "power_factor_total": (0x202A, 0, 0.001),
    "frequency": (0x2044, 0, 0.01),
    "energy_import_total": (0x401E, 0, 1.0),
    "energy_export_total": (0x401E, 10, 1.0),
}


def decode_float32(regs, off):
    return struct.unpack(">f", struct.pack(">HH", regs[off], regs[off + 1]))[0]


def main():
    host = sys.argv[1] if len(sys.argv) > 1 else "192.168.1.50"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 502
    slave = int(sys.argv[3]) if len(sys.argv) > 3 else 4

    c = ModbusTcpClient(host, port=port, timeout=5)
    if not c.connect():
        print("CONNECT FAIL", host, port)
        sys.exit(1)

    raw = {}
    for addr, cnt in BLOCKS:
        rr = c.read_holding_registers(addr, cnt, unit=slave)
        if rr.isError():
            print("READ FAIL 0x%04X: %s" % (addr, rr))
            continue
        raw[addr] = rr.registers
    c.close()

    for key, (baddr, off, scale) in FIELD_MAP.items():
        regs = raw.get(baddr)
        if regs is None or off + 2 > len(regs):
            print("%-22s : <no data>" % key)
            continue
        print("%-22s : %.3f" % (key, decode_float32(regs, off) * scale))


if __name__ == "__main__":
    main()
