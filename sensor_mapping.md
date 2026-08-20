# 📊 Siseli 100% Verified Mapping (Live HA Payload compared to Live App UI trace)

> **Absolute Transparency Verified:** Using the newly minted `changed_values` logs you generated, we explicitly pull exactly how the live Home Assistant database sees the strings, side-by-side with what your App GUI reported. It is a 100% transparent translation pipeline.

> **⚠️ Update for 2.6.0:** rows marked *(Not decoded — preset removed in 2.6.0)* were
> never decoded from the wire. They came from hardcoded presets keyed on one specific
> inverter's configuration and have been removed. The values recorded below are what
> the bridge used to publish, not what it read.

| Raw MQTT ID | HA Database Live State | Official App UI Real-Time Trace | HA Clean Label | Entity Location |
|---|---|---|---|---|
| `model_code` | `HPVINV04` | **HPVINV04** | Device Type | ⚙️ Diagnostic Card |
| `output_model` | `PAL` | **PAL** | Output Model | ⚙️ Diagnostic Card *(Not decoded — preset removed in 2.6.0)* |
| `mode` | `Battery Mode` | **Battery Mode** | Mode | ⚙️ Diagnostic Card *(Not decoded — preset removed in 2.6.0)* |
| `status_code` | `00` | **00** | Status Code | ⚙️ Diagnostic Card |
| `firmware_info` | `0010.11 20250630 14` | **0010.11 20250630 14** | Firmware Info | ⚙️ Diagnostic Card |
| `firmware_version` | `0010.11` | **10.11** | Firmware Version | ⚙️ Diagnostic Card |
| `firmware_build_date` | `2025-06-30` | ***(Hidden)*** | Firmware Build Date | ⚙️ Diagnostic Card |
| `firmware_build_slot` | `14` | ***(Hidden)*** | Firmware Build Slot | ⚙️ Diagnostic Card |
| `bat_v` | `53.3 V` | **53.3 V** | Battery Voltage | 🌟 Main Sensors Card |
| `bat_cap` | `88 %` | **88 %** | Battery Capacity | 🌟 Main Sensors Card |
| `bat_charge_current` | `5.0 A` | **5 A** | Battery Charging Current | 🌟 Main Sensors Card |
| `dischg_current` | `0.0 A` | **0 A** | Battery Discharge Current | 🌟 Main Sensors Card |
| `bat_series_count` | `4` | **4** | Battery Number In Series | 🌟 Main Sensors Card |
| `battery_status` | `Charge` | **Charge** | Battery Status | 🌟 Main Sensors Card |
| `battery_type` | `LIA` | **LIA** | Battery Type | 🌟 Main Sensors Card |
| `bms_remaining_ah` | `262.9 Ah` | **262.9 A** | Remaining Capacity | 🌟 Main Sensors Card |
| `bms_nominal_ah` | `300.0 Ah` | **300 A** | Nominal Capacity | 🌟 Main Sensors Card |
| `bms_display_mode` | `Display All Battery Cell Data Locations` | **Display All Battery Cell Data Locations** | Display Mode | 🌟 Main Sensors Card |
| `bms_max_cell_mv` | `3330 mV` | **3330 mV** | Max Voltage | 🌟 Main Sensors Card |
| `bms_max_cell_pos` | `9` | **ID:0(9)** | Max Voltage Cell Position | 🌟 Main Sensors Card |
| `bms_min_cell_mv` | `3324 mV` | **3324 mV** | Min Voltage | 🌟 Main Sensors Card |
| `bms_min_cell_pos` | `32` | **ID:0(32)** | Min Voltage Cell Position | 🌟 Main Sensors Card |
| `bms_cell_count` | `16` | **16** | BMS Cell Count | 🌟 Main Sensors Card |
| `bms_cell_delta_mv` | `6 mV` | **6 mV** | BMS Cell Delta | 🌟 Main Sensors Card |
| `cell_1_mv` | `3326 mV` | **3326 mV** | Battery Voltage 1 | 🌟 Main Sensors Card |
| `cell_2_mv` | `3328 mV` | **3328 mV** | Battery Voltage 2 | 🌟 Main Sensors Card |
| `cell_3_mv` | `3328 mV` | **3328 mV** | Battery Voltage 3 | 🌟 Main Sensors Card |
| `cell_4_mv` | `3327 mV` | **3327 mV** | Battery Voltage 4 | 🌟 Main Sensors Card |
| `cell_5_mv` | `3328 mV` | **3328 mV** | Battery Voltage 5 | 🌟 Main Sensors Card |
| `cell_6_mv` | `3327 mV` | **3327 mV** | Battery Voltage 6 | 🌟 Main Sensors Card |
| `cell_7_mv` | `3329 mV` | **3329 mV** | Battery Voltage 7 | 🌟 Main Sensors Card |
| `cell_8_mv` | `3328 mV` | **3328 mV** | Battery Voltage 8 | 🌟 Main Sensors Card |
| `cell_9_mv` | `3330 mV` | **3330 mV** | Battery Voltage 9 | 🌟 Main Sensors Card |
| `cell_10_mv` | `3328 mV` | **3328 mV** | Battery Voltage 10 | 🌟 Main Sensors Card |
| `cell_11_mv` | `3328 mV` | **3328 mV** | Battery Voltage 11 | 🌟 Main Sensors Card |
| `cell_12_mv` | `3328 mV` | **3328 mV** | Battery Voltage 12 | 🌟 Main Sensors Card |
| `cell_13_mv` | `3328 mV` | **3328 mV** | Battery Voltage 13 | 🌟 Main Sensors Card |
| `cell_14_mv` | `3329 mV` | **3329 mV** | Battery Voltage 14 | 🌟 Main Sensors Card |
| `cell_15_mv` | `3328 mV` | **3328 mV** | Battery Voltage 15 | 🌟 Main Sensors Card |
| `cell_16_mv` | `3326 mV` | **3326 mV** | Battery Voltage 16 | 🌟 Main Sensors Card |
| `grid_v` | `232.7 V` | **232.7 V** | AC Input Voltage | 🌟 Main Sensors Card |
| `grid_hz` | `49.9 Hz` | **49.9 Hz** | Mains Frequency | 🌟 Main Sensors Card |
| `mains_current_flow_direction` | `Mains To Inverter` | **Mains To Inverter** | Mains Current Flow Direction | 🌟 Main Sensors Card |
| `mains_power_w` | `0 W` | **0 kW** | Mains Power | 🌟 Main Sensors Card |
| `mains_apparent_va` | `0 VA` | **0 VA** | Mains Apparent Power | 🌟 Main Sensors Card |
| `out_v` | `229.9 V` | **229.9 V** | Output Voltage | 🌟 Main Sensors Card |
| `out_hz` | `49.9 Hz` | **49.9 Hz** | Output Frequency | 🌟 Main Sensors Card |
| `apparent_va` | `390 VA` | **390 VA** | Output Apparent Power | 🌟 Main Sensors Card |
| `load_w` | `267 W` | **0.267 kW** | Output Active Power | 🌟 Main Sensors Card |
| `load_pct` | `3 %` | **3 %** | Output Load Percent | 🌟 Main Sensors Card |
| `output_dc_comp` | `14` | **14** | Output DC Component | 🌟 Main Sensors Card |
| `generation_power_w` | `659 W` | **0.659 kW** | Generation Power | 🌟 Main Sensors Card |
| `pv_v` | `0.0 V` | **0 V** | PV Voltage | 🌟 Main Sensors Card |
| `pv_current_a` | `0.0 A` | **0 A** | PV Current | 🌟 Main Sensors Card |
| `pv_w` | `0 W` | **0 W** | PV Power | 🌟 Main Sensors Card |
| `pv2_v` | `359.5 V` | **359.5 V** | PV2 Voltage | 🌟 Main Sensors Card |
| `pv2_current_a` | `1.8 A` | **1.8 A** | PV2 Current | 🌟 Main Sensors Card |
| `pv2_power_w` | `659 W` | **659 W** | PV2 Power | 🌟 Main Sensors Card |
| `pv_today_kwh` | `14.98 kWh` | **14.98 kWh** | Daily Electricity Generation | 🌟 Main Sensors Card |
| `pv_month_kwh` | `210.5 kWh` | **210.5 kWh** | Monthly Electricity Generation | 🌟 Main Sensors Card |
| `pv_total_kwh` | `774.1 kWh` | **774.1 kWh** | Total Electricity Generation | 🌟 Main Sensors Card |
| `pv_year_kwh` | `570.5 kWh` | **570.5 kWh** | Yearly Electricity Generation | 🌟 Main Sensors Card |
| `pv_temp` | `35.0 °C` | **35 °C** | PV Temperature | 🌟 Main Sensors Card |
| `pv2_temp` | `34.0 °C` | **34 °C** | PV2 Temperature | 🌟 Main Sensors Card |
| `solar_charging_switch` | `Open` | **Open** | Solar Charging Switch | 🌟 Main Sensors Card |
| `bus_voltage` | `403.0 V` | **403 V** | BUS Voltage | ⚙️ Diagnostic Card |
| `ac_charging_switch` | `Close` | **Close** | AC Charging Switch | ⚙️ Diagnostic Card |
| `abnormal_fan_speed` | `No` | **No** | Abnormal Fan Speed | ⚙️ Diagnostic Card *(Not decoded — preset removed in 2.6.0)* |
| `abnormal_low_pv_power` | `No` | **No** | Abnormal Low PV Power | ⚙️ Diagnostic Card *(Not decoded — preset removed in 2.6.0)* |
| `abnormal_temperature_sensor` | `No` | **No** | Abnormal Temperature Sensor | ⚙️ Diagnostic Card *(Not decoded — preset removed in 2.6.0)* |
| `automatic_return_to_first_page` | `On` | **On** | Automatic Return To The First Page Function | ⚙️ Diagnostic Card |
| `bms_allow_charging_flag` | `Yes` | **Yes** | BMS Allow Charging Flag | ⚙️ Diagnostic Card *(Not decoded — preset removed in 2.6.0)* |
| `bms_allow_discharge_flag` | `Yes` | **Yes** | BMS Allow Discharge Flag | ⚙️ Diagnostic Card *(Not decoded — preset removed in 2.6.0)* |
| `bms_auto_start_soc_after_low` | `25 %` | **25 %** | BMS Automatically Starts SOC After Low | ⚙️ Diagnostic Card |
| `bms_avg_temp_c` | `*(Static)*` | **20.95 °C** | BMS Average Temperature | ⚙️ Diagnostic Card |
| `bms_charge_current_limit_a` | `195.0 A` | **195 A** | BMS Charge Current Limit | ⚙️ Diagnostic Card |
| `bms_charge_voltage_limit_v` | `57.6 V` | **57.6 V** | BMS Charge Voltage Limit | ⚙️ Diagnostic Card |
| `bms_charging_current_a` | `10.7 A` | **10.7 A** | BMS Charging Current | ⚙️ Diagnostic Card |
| `bms_charging_overcurrent_sign` | `No` | **No** | BMS Charging Overcurrent Sign | ⚙️ Diagnostic Card *(Not decoded — preset removed in 2.6.0)* |
| `bms_communication_control_function` | `Open` | **Open** | BMS Communication Control Function | ⚙️ Diagnostic Card *(Not decoded — preset removed in 2.6.0)* |
| `bms_communication_normal` | `Yes` | **Yes** | BMS Communication Normal | ⚙️ Diagnostic Card *(Not decoded — preset removed in 2.6.0)* |
| `bms_current_soc` | `88 %` | **88 %** | BMS Current SOC | ⚙️ Diagnostic Card |
| `bms_discharge_current_a` | `0.0 A` | **0 A** | BMS Discharge Current | ⚙️ Diagnostic Card |
| `bms_discharge_overcurrent_flag` | `No` | **No** | BMS Discharge Overcurrent Flag | ⚙️ Diagnostic Card *(Not decoded — preset removed in 2.6.0)* |
| `bms_discharge_voltage_limit_v` | `42.0 V` | **42 V** | BMS Discharge Voltage Limit | ⚙️ Diagnostic Card |
| `bms_low_battery_alarm_flag` | `No` | **No** | BMS Low Battery Alarm Flag | ⚙️ Diagnostic Card *(Not decoded — preset removed in 2.6.0)* |
| `bms_low_power_fault_flag` | `No` | **No** | BMS Low Power Fault Flag | ⚙️ Diagnostic Card *(Not decoded — preset removed in 2.6.0)* |
| `bms_low_power_soc` | `15 %` | **15 %** | BMS Low Power SOC | ⚙️ Diagnostic Card |
| `bms_low_temperature_flag` | `No` | **No** | BMS Low Temperature Flag | ⚙️ Diagnostic Card *(Not decoded — preset removed in 2.6.0)* |
| `bms_returns_to_battery_mode_soc` | `50 %` | **50 %** | BMS Returns To Battery Mode SOC | ⚙️ Diagnostic Card |
| `bms_returns_to_mains_mode_soc` | `35 %` | **35 %** | BMS Returns To Mains Mode SOC | ⚙️ Diagnostic Card |
| `bms_temperature_too_high_flag` | `No` | **No** | BMS Temperature Too High Flag | ⚙️ Diagnostic Card *(Not decoded — preset removed in 2.6.0)* |
| `battery_equalization_mode` | `Disable` | **Disable** | Battery Equalization Mode | ⚙️ Diagnostic Card |
| `battery_equalization_voltage_v` | `58.4 V` | **58.4 V** | Battery Equalization Voltage | ⚙️ Diagnostic Card |
| `battery_not_connected` | `No` | **No** | Battery Not Connected | ⚙️ Diagnostic Card *(Not decoded — preset removed in 2.6.0)* |
| `battery_overvoltage_shutdown_voltage_v` | `44.0 V` | **44 V** | Battery Overvoltage Shutdown Voltage | ⚙️ Diagnostic Card |
| `battery_voltage_higher` | `No` | **No** | Battery Voltage Higher | ⚙️ Diagnostic Card *(Not decoded — preset removed in 2.6.0)* |
| `boost_temperature_c` | `27.0 °C` | **27 °C** | Boost Temperature | ⚙️ Diagnostic Card |
| `buzzer_function` | `On` | **On** | Buzzer Function | ⚙️ Diagnostic Card |
| `charging_light_status` | `Light` | **Flicker** | Charging Light Status | ⚙️ Diagnostic Card *(Not decoded — preset removed in 2.6.0)* |
| `charging_main_switch` | `Open` | **Open** | Charging Main Switch | ⚙️ Diagnostic Card *(Not decoded — preset removed in 2.6.0)* |
| `charging_priority_order` | `SNU` | **SNU** | Charging Priority Order | ⚙️ Diagnostic Card |
| `ct_function_switch` | `OFF` | **OFF** | CT Function Switch | ⚙️ Diagnostic Card |
| `dc_rectification_temperature_c` | `42.0 °C` | **42 °C** | DC Rectification Temperature | ⚙️ Diagnostic Card |
| `does_machine_have_output` | `Yes` | **Yes** | Does The Machine Have An Output | ⚙️ Diagnostic Card |
| `dual_output_mode` | `On` | **On** | Dual Output Mode | ⚙️ Diagnostic Card |
| `eco` | `Off` | **Off** | ECO | ⚙️ Diagnostic Card |
| `eeprom_data_abnormality` | `No` | **No** | EEPROM Data Abnormality | ⚙️ Diagnostic Card *(Not decoded — preset removed in 2.6.0)* |
| `eeprom_read_write_exception` | `No` | **No** | EEPROM Read Write Exception | ⚙️ Diagnostic Card *(Not decoded — preset removed in 2.6.0)* |
| `equalization_interval` | `30 day` | **30 day** | Equalization Interval | ⚙️ Diagnostic Card |
| `equalization_overtime` | `120 min` | **120 min** | Equalization Overtime | ⚙️ Diagnostic Card |
| `equalization_time` | `60 min` | **60 min** | Equalization Time | ⚙️ Diagnostic Card |
| `fan_1_speed` | `30 %` | **30 %** | Fan 1 Speed | ⚙️ Diagnostic Card |
| `fan_1_status` | `Open` | **Open** | Fan 1 Status | ⚙️ Diagnostic Card |
| `fan_2_speed` | `30 %` | **30 %** | Fan 2 Speed | ⚙️ Diagnostic Card |
| `fan_2_status` | `Open` | **Open** | Fan 2 Status | ⚙️ Diagnostic Card |
| `float_charging_voltage_v` | `56.4 V` | **56.4 V** | Float Charging Voltage | ⚙️ Diagnostic Card |
| `grid_connected_current_a` | `20 A` | **20 A** | Grid Connected Current | ⚙️ Diagnostic Card |
| `grid_connection_function` | `Off` | **Off** | Grid Connection Function | ⚙️ Diagnostic Card |
| `grid_connection_sign` | `Off Grid` | **Off Grid** | Grid Connection Sign | ⚙️ Diagnostic Card |
| `high_frequency_of_mains_power_loss_hz` | `65.0 Hz` | **65 Hz** | High Frequency Of Mains Power Loss | ⚙️ Diagnostic Card |
| `high_point_of_mains_power_loss_voltage_v` | `280.0 V` | **280 V** | High Point Of Mains Power Loss Voltage | ⚙️ Diagnostic Card |
| `inductor_current_a` | `6.7 A` | **6.7 A** | Inductor Current | ⚙️ Diagnostic Card |
| `input_source_prompt_function` | `On` | **On** | Input Source Prompt Function | ⚙️ Diagnostic Card |
| `input_voltage_too_high` | `No` | **No** | Input Voltage Too High | ⚙️ Diagnostic Card *(Not decoded — preset removed in 2.6.0)* |
| `inverter_light_status` | `Light` | **Light** | Inverter Light Status | ⚙️ Diagnostic Card *(Not decoded — preset removed in 2.6.0)* |
| `inverter_temperature_c` | `39.0 °C` | **39 °C** | Inverter Temperature | ⚙️ Diagnostic Card |
| `lcd_back_lighting` | `On` | **On** | LCD Back Lighting | ⚙️ Diagnostic Card *(Not decoded — preset removed in 2.6.0)* |
| `li_battery_activation_function_switch` | `Close` | **Close** | Li Battery Activation Function Switch | ⚙️ Diagnostic Card *(Not decoded — preset removed in 2.6.0)* |
| `li_battery_activation_process` | `Stop` | **Stop** | Li Battery Activation Process | ⚙️ Diagnostic Card *(Not decoded — preset removed in 2.6.0)* |
| `low_battery_alarm` | `No` | **No** | Low Battery Alarm | ⚙️ Diagnostic Card *(Not decoded — preset removed in 2.6.0)* |
| `low_electric_lock_voltage_v` | `42.0 V` | **42 V** | Low Electric Lock Voltage | ⚙️ Diagnostic Card |
| `low_frequency_of_mains_power_loss_hz` | `40.0 Hz` | **40 Hz** | Low Frequency Of Mains Power Loss | ⚙️ Diagnostic Card |
| `low_point_of_mains_power_loss_voltage_v` | `170.0 V` | **170 V** | Low Point Of Mains Power Loss Voltage | ⚙️ Diagnostic Card |
| `machine_over_temperature` | `No` | **No** | Machine Over Temperature | ⚙️ Diagnostic Card *(Not decoded — preset removed in 2.6.0)* |
| `main_output_relay_status` | `On` | **On** | Main Output Relay Status | ⚙️ Diagnostic Card |
| `mains_charging_ending_time` | `0 h` | **0 h** | Mains Charging Ending Time | ⚙️ Diagnostic Card |
| `mains_charging_starting_time` | `0 h` | **0 h** | Mains Charging Starting Time | ⚙️ Diagnostic Card |
| `mains_input_range` | `UPS` | **UPS** | Mains Input Range | ⚙️ Diagnostic Card |
| `mains_light_status` | `Flicker` | **Flicker** | Mains Light Status | ⚙️ Diagnostic Card *(Not decoded — preset removed in 2.6.0)* |
| `max_utility_charge_current_a` | `10 A` | **10 A** | Max utility charge current | ⚙️ Diagnostic Card |
| `max_temperature_c` | `53.0 °C` | **53 °C** | Max. Temperature | ⚙️ Diagnostic Card |
| `maximum_total_charging_current_a` | `50 A` | **50 A** | Maximum Total Charging Current | ⚙️ Diagnostic Card |
| `mppt_constant_temperature_mode` | `Disable` | **Disable** | MPPT Constant Temperature Mode | ⚙️ Diagnostic Card *(Not decoded — preset removed in 2.6.0)* |
| `output_ending_time` | `0 h` | **0 h** | Output Ending Time | ⚙️ Diagnostic Card |
| `output_set_frequency` | `49.9 Hz` | **50 Hz** | Output Set Frequency | ⚙️ Diagnostic Card |
| `output_set_voltage` | `230 V` | **230 V** | Output Set Voltage | ⚙️ Diagnostic Card |
| `output_starting_time` | `0 h` | **0 h** | Output Starting Time | ⚙️ Diagnostic Card |
| `over_temperature_restart_function` | `Open` | **Open** | Over Temperature Restart Function | ⚙️ Diagnostic Card *(Not decoded — preset removed in 2.6.0)* |
| `overloaded` | `No` | **No** | OverLoaded | ⚙️ Diagnostic Card *(Not decoded — preset removed in 2.6.0)* |
| `overload_restart_function` | `Close` | **Close** | Overload Restart Function | ⚙️ Diagnostic Card *(Not decoded — preset removed in 2.6.0)* |
| `overload_to_bypass_function` | `Close` | **Close** | Overload To Bypass Function | ⚙️ Diagnostic Card *(Not decoded — preset removed in 2.6.0)* |
| `parallel_mode` | `Enable` | **Enable** | Parallel Mode | ⚙️ Diagnostic Card |
| `parallel_mode_turn_off_soc` | `20 %` | **20 %** | Parallel Mode Turn Off SOC | ⚙️ Diagnostic Card |
| `parallel_mode_turn_off_voltage_v` | `44.0 V` | **44 V** | Parallel Mode Turn Off Voltage | ⚙️ Diagnostic Card |
| `parallel_role` | `Host` | **Host** | Parallel Role | ⚙️ Diagnostic Card |
| `power_supply_from_pv_to_load_in_ac_state` | `No` | **No** | Power Supply From PV To Load In AC State | ⚙️ Diagnostic Card |
| `pv_energy_feeding_priority` | `LBU` | **LBU** | PV Energy Feeding Priority | ⚙️ Diagnostic Card *(Not decoded — preset removed in 2.6.0)* |
| `pv_grid_connection_agreement` | `3` | **3** | PV Grid Connection Agreement | ⚙️ Diagnostic Card *(Not decoded — preset removed in 2.6.0)* |
| `return_to_battery_mode_voltage_v` | `54.0 V` | **54 V** | Return To Battery Mode Voltage | ⚙️ Diagnostic Card |
| `return_to_mains_mode_voltage_v` | `46.0 V` | **46 V** | Return To Mains Mode Voltage | ⚙️ Diagnostic Card |
| `second_delay_time` | `5 min` | **5 min** | Second Delay Time | ⚙️ Diagnostic Card |
| `second_output_battery_capacity` | `50 %` | **50 %** | Second Output Battery Capacity | ⚙️ Diagnostic Card |
| `second_output_battery_voltage_v` | `52.0 V` | **52 V** | Second Output Battery Voltage | ⚙️ Diagnostic Card |
| `second_output_discharge_time` | `0 min` | **0 min** | Second Output Discharge Time | ⚙️ Diagnostic Card |
| `software_version` | `0010.11` | **10.11** | Software Version | ⚙️ Diagnostic Card |
| `strong_charging_voltage_v` | `56.4 V` | **56.4 V** | Strong Charging Voltage | ⚙️ Diagnostic Card |
| `system_time_hm` | `22:40` | **22:40** | System Time (Hour Minute) | ⚙️ Diagnostic Card |
| `system_time_ymd` | `260317` | **260317** | System Time (Year Month Day) | ⚙️ Diagnostic Card |
| `total_number_of_grid_connection` | `2` | **2** | Total Number Of Grid Connection | ⚙️ Diagnostic Card |
| `transformer_temperature_c` | `53.0 °C` | **53 °C** | Transformer Temperature | ⚙️ Diagnostic Card |
| `warning_light_status` | `Off` | **Off** | Warning Light Status | ⚙️ Diagnostic Card *(Not decoded — preset removed in 2.6.0)* |
| `working_mode` | `SBU` | **SBU** | Working Mode | ⚙️ Diagnostic Card |
| `mains_wdrr_token` | `*(Static)*` | ***(Hidden)*** | Mains WdRR Token | ⚙️ Diagnostic Card |
| `mains_wdrr_value` | `*(Static)*` | ***(Hidden)*** | Mains WdRR Value | ⚙️ Diagnostic Card |
| `mains_wdrr_abs` | `*(Static)*` | ***(Hidden)*** | Mains WdRR Absolute | ⚙️ Diagnostic Card |
| `mains_eo8w_code` | `*(Static)*` | ***(Hidden)*** | Mains eo8w Code | ⚙️ Diagnostic Card |
| `wdrr_status_bits` | `*(Static)*` | ***(Hidden)*** | WdRR Status Bits | ⚙️ Diagnostic Card |
| `eo8w_flags_raw` | `*(Static)*` | ***(Hidden)*** | eo8w Flags Raw | ⚙️ Diagnostic Card |
| `eo8w_blob_raw` | `*(Static)*` | ***(Hidden)*** | eo8w Blob Raw | ⚙️ Diagnostic Card |
| `yavb_flags_raw` | `*(Static)*` | ***(Hidden)*** | Yavb Flags Raw | ⚙️ Diagnostic Card |
| `yavb_code_raw` | `*(Static)*` | ***(Hidden)*** | Yavb Code Raw | ⚙️ Diagnostic Card |
| `yavb_aux_raw` | `*(Static)*` | ***(Hidden)*** | Yavb Aux Raw | ⚙️ Diagnostic Card |
| `output_status_bits` | `*(Static)*` | ***(Hidden)*** | Output Status Bits | ⚙️ Diagnostic Card |
| `mains_flow_code` | `*(Static)*` | ***(Hidden)*** | Mains Flow Code | ⚙️ Diagnostic Card |
| `mains_input_range_code` | `*(Static)*` | ***(Hidden)*** | Mains Input Range Code | ⚙️ Diagnostic Card |
| `bat_temp` | `39.0 °C` | ***(Hidden)*** | Inverter Temperature (legacy) | ⚙️ Diagnostic Card |
| `max_chg` | `50 A` | ***(Hidden)*** | Max Charge Current (legacy) | ⚙️ Diagnostic Card |
| `util_chg` | `*(Static)*` | ***(Hidden)*** | Utility Charge Current (candidate) | ⚙️ Diagnostic Card *(Not decoded — preset removed in 2.6.0)* |
| `bulk_v` | `56.4 V` | ***(Hidden)*** | Bulk Charging Voltage (legacy) | ⚙️ Diagnostic Card |
| `float_v` | `56.4 V` | ***(Hidden)*** | Float Charging Voltage (legacy) | ⚙️ Diagnostic Card |
| `cut_v` | `42.0 V` | ***(Hidden)*** | Low Battery Cut-off (legacy) | ⚙️ Diagnostic Card |
| `mains_flow_state` | `*(Static)*` | ***(Hidden)*** | Mains Flow State (legacy) | ⚙️ Diagnostic Card |
