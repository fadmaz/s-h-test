# Verified sensor mapping — HPVINV04

A second mapping, built independently of [`sensor_mapping.md`](sensor_mapping.md), which
is kept as-is. This one is assembled from two sources captured on the same day:

- **The wire** — a full debug capture from add-on 2.6.8, with every block and every token
  position recorded (`DEBUG_FLAGS` all on, 2026-08-21).
- **The vendor portal** — `solar.siseli.com`, device `Dtu34545375423553743260`, read
  directly from the *Data Overview* page at inverter clock `05:34` on the same day.

**Device:** `HPVINV04`, firmware `0010.11` (build `20250630`, slot `14`), software
version `10.11`, protocol `MH2089635`. Rated power **11 kW**. Two inverters in parallel
(`Parallel Role: Host`, `Total Number Of Grid Connection: 2`), 2 × 300 Ah battery bank,
one live PV string on the **second** MPPT input.

> **Timestamps differ.** The log capture ends at inverter clock `05:17`; the portal was
> read at `05:34`. Slow-moving values (settings, limits, identifiers) are directly
> comparable. Fast-moving ones (power, current, temperature) will differ, and a mismatch
> there is **not** evidence of a decode error. Rows where that matters are marked.

---

## 1. The headline finding

**Every sensor the bridge currently reports as `unknown` has a real value in the vendor
portal.** All ~40 of them. The data is in the stream; the bridge just cannot locate it.

That is a meaningful change to what "undecodable" means here. It is not missing data — it
is data encoded in the bit and status fields the bridge currently publishes only as raw
strings. See [section 5](#5-what-the-bridge-cannot-decode-yet).

---

## 2. Blocks on the wire

Fifteen distinct blocks were observed. Payloads carry different subsets — one payload in
this capture carried eleven blocks, the next carried four, with **zero overlap**.

| Block | Tokens | Carries | Fully decoded? |
|---|---|---|---|
| `2ONL` | 8 | Battery voltage, capacity, currents, series count, bus voltage | Tokens 6–7 undecoded |
| `2l0E` | 9 | Output voltage/frequency, apparent and active power, load %, DC component, inductor current, rated power | Token 6 undecoded |
| `93VQ` | 20 | The settings block — charge voltages, SOC thresholds, currents, times | Token 3 undecoded |
| `COST` | 7 | System date/time, daily/monthly/yearly/total PV energy | Token 6 undecoded |
| `Mpod` | 9 | PV1 voltage/current/power, PV1 temperature | Tokens 4–5, 8 undecoded |
| `V4W3` | 11 | Temperatures and fan speeds | Token 10 undecoded |
| `WdRR` | 10 | Grid voltage/frequency, mains loss thresholds, mains power, flow, relay | Token 8 partly |
| `Yavb` | 10 | BMS limits, SOC, charge/discharge currents, **the 16-bit flag word** | Tokens 1, 8, 9 undecoded |
| `dHrK` | 17 | Second-output and equalization settings | Tokens 11, 12, 14 undecoded |
| `eo8w` | 3 | Status code, **13-char flag string**, build blob | Tokens 1–2 undecoded |
| `noeP` | 6 | PV2 voltage/current/power | Token 5 undecoded |
| `hR6Y` | 3 | Firmware version, build date, build slot | Fully decoded |
| `SUCV` | 1 | Model code | Fully decoded |
| `uxJp` | 8 | BMS remaining/nominal Ah, cell min/max and positions | Token 7 undecoded |
| `v09K` | 17 | Cell voltages 1–16 | Token 16 undecoded |

### Observed values, this capture

```
2ONL  04 053.0 038 002 00000 369 110007200000 00000000
2l0E  229.3 50.0 00550 00410 005 032 11000 007.5 00629
93VQ  1 050 010 13310110230 011 1 1 0 1 1 015 035 050 025 056.4 056.4 042.0 020 0 0
COST  260721 05:17 00.967 0328.0 2093.3 000002296.9 000000000000
Mpod  000.0 00.0 00000 00000.0 00000 0 380.0 018 12000
V4W3  050 047 038 059 059 030 030 11 045 049 000000000
WdRR  227.7 50.0 280 170 65 40 +00000 0 11000 11+00000
Yavb  04 1001100000000000 042.0 057.6 195.0 038 0015.9 0000.0 03041 000000
dHrK  1 044.0 020 044.0 046.0 054.0 0 058.4 060 120 030 0000 0000 05 0000 52.0 50000
eo8w  00 B010000000000 20211002120B117020000
noeP  185.0 04.7 00873 2 184.3 00000000000000000000000
hR6Y  0010.11 20250630 14
SUCV  HPVINV04
uxJp  0114.0 0299.8 2 3302 0009 3296 0032 0000000000000000000000
v09K  3300 3298 3299 3300 3300 3300 3299 3299 3302 3300 3300 3300 3300 3300 3300 3298 00000000
```

---

## 3. Decoded and confirmed against the portal

Every row here was checked against the portal's own label and value.

### Identity and firmware

| Portal label | Portal | Bridge key | Bridge | Source |
|---|---|---|---|---|
| Device Type | `HPVINV04` | `model_code` | `HPVINV04` | `SUCV`[0] |
| Software Version | `10.11` | `software_version` | `10.11` | `hR6Y`[0] |
| — | — | `firmware_version` | `0010.11` | `hR6Y`[0] |
| — | — | `firmware_build_date` | `2025-06-30` | `hR6Y`[1] |
| — | — | `firmware_build_slot` | `14` | `hR6Y`[2] |
| Status Code | `00` | `status_code` | `00` | `eo8w`[0] |
| System Time (Year Month Day) | `260721` | `system_time_ymd` | `260721` | `COST`[0] |
| System Time (Hour Minute) | `05:34` | `system_time_hm` | `05:17` | `COST`[1] |

### Battery

| Portal label | Portal | Bridge key | Bridge | Source |
|---|---|---|---|---|
| Battery Voltage | `53 V` | `bat_v` | `53.0` | `2ONL`[1] |
| Battery Capacity | `39 %` | `bat_cap` | `38` | `2ONL`[2] |
| Battery Charging Current | `1 A` | `bat_charge_current` | `2.0` | `2ONL`[3] |
| Battery Discharge Current | `0 A` | `dischg_current` | `0.0` | `2ONL`[4] |
| Battery Number In Series | `4` | `bat_series_count` | `4` | `2ONL`[0] |
| Battery Status | `Charge` | `battery_status` | `Charge` | *derived from calculated power* |
| BUS Voltage | `371 V` | `bus_voltage` | `369.0` | `2ONL`[5] |

### BMS

| Portal label | Portal | Bridge key | Bridge | Source |
|---|---|---|---|---|
| Remaining Capacity | `116.3 A` | `bms_remaining_ah` | `114.0` | `uxJp`[0] |
| Nominal Capacity | `299.8 A` | `bms_nominal_ah` | `299.8` | `uxJp`[1] |
| Display Mode | `Display All Battery Cell Data Locations` | `bms_display_mode` | *same* | `uxJp`[2] |
| Max Voltage | `3305 mV` | `bms_max_cell_mv` | `3302` | `uxJp`[3] |
| Max Voltage Cell Position | `ID:0(9)` | `bms_max_cell_pos` | `9` | `uxJp`[4] |
| Min Voltage | `3299 mV` | `bms_min_cell_mv` | `3296` | `uxJp`[5] |
| Min Voltage Cell Position | `ID:0(32)` | `bms_min_cell_pos` | `32` | `uxJp`[6] |
| Battery Voltage 1–16 | `3301–3306 mV` | `cell_1_mv` … `cell_16_mv` | `3298–3302` | `v09K`[0..15] |
| BMS Charge Current Limit | `195 A` | `bms_charge_current_limit_a` | `195.0` | `Yavb`[4] |
| BMS Charge Voltage Limit | `57.6 V` | `bms_charge_voltage_limit_v` | `57.6` | `Yavb`[3] |
| BMS Discharge Voltage Limit | `42 V` | `bms_discharge_voltage_limit_v` | `42.0` | `Yavb`[2] |
| BMS Current SOC | `39 %` | `bms_current_soc` | `38` | `Yavb`[5] |
| BMS Charging Current | `18.4 A` | `bms_charging_current_a` | `15.9` | `Yavb`[6] |
| BMS Discharge Current | `0 A` | `bms_discharge_current_a` | `0.0` | `Yavb`[7] |
| BMS Low Power SOC | `15 %` | `bms_low_power_soc` | `15` | `93VQ`[10] |
| BMS Returns To Mains Mode SOC | `35 %` | `bms_returns_to_mains_mode_soc` | `35` | `93VQ`[11] |
| BMS Returns To Battery Mode SOC | `50 %` | `bms_returns_to_battery_mode_soc` | `50` | `93VQ`[12] |
| BMS Automatically Starts SOC After Low | `25 %` | `bms_auto_start_soc_after_low` | `25` | `93VQ`[13] |

> **Cell position 32 with a 16-cell list.** The BMS reports its minimum at physical
> position 32 while `v09K` carries only 16 cells — the portal shows the same
> `ID:0(32)`. The pack is 32 cells; the block is a 16-cell window. This is why cell
> min/max come from `uxJp` and never from the `v09K` list.

### Grid

| Portal label | Portal | Bridge key | Bridge | Source |
|---|---|---|---|---|
| AC input voltage | `226.8 V` | `grid_v` | `227.7` | `WdRR`[0] |
| Mains Frequency | `49.9 Hz` | `grid_hz` | `50.0` | `WdRR`[1] |
| Mains Current Flow Direction | `Mains To Inverter` | `mains_current_flow_direction` | *same* | `WdRR`[7] |
| Mains Power | `0 kW` | `mains_power_w` | `0` | `WdRR`[6] |
| High Point Of Mains Power Loss Voltage | `280 V` | `high_point_of_mains_power_loss_voltage_v` | `280.0` | `WdRR`[2] |
| Low Point Of Mains Power Loss Voltage | `170 V` | `low_point_of_mains_power_loss_voltage_v` | `170.0` | `WdRR`[3] |
| High Frequency Of Mains Power Loss | `65 Hz` | `high_frequency_of_mains_power_loss_hz` | `65.0` | `WdRR`[4] |
| Low Frequency Of Mains Power Loss | `40 Hz` | `low_frequency_of_mains_power_loss_hz` | `40.0` | `WdRR`[5] |
| Mains Input Range | `UPS` | `mains_input_range` | `UPS` | `WdRR`[9] |
| Main Output Relay Status | `On` | `main_output_relay_status` | `On` | `WdRR`[8] bit 1 |
| Grid Connection Sign | `Off Grid` | `grid_connection_sign` | `Off Grid` | `93VQ` |
| Grid Connected Current | `20 A` | `grid_connected_current_a` | `20` | `93VQ`[17] |
| Total Number Of Grid Connection | `2` | `total_number_of_grid_connection` | `2` | — |

### Load

| Portal label | Portal | Bridge key | Bridge | Source | |
|---|---|---|---|---|---|
| Output Voltage | `229.3 V` | `out_v` | `229.3` | `2l0E`[0] | exact |
| Output Frequency | `49.9 Hz` | `out_hz` | `50.0` | `2l0E`[1] | |
| Output Apparent Power | `852 VA` | `apparent_va` | `550` | `2l0E`[2] | ⏱ |
| Output Active Power | `0.756 kW` | `load_w` | `410` | `2l0E`[3] | ⏱ **see §6** |
| Output Load Percent | `7 %` | `load_pct` | `5` | `2l0E`[4] | ⏱ |
| Output DC Component | `3` | `output_dc_comp` | `32` | `2l0E`[5] | ⚠ **see §6** |
| Rated Power | `11 kW` | *not published* | — | `2l0E`[6] = `11000` | **newly identified** |
| Inductor Current | `6.9 A` | `inductor_current_a` | `7.5` | `2l0E`[7] | ⏱ |

### PV

| Portal label | Portal | Bridge key | Bridge | Source |
|---|---|---|---|---|
| PV Voltage | `0 V` | `pv_v` | `0.0` | `Mpod`[0] |
| PV Current | `0 A` | `pv_current_a` | `0.0` | `Mpod`[1] |
| PV Power | `0 kW` | `pv_w` | `0` | `Mpod`[2] |
| PV Temperature | `54 °C` | `pv_temp` | `50.0` | `V4W3` ⏱ |
| PV2 Voltage | `146.5 V` | `pv2_v` | `185.0` | `noeP`[0] ⏱ |
| PV2 Current | `5.7 A` | `pv2_current_a` | `4.7` | `noeP`[1] ⏱ |
| PV2 Power | `0.843 kW` | `pv2_power_w` | `873` | `noeP`[2] ⏱ |
| PV2 Temperature | `47 °C` | `pv2_temp` | `45.0` | `V4W3` ⏱ |
| Generation Power | `0.843 kW` | `generation_power_w` | `873` | `pv_w + pv2_power_w` |
| Daily Electricity Generation | `0.967 kWh` | `pv_today_kwh` | `0.967` | `COST`[2] **exact** |
| Monthly Electricity Generation | `328 kWh` | `pv_month_kwh` | `328.0` | `COST`[3] **exact** |
| Yearly Electricity Generation | `2093.3 kWh` | `pv_year_kwh` | `2093.3` | `COST`[4] **exact** |
| Total Electricity Generation | `2296.9 kWh` | `pv_total_kwh` | `2296.9` | `COST`[5] **exact** |
| Solar Charging Switch | `Open` | `solar_charging_switch` | `Open` | derived |

> **PV1 reads zero and that is correct.** The portal shows the same: `PV Voltage 0 V`,
> `PV Current 0 A`, `PV Power 0 kW`, with the live string on PV2. One PV string on the
> second MPPT input.

### Temperatures and fans

| Portal label | Portal | Bridge key | Bridge | Source |
|---|---|---|---|---|
| Boost Temperature | `38 °C` | `boost_temperature_c` | `38.0` | `V4W3`[2] **exact** |
| Inverter Temperature | `50 °C` | `inverter_temperature_c` | `47.0` | `V4W3`[1] ⏱ |
| DC Rectification Temperature | `50 °C` | `dc_rectification_temperature_c` | `49.0` | `V4W3`[9] |
| Transformer Temperature | `60 °C` | `transformer_temperature_c` | `59.0` | `V4W3`[3] |
| Max. Temperature | `60` *(no unit shown)* | `max_temperature_c` | `59.0` | `V4W3`[4] |
| Fan 1 Speed | `30 %` | `fan_1_speed` | `30` | `V4W3`[5] **exact** |
| Fan 2 Speed | `30 %` | `fan_2_speed` | `30` | `V4W3`[6] **exact** |
| Fan 1 Status / Fan 2 Status | `Open` | `fan_1_status` / `fan_2_status` | `Open` | `V4W3`[7] |

### Settings — all exact matches

Every one of these agreed exactly. `93VQ` unless noted.

| Portal label | Value | Bridge key |
|---|---|---|
| Float Charging Voltage | `56.4 V` | `float_charging_voltage_v` |
| Strong Charging Voltage | `56.4 V` | `strong_charging_voltage_v` |
| Low Electric Lock Voltage | `42 V` | `low_electric_lock_voltage_v` |
| Maximum Total Charging Current | `50 A` | `maximum_total_charging_current_a` |
| Max utility charge current | `10 A` | `max_utility_charge_current_a` |
| Output Set Voltage | `230 V` | `output_set_voltage` |
| Output Set Frequency | `50 Hz` | `output_set_frequency` |
| Charging Priority Order | `SNU` | `charging_priority_order` |
| Working Mode | `SBU` | `working_mode` |
| Parallel Mode | `Enable` | `parallel_mode` |
| Parallel Role | `Host` | `parallel_role` |
| AC Charging Switch | `Close` | `ac_charging_switch` |
| Grid Connection Function | `Off` | `grid_connection_function` |
| CT Function Switch | `OFF` | `ct_function_switch` |
| Buzzer Function | `On` | `buzzer_function` |
| ECO | `Off` | `eco` |
| Dual Output Mode | `On` | `dual_output_mode` |
| Does The Machine Have An Output | `Yes` | `does_machine_have_output` |
| Input Source Prompt Function | `On` | `input_source_prompt_function` |
| Automatic Return To The First Page Function | `On` | `automatic_return_to_first_page` |
| Power Supply From PV To Load In AC State | `No` | `power_supply_from_pv_to_load_in_ac_state` |
| Mains Charging Starting/Ending Time | `0 h` | `mains_charging_starting_time` / `_ending_time` |
| Battery Overvoltage Shutdown Voltage | `44 V` | `battery_overvoltage_shutdown_voltage_v` (`dHrK`[1]) |
| Battery Equalization Mode | `Disable` | `battery_equalization_mode` |
| Battery Equalization Voltage | `58.4 V` | `battery_equalization_voltage_v` (`dHrK`[7]) |
| Equalization Time | `60 min` | `equalization_time` (`dHrK`[8]) |
| Equalization Overtime | `120 min` | `equalization_overtime` (`dHrK`[9]) |
| Equalization Interval | `30 day` | `equalization_interval` (`dHrK`[10]) |
| Parallel Mode Turn Off SOC | `20 %` | `parallel_mode_turn_off_soc` (`dHrK`[2]) |
| Parallel Mode Turn Off Voltage | `44 V` | `parallel_mode_turn_off_voltage_v` (`dHrK`[3]) |
| Return To Mains Mode Voltage | `46 V` | `return_to_mains_mode_voltage_v` (`dHrK`[4]) |
| Return To Battery Mode Voltage | `54 V` | `return_to_battery_mode_voltage_v` (`dHrK`[5]) |
| Second Output Battery Voltage | `52 V` | `second_output_battery_voltage_v` (`dHrK`[15]) |
| Second Output Battery Capacity | `50 %` | `second_output_battery_capacity` |
| Second Delay Time | `5 min` | `second_delay_time` (`dHrK`[13]) |
| Second Output Discharge Time | `0 min` | `second_output_discharge_time` |
| Dual Output Starting/Ending Time | `0 h` | `output_starting_time` / `output_ending_time` |

---

## 4. Published by the bridge, absent from the portal

Raw diagnostic artefacts kept deliberately, so a future decode has something to work from.

| Bridge key | Value |
|---|---|
| `yavb_flags_raw` | `1001100000000000` |
| `eo8w_flags_raw` | `B010000000000` |
| `eo8w_blob_raw` | `20211002120B117020000` |
| `yavb_code_raw` / `yavb_aux_raw` | `03041` / `000000` |
| `wdrr_status_bits` / `output_status_bits` | `11000` / `11000` |
| `mains_wdrr_token` / `mains_wdrr_value` / `mains_wdrr_abs` | `+00000` / `0` / `0` |
| `mains_flow_code` / `mains_input_range_code` / `mains_eo8w_code` | `0` / `11` / `B B` |
| `bms_cell_count` / `bms_cell_delta_mv` | `16` / `6` |

---

## 5. What the bridge cannot decode yet

**All of these have live values in the portal.** This is the actionable part of the
document — it turns "undecodable" into a specific search.

### Light and indicator statuses — candidate source `eo8w`[1] = `B010000000000`

| Portal label | Portal value | Bridge key |
|---|---|---|
| Charging Light Status | `Flicker` | `charging_light_status` |
| Inverter Light Status | `Light` | `inverter_light_status` |
| Mains Light Status | `Flicker` | `mains_light_status` |
| Warning Light Status | `Off` | `warning_light_status` |
| LCD Back Lighting | `On` | `lcd_back_lighting` |

Thirteen characters, leading `B`, only two non-zero positions. Five statuses, three of
which are non-`Off`. The `B` prefix and position 3 (`1`) are the obvious starting point.

### BMS flags — candidate source `Yavb`[1] = `1001100000000000`

| Portal label | Portal value | Bridge key |
|---|---|---|
| BMS Allow Charging Flag | `Yes` | `bms_allow_charging_flag` |
| BMS Allow Discharge Flag | `Yes` | `bms_allow_discharge_flag` |
| BMS Communication Normal | `Yes` | `bms_communication_normal` |
| BMS Communication Control Function | `Open` | `bms_communication_control_function` |
| BMS Charging Overcurrent Sign | `No` | `bms_charging_overcurrent_sign` |
| BMS Discharge Overcurrent Flag | `No` | `bms_discharge_overcurrent_flag` |
| BMS Low Battery Alarm Flag | `No` | `bms_low_battery_alarm_flag` |
| BMS Low Power Fault Flag | `No` | `bms_low_power_fault_flag` |
| BMS Low Temperature Flag | `No` | `bms_low_temperature_flag` |
| BMS Temperature Too High Flag | `No` | `bms_temperature_too_high_flag` |
| Battery Not Connected | `No` | `battery_not_connected` |
| Battery Voltage Higher | `No` | `battery_voltage_higher` |

Sixteen bits, set at positions **1, 4, 5** (1-indexed). Twelve flags, four of which are
affirmative in the portal. **Three set bits against four affirmatives — they do not
match**, so a naive one-bit-per-flag reading is wrong. This is exactly why the old preset
was removed: it asserted a mapping that the data does not support.

A second capture in a **different battery state** (discharging, or with an alarm active)
would show which bits move, and is the only way to settle this.

### Fault and function flags — source not yet identified

Candidates: `2ONL`[6] = `110007200000`, `2l0E`[6] = `11000` *(now believed to be rated
power — see §3)*, `93VQ`[3] = `13310110230`, `2ONL`[7] = `00000000`.

| Portal label | Portal value | Bridge key |
|---|---|---|
| Abnormal Fan Speed | `No` | `abnormal_fan_speed` |
| Abnormal Low PV Power | `No` | `abnormal_low_pv_power` |
| Abnormal Temperature Sensor | `No` | `abnormal_temperature_sensor` |
| EEPROM Data Abnormality | `No` | `eeprom_data_abnormality` |
| EEPROM Read Write Exception | `No` | `eeprom_read_write_exception` |
| Input Voltage Too High | `No` | `input_voltage_too_high` |
| Low Battery Alarm | `No` | `low_battery_alarm` |
| Machine Over Temperature | `No` | `machine_over_temperature` |
| OverLoaded | `No` | `overloaded` |
| Overload Restart Function | `Close` | `overload_restart_function` |
| Overload To Bypass Function | `Close` | `overload_to_bypass_function` |
| Over Temperature Restart Function | `Open` | `over_temperature_restart_function` |
| Charging Main Switch | `Open` | `charging_main_switch` |
| MPPT Constant Temperature Mode | `Disable` | `mppt_constant_temperature_mode` |
| Li Battery Activation Function Switch | `Close` | `li_battery_activation_function_switch` |
| Li Battery Activation Process | `Stop` | `li_battery_activation_process` |

Every one of these reads a "safe" value in this capture. **A capture taken during a fault
would be far more informative than another healthy one.**

### Named values — source not yet identified

| Portal label | Portal value | Bridge key | Note |
|---|---|---|---|
| Mode | `Battery Mode` | `mode` | Was a hardcoded string until 2.6.1 |
| Output Model | `PAL` | `output_model` | Matches `Parallel Mode: Enable` |
| Battery Type | `LIA` | `battery_type` | Was a hardcoded string until 2.6.1 |
| PV Energy Feeding Priority | `LBU` | `pv_energy_feeding_priority` | |
| PV Grid Connection Agreement | `3` | `pv_grid_connection_agreement` | |
| BMS Average Temperature | `30.95 °C` | `bms_avg_temp_c` | The bridge logs this in `[UNRESOLVED TARGETS]` every payload |

`Mode`, `Output Model` and `Battery Type` are alphabetic codes like the ones `93VQ`
already yields (`SNU`, `SBU`, `Host`), so `93VQ` is the natural place to look.

`BMS Average Temperature` is a **decimal** value, `30.95` — two decimal places, unlike
every other temperature on the device. That precision is distinctive and should make it
findable.

### Not on the portal either

| Bridge key | Note |
|---|---|
| `util_chg` | Named a "candidate" in the registry; no portal field corresponds |
| `c_bms_remaining_capacity_ah` | A calculated helper that is never populated |

---

## 6. Discrepancies worth investigating

**⚠ `output_dc_comp` — portal `3`, bridge `32`.** Earlier in the same capture the bridge
read `8`. The portal's value is a single digit while the bridge's is two. Possibly a
scale factor, possibly just a fast-moving value at a different instant. Needs a
simultaneous reading to settle.

**⚠ Scaling: the portal does not agree with itself.** At the portal's own instant:

```
PV Panel   0.843 kW
Load       0.756 kW
Grid       0     kW
Battery    53 V × 18.4 A (BMS, whole bank) = 975 W charging
```

Energy in must equal energy out: `PV = Load + Battery charge`, i.e. `843 = 756 + 975`.
That is **not** balanced — it is short by 888 W, almost exactly the PV figure again.

Doubling PV closes it: `1686 = 756 + 975 = 1731`, within 2.6%.

So the portal's **PV figure appears to be per-inverter** while its **Load figure appears
to be the system total** — which is inconsistent, and means the portal cannot be used as
a reference for whether `INVERTER_COUNT` scaling is correct.

The bridge's own energy balance at its own instant does close, using `INVERTER_COUNT=2`
throughout. The exact-match energy counters (`pv_total_kwh` 2296.9, `pv_year_kwh` 2093.3,
`pv_month_kwh` 328.0, `pv_today_kwh` 0.967) confirm the bridge reads the same raw numbers
the portal displays — the open question is only what those raw numbers *count*.

**To settle it:** take a portal screenshot and a bridge log within the same minute, on a
day with meaningful PV production, and compare the four power figures directly.

---

## 7. How to extend this file

1. Set **Debug Flags** to `blocks` and `unparsed_publish`, **Log Level** to `info`, for
   about two minutes, then turn them back off.
2. Read `solar.siseli.com` → device → *Data Overview* within the same minute.
3. Add the `[BLOCK RAW]` lines and the portal values side by side.

The highest-value captures are the ones **not** in a healthy steady state: discharging,
on grid, during an alarm, or with the second PV string live. Every flag in
[section 5](#5-what-the-bridge-cannot-decode-yet) reads its safe value here, so this
capture cannot distinguish them.

Block positions in this project are read positionally with no published schema. A value
is published only when the payload contains evidence for it — which is why the fields in
section 5 read `unknown` rather than a plausible guess.
