"""Real inverter block data captured from the wire. DATA ONLY -- no imports, no logic.

Naming contract, enforced by review:

  BLOCK_*   Verbatim bytes from a real device. Reconstructed from the ``hex_preview``
            field of a ``[BLOCK RAW]`` debug line, so the framing is exact: a leading
            ``(`` and a trailing ``\\r``, with no closing paren. Golden value
            assertions MAY use these.
  SYNTH_*   Hand-constructed. For structural and edge-case tests ONLY -- never for
            value-parity assertions, because a hand-built block proves nothing about
            what a device actually emits.

To add a capture: ask the reporter for ``LOG_LEVEL: debug`` output, take the
``hex_preview`` from the ``[BLOCK RAW]`` line, decode it, and paste it verbatim under
a name that records the block key and the device state it was taken in. Record the
model and firmware in a comment.
"""

# ---------------------------------------------------------------------------
# Device A -- HPVINV04, firmware 0010.11, 2x parallel, 2x battery (32-cell bank).
# Captured 2026-08-20 while charging in battery mode with PV on string 2.
# This device's payloads arrive as TWO disjoint block sets, which is why the
# energy calculation must gate per payload rather than assume every field is
# present every time.
# ---------------------------------------------------------------------------

# --- payload 1: telemetry (11 blocks) --------------------------------------
BLOCK_2ONL_CHARGING = b"(04 053.4 058 007 00000 420 110007200000 00000000\r"
BLOCK_2L0E_LOADED = b"(228.5 49.9 00868 00766 007 018 11000 008.7 01175\r"
BLOCK_WDRR_NO_GRID_FLOW = b"(232.7 49.9 280 170 65 40 +00000 0 11000 11+00000\r"
BLOCK_YAVB_CHARGING = b"(04 1001100000000000 042.0 057.6 195.0 058 0029.1 0000.0 03041 000000\r"
BLOCK_93VQ_SETTINGS = b"(1 050 010 13310110230 011 1 1 0 1 1 015 035 050 025 056.4 056.4 042.0 020 0 0\r"
BLOCK_DHRK_SETTINGS = b"(1 044.0 020 044.0 046.0 054.0 0 058.4 060 120 030 0000 0000 05 0000 52.0 50000\r"
BLOCK_EO8W_STATUS = b"(00 B010000000000 20211002120B117020000\r"
BLOCK_MPOD_PV1_IDLE = b"(000.0 00.0 00000 00000.0 00000 0 380.0 018 12000\r"
BLOCK_NOEP_PV2_ACTIVE = b"(132.0 10.6 01403 2 132.5 00000000000000000000000\r"
BLOCK_V4W3_TEMPS = b"(058 048 038 059 059 050 050 11 048 051 000000000\r"
BLOCK_COST_ENERGY = b"(260720 10:04 02.939 0315.7 2081.0 000002284.6 000000000000\r"

# --- payload 2: identity + BMS detail (4 blocks, zero overlap with payload 1)
BLOCK_SUCV_MODEL = b"(HPVINV04\r"
BLOCK_HR6Y_FIRMWARE = b"(0010.11 20250630 14\r"
BLOCK_UXJP_BMS_CAPACITY = b"(0173.0 0299.8 2 3327 0009 3320 0032 0000000000000000000000\r"
BLOCK_V09K_CELLS_16 = (
    b"(3321 3321 3323 3322 3323 3322 3323 3321 3328 3326 3323 3323 3322 3325 3324 3321 00000000\r"
)

CAPTURE_TELEMETRY = {
    "2ONL": BLOCK_2ONL_CHARGING,
    "2l0E": BLOCK_2L0E_LOADED,
    "WdRR": BLOCK_WDRR_NO_GRID_FLOW,
    "Yavb": BLOCK_YAVB_CHARGING,
    "93VQ": BLOCK_93VQ_SETTINGS,
    "dHrK": BLOCK_DHRK_SETTINGS,
    "eo8w": BLOCK_EO8W_STATUS,
    "Mpod": BLOCK_MPOD_PV1_IDLE,
    "noeP": BLOCK_NOEP_PV2_ACTIVE,
    "V4W3": BLOCK_V4W3_TEMPS,
    "COST": BLOCK_COST_ENERGY,
}

CAPTURE_IDENTITY = {
    "SUCV": BLOCK_SUCV_MODEL,
    "hR6Y": BLOCK_HR6Y_FIRMWARE,
    "uxJp": BLOCK_UXJP_BMS_CAPACITY,
    "v09K": BLOCK_V09K_CELLS_16,
}

# Golden expected state for CAPTURE_TELEMETRY, taken from the add-on's own
# "Published to HA" line for that exact payload. Config-INDEPENDENT values only --
# anything scaled by INVERTER_COUNT lives in EXPECTED_TELEMETRY_SCALED below.
EXPECTED_TELEMETRY = {
    "bat_v": 53.4,
    "bat_cap": 58,
    "bat_charge_current": 7.0,
    "dischg_current": 0.0,
    "bus_voltage": 420.0,
    "bms_current_soc": 58,
    "bms_charging_current_a": 29.1,
    "bms_discharge_current_a": 0.0,
    "grid_v": 232.7,
    "grid_hz": 49.9,
    "mains_power_w": 0,
    "mains_apparent_va": 0,
    "out_v": 228.5,
    "out_hz": 49.9,
    "apparent_va": 868,
    "load_w": 766,
    "load_pct": 7,
    "output_dc_comp": 18,
    "inductor_current_a": 8.7,
    "generation_power_w": 1403,
    "pv_v": 0.0,
    "pv_current_a": 0.0,
    "pv_w": 0,
    "pv2_v": 132.0,
    "pv2_current_a": 10.6,
    "pv2_power_w": 1403,
    "pv_today_kwh": 2.939,
    "pv_month_kwh": 315.7,
    "pv_year_kwh": 2081.0,
    "pv_total_kwh": 2284.6,
    "pv_temp": 58.0,
    "pv2_temp": 48.0,
    "inverter_temperature_c": 48.0,
    "transformer_temperature_c": 59.0,
    "max_temperature_c": 59.0,
    "dc_rectification_temperature_c": 51.0,
    "fan_1_speed": 50,
    "fan_2_speed": 50,
}

# Requires INVERTER_COUNT = 2, which is this device's configuration.
EXPECTED_TELEMETRY_SCALED = {
    "c_load_w": 1532,
    "c_generation_power_w": 2806,
    "c_mains_power_w": 0,
}

EXPECTED_IDENTITY = {
    "model_code": "HPVINV04",
    "firmware_version": "0010.11",
    "software_version": "10.11",
    "firmware_build_date": "2025-06-30",
    "firmware_build_slot": "14",
    "bms_remaining_ah": 173.0,
    "bms_nominal_ah": 299.8,
    "bms_cell_count": 16,
    "cell_1_mv": 3321,
    "cell_9_mv": 3328,
    "cell_16_mv": 3321,
    # From uxJp, the BMS's own whole-bank summary. Note min is at position 32 on a
    # bank whose v09K block only carries 16 cells -- cells 17-32 have no entity.
    "bms_max_cell_mv": 3327,
    "bms_max_cell_pos": 9,
    "bms_min_cell_mv": 3320,
    "bms_min_cell_pos": 32,
    "bms_cell_delta_mv": 7,
}

# ---------------------------------------------------------------------------
# Device B -- the reference unit documented in sensor_mapping.md. These are the
# literals the original test suite used; kept so those assertions stay anchored to
# a second, independently captured device.
# ---------------------------------------------------------------------------

BLOCK_HR6Y_FIRMWARE_REF = b"(0010.11 20250630 14)"
BLOCK_2L0E_REF = b"(229.8 49.9 252 129 2 24 11000 006.1 0044)"
BLOCK_93VQ_REF = b"(1 050 010 13310110230 011 1 1 0 1 1 015 035 050 025 056.4 056.4 042.0 020 0 0)"
BLOCK_EO8W_REF = b"(00 B0100000000000 20211002110B117020000)"
BLOCK_YAVB_REF = b"(04 1001100000000000 042.0 057.6 195.0 054 0022.3 0000.0 02921 000000 18.95)"
BLOCK_YAVB_REF_NO_TAIL = b"(04 1001100000000000 042.0 057.6 195.0 054 0022.3 0000.0 02921 000000)"

# ---------------------------------------------------------------------------
# Synthetic blocks -- structural tests only. Never assert app parity on these.
# ---------------------------------------------------------------------------

SYNTH_UNKNOWN_BLOCK = b"(1 2 3)"
SYNTH_V09K_CELL_3_COLLAPSED = b"(3321 3321 1900 3322 3323 00000000)"
SYNTH_2L0E_OVERLOADED = b"(228.5 49.9 00868 00766 115 018 11000 008.7 01175\r"
SYNTH_2ONL_IDLE = b"(04 053.4 058 000 00000 420 110007200000 00000000\r"
SYNTH_YAVB_ABSURD_CURRENT = b"(04 1001100000000000 042.0 057.6 195.0 058 9999.0 0000.0 03041 000000\r"
SYNTH_WDRR_RELAY_OPEN = b"(232.7 49.9 280 170 65 40 +00000 0 01000 11+00000\r"

# ---------------------------------------------------------------------------
# NOT YET CAPTURED
# The parser recognises 15 block keys. Device A above covers all of them except
# none -- but only Device A's *configuration* is represented. Captures still
# wanted: a 120 V unit (the 93VQ config decode no-ops unless the packed word ends
# "230"), an inverter reporting a real BMS fault word (every capture so far reads
# the all-clear 1001100000000000), and a single-inverter non-parallel install.
# ---------------------------------------------------------------------------
