# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

## [2.6.5] - 2026-08-20

### Fixed

- **Every Sensor Flapped To Unavailable And Back**: `TELEMETRY_TIMEOUT_SEC` shipped at 180 seconds while inverters report every 300 seconds, with gaps of 600 observed. The watchdog therefore fired before every single payload, so all sensors cycled to Unavailable and back continuously. Both it and `EXPIRE_AFTER_SEC` now default to 1800 seconds, and startup validation rejects a timeout longer than the expiry window.
- **The Heartbeat Could Not Fire When It Was Needed**: The republish that keeps Home Assistant's expiry window fresh ran inside the payload parser, so it only happened when a payload arrived -- precisely when it was not required. It is now driven by the watchdog timer and runs regardless of inverter traffic.
- **Fabricated Values Survived In The State Cache**: Removing the hardcoded sensor presets in 2.6.0 stopped the bridge generating them but left the ones already written to `/data/state.json`, which were restored and republished on every start. On a live installation `mode` still read `Battery Mode` three releases after the code that invented it was deleted. Cached values with no decode path are now discarded on load and reported.

### Added

- **Test Environment Drift Guard**: The test suite's stand-in for Supervisor's options is now asserted to match the shipped defaults. It had drifted, which made the flapping bug above appear fixed or broken depending on test order.

## [2.6.4] - 2026-08-20

### Fixed

- **Battery Status Contradicted The Power Reading**: `battery_status` was derived from the inverter's own ammeter while the calculated power sensors used the BMS. On a live installation the two disagreed in the same publish -- the status read `Idle` alongside 344 W flowing into the battery. It is now derived from the calculated power, so the two cannot contradict each other.
- **Disagreement Warning Missed The Clearest Case**: `[ENERGY SOURCE DISAGREEMENT]` compared the two current sources by ratio, which cannot express one source reading zero while the other reports current -- exactly the case that produced the contradiction above. It now reports that too.

### Added

- **Container Smoke Test**: CI now starts the built image and waits for it to report a running sniffer, failing if the process exits first. Two releases shipped broken because a passing test suite and a successful image build were both consistent with an add-on that could not start.

## [2.6.3] - 2026-08-20

### Fixed

- **Add-on Crash-Looped On Start**: 2.6.2 raised `NameError: name '_debug' is not defined` before the sniffer started, restarting continuously without ever publishing. `from .config import *` does not import names beginning with an underscore, so the private helper the startup banner called was never available. The computed flag list is now exported as `ACTIVE_DEBUG_FLAGS`.

### Added

- **Startup Path Coverage**: The startup banner was inline in the `__main__` body, which no test executes, so the crash shipped with a passing suite and a clean lint run. It is now a module-level function with tests that run it, plus a check that no module referencing `from .config import *` uses a private name from that module. `ruff` could not have caught this: `core.py` carries an `F405` exemption because the star import is load-bearing, and `F405` is the rule that would have flagged it.

## [2.6.2] - 2026-08-20

### Fixed

- **Update Blocked By The Add-on's Own Defaults**: 2.6.1 added a MAC address pattern to `INVERTER_MAC` and `ROUTER_MAC`, both of which ship blank. Home Assistant validates stored options before installing an update and an empty string is a present value, so it had to satisfy the pattern and did not -- blocking the upgrade on every installation with `App ... has invalid options: does not match regular expression`. The pattern now accepts a blank value, which is what the trailing `?` was mistakenly assumed to cover.
- **Removed Option Blocked The Update**: `LISTEN_PORT` was deleted from the schema in 2.6.1 while existing installations still carry it in their stored options. It is restored as an optional, unused key with a deprecation warning, and will be removed in 2.7.0 once stored copies no longer contain it.

### Added

- **Schema Regression Guard**: Tests now assert that every shipped default satisfies its own schema declaration, and replay a real stored configuration through the schema. Either check would have caught both faults above before release.

## [2.6.1] - 2026-08-20

### Fixed

- **Options The UI Accepted But The Add-on Rejected**: Port numbers, MAC addresses, the discovery prefix and the update interval are now bounded in the add-on schema to exactly what the code enforces, so an invalid value is reported on the options page instead of leaving the add-on in a restart loop.
- **Device ID No Longer Drove Nothing**: `STATE_TOPIC` and `AVAILABILITY_TOPIC` shipped literal defaults naming `siseli_inverter_1`, so Supervisor always supplied them and changing `DEVICE_ID` did not move the topics. Both now default to blank and are derived from the device id; an explicitly set topic still wins.
- **Invalid MQTT Topics Are Rejected**: A topic containing `+` or `#` is a protocol violation that makes the broker close the connection, which the client then retries in a loop. Startup validation now catches it.

### Added

- **Debug Flags**: A single multi-select option replaces ten diagnostic switches that had no add-on option at all, so from the UI they were previously either all on (via `LOG_LEVEL: debug`) or all off. It is now possible to enable just `unparsed_publish`, which is what an unsupported inverter needs, without also turning on the per-packet trace.
- **Issue Templates**: Reporting an unsupported inverter now asks for the debug capture whose block lines become test fixtures, and reminds the reporter to scrub the cloud topic, which contains their device serial.

### Changed

- **Verbose Logging Is Off By Default**: `LOG_VERBOSE` shipped enabled and was documented as deprecated in the same breath, so a fresh installation wrote a log line for every captured frame without anyone asking. It is now ignored entirely, with a deprecation warning, and will be removed in 2.7.0. Use `DEBUG_FLAGS` with `xray` (every frame) or `packets` (reassembled MQTT packets).
- **Interception Documentation Corrected**: The README described a DNS-override method that cannot work -- the bridge observes traffic rather than terminating it, so there is no listener for a redirected connection to reach. It is replaced by the requirements a router-side redirect actually has, and by switch port mirroring, which needs no code at all and is the right answer for networks that block ARP interception.
- **`LISTEN_PORT` Removed**: It was exported, validated and described in the UI as the port the add-on listens on. Nothing ever opened a socket; its only consumer was a startup log line.
- **One Changelog**: `siseli_bridge/CHANGELOG.md` is canonical. The root file, which duplicated it by hand and had already drifted, now points at it.

### Removed

- **Dead Code**: `sanitize_block_key` had no call sites, and `_apply_dynamic_debug` took a state parameter it never touched.
- **Deprecated Architectures**: Dropped `armhf`, `armv7` and `i386` from the supported architecture list. Home Assistant removed support for all three in release 2025.12, so no installation that can run current Home Assistant is affected.

## [2.6.0] - 2026-08-20

### Fixed

- **Removed Fabricated Sensor Presets**: Deleted three hardcoded blocks that filled in ~37 sensors whenever a raw value matched one specific inverter's settings. Twelve BMS alarm flags (`bms_temperature_too_high_flag`, `bms_communication_normal` and others) and eight fault indicators (`overloaded`, `machine_over_temperature`, `low_battery_alarm`, `input_voltage_too_high`, `eeprom_data_abnormality`, `abnormal_fan_speed` and others) were constants in the source, not readings, and were structurally incapable of ever reporting a fault. They now report `unknown` until a real decode exists.
- **Fabricated Battery Type And Charge Status**: `battery_type` was set to `LIA` merely because a `Yavb` block was present, and `battery_status` reported `Charge` from a payload carrying no battery data at all. `battery_status` now also reports `Idle` when both currents are known and zero.
- **Sensor Value Collisions**: Six keys had two writers and the last block parsed won. `dc_rectification_temperature_c` decoded to 117.5 C from one block and 51.0 C from another; `grid_connected_current_a` was receiving a state-of-charge percentage into a sensor declared in amps; one `dHrK` token was written to both the charging start and end time. Each now has a single writer.
- **Main Output Relay Off State**: `main_output_relay_status` could only ever read `On` -- the off case produced a null that was stripped before publishing.
- **Overload Percentage Visibility**: `load_pct` above 100 % was discarded, so an overloaded inverter kept showing its last normal reading.
- **Cell Index Alignment**: A cell voltage outside the valid range was skipped rather than stopping the run, silently renumbering every later cell so `cell_3_mv` reported physical cell 4.
- **BMS Cell Summary Source**: The min/max/delta summary is taken from the BMS's own whole-bank figures instead of being recomputed from the 16 cells this block carries, which described only part of a larger pack.
- **Energy Calculation Freshness**: The calculated power and energy sensors are gated per domain and only run on payloads that actually carry the inputs. A payload with no battery data used to publish a changed battery energy total, integrating a cached current indefinitely.
- **Energy Counter Poisoning**: `bms_charging_current_a` and `bms_discharge_current_a` are range-checked like every other current. Unbounded input multiplied by voltage and accumulated into a `total_increasing` sensor could never be corrected downward.
- **Energy Fallback Scaling**: The inverter-reported current fallback is scaled by `INVERTER_COUNT` like every other calculated sensor, instead of silently switching basis when the BMS block was absent.
- **Publish Interval Enforcement**: `UPDATE_INTERVAL_SEC` now actually throttles. The previous condition published on any change, so the option never suppressed anything despite being documented as saving database storage. Changes inside the window are deferred, never dropped.
- **Unparsed Payload Detection**: A payload with no recognised blocks now reports failure. Every payload previously reported success because the calculated sensors were always written, which also made the unparsed-payload diagnostics unreachable.
- **Availability Coverage**: Every entity now watches the bridge's last-will topic. Previously availability was published per sensor group, but MQTT allows one will, so a broker disconnect marked only the twelve main-group entities unavailable while the other ~191 kept showing their last values as though they were live.
- **Stale Value Detection**: Availability is driven by the age of the last decoded reading, with an `expire_after` backstop on every discovery payload. Nothing previously aged a value out, so a bridge that stopped receiving data left every sensor frozen at its last reading indefinitely.
- **MQTT Thread Safety**: Shared state is snapshotted under a lock, and exceptions inside the MQTT callbacks are contained. A dictionary resize during a reconnect could raise inside a paho callback and silently kill the network thread, after which the add-on kept parsing and logging while publishing nothing.
- **Stream Reassembly Recovery**: Out-of-order segments are capped and time-limited, and a stalled flow resynchronises instead of waiting forever. A single segment the sniffer missed used to stop all sensor updates permanently, because the real receiver had already acknowledged it so no retransmission ever came.
- **Sequence Wraparound**: TCP sequence numbers are compared with serial arithmetic, so a 32-bit wrap no longer makes every subsequent segment look like a duplicate.
- **Connection Lifecycle**: SYN, FIN and RST are honoured, so a reconnect reusing the same socket pair no longer inherits the previous connection's sequence state.
- **Frame Validation**: Non-PUBLISH MQTT packets are validated per control type, with reserved flag bits, exact lengths and minimal length encoding enforced. After any desync the parser previously accepted arbitrary bytes as frames and consumed the genuine telemetry queued behind them.
- **State Cache Integrity**: `/data/state.json` is written atomically and no more than once every 30 seconds. A kill mid-write left invalid JSON, which the loader turned into an empty state, silently zeroing every cumulative energy counter.
- **Shutdown Restores ARP**: Stopping the add-on now sends corrective ARP replies to both the inverter and the router. Both caches previously stayed poisoned until they aged out, leaving the inverter unable to reach the cloud for that whole window.
- **MAC Learning**: The bridge recognises its own re-emitted frames and records learned addresses only after the identity check, so it no longer reports its own MAC as both an inverter and a router address.
- **Device Identifier Validation**: `DEVICE_ID` is sanitised for Home Assistant's discovery matcher, which accepts only letters, digits, underscores and hyphens. A value containing a space previously created zero entities with nothing logged anywhere; a `+` or `#` caused the broker to close the connection in a retry loop. Case is preserved, so every working identifier is unchanged.

### Added

- **Sensor Expiry**: New `EXPIRE_AFTER_SEC` option (default 600). Sensors are republished on a heartbeat well inside this window so a steady inverter cannot look stale.
- **Reset Calculated Energy Counters**: New `RESET_ENERGY_COUNTERS` option zeroes the calculated energy totals on the next start, for installations whose counters were inflated by the bug above. Turn on, restart once, turn off.
- **Energy Source Disagreement Warning**: When the BMS and inverter both report a battery current and they differ by more than 2x, the bridge logs both instead of silently picking one. There is no ground truth -- the official app displays both and they disagree too.
- **Corrupt Counter Detection**: Invalid or negative energy counters in the cached state are dropped on load rather than restored.
- **Test Infrastructure**: Added shared test helpers and real captured inverter blocks as fixtures, first-ever coverage for `mqtt.py` and `core.py`, packaging and option-wiring guards, and `ruff` linting. Coverage rose from 52 % to 80 %.
- **Automatic Discovery Cleanup**: Stale retained discovery topics left by earlier sensor groupings are cleared on the first start, so the manual broker cleanup previously documented in the README is no longer needed. Controlled by `DISCOVERY_CLEANUP`.
- **Telemetry Timeout**: New `TELEMETRY_TIMEOUT_SEC` option (default 180) sets how long without a decoded reading before sensors are marked unavailable.
- **Optional Full Traffic Forwarding**: New `FORWARD_ALL_INVERTER_TRAFFIC` option relays inverter traffic other than broker data, such as DNS and NTP, which ARP interception otherwise blackholes. Off by default.
- **Dropped Packet Visibility**: The health line reports non-broker inverter packets that were dropped, broken down by protocol and port, so the option above can be judged from evidence.

### Changed

- **Configured Capacity Naming**: `c_bms_total_capacity_ah` is now "Configured Battery Bank Capacity". It echoes `BATTERY_COUNT` x `BATTERY_CAPACITY_PER_BATTERY_AH`, and read as a BMS measurement it contradicted the BMS's own reported capacity.
- **Undecodable Sensors Disabled By Default**: The 38 sensors with no decode path are marked disabled so they no longer clutter a fresh installation. They stay declared, so a future decode reuses the same entity.
- **Packaging Metadata Corrected**: `pip install .` works; the declared build backend did not exist and the package list was missing, which produced an empty wheel.

## [2.5.24] - 2026-03-30

### Fixed

- **Logging Level Enforcement**: Implemented level-aware logging so `LOG_LEVEL=error` suppresses routine informational/debug logs while preserving error output.
- **Debug Block Noise**: Converted parser debug block output (`[DEBUG BLOCK]`) to debug-level logging so it no longer appears at warning/error levels.
- **Severity Alignment**: Tagged runtime and MQTT lifecycle logs with explicit severities for consistent filtering behavior.

### Added

- **Logging Regression Tests**: Added `tests/test_logging.py` coverage for level filtering and always-on critical error logging behavior.

## [2.5.23] - 2026-03-30

### Fixed

- **App Parity (BMS Temp)**: Added guarded parsing for `bms_avg_temp_c` from extended `Yavb` payloads to reduce `null` values when the inverter provides the field.
- **App Parity (Charging Light)**: Updated preset fallback for `charging_light_status` from `Light` to `Flicker` to match observed app behavior.
- **App Parity (Output Set Frequency)**: Normalized `output_set_frequency` display to app-style integer setpoint representation (example: `49.9` -> `50`).
- **App Parity (Software Version)**: Normalized `software_version` display format (example: `0010.11` -> `10.11`) while preserving raw firmware token in `firmware_version`.

### Changed

- **README Refresh**: Expanded README with a "What is New" section and clearer add-on usage notes.
- **Add-on Info Documentation Link**: Added add-on `url` metadata so the Home Assistant add-on page points directly to the project README.

## [2.5.22] - 2026-03-30

### Changed

- **Battery Power Calculation**: `c_battery_charge_power_w` and `c_battery_discharge_power_w` are no longer scaled by `INVERTER_COUNT`; they reflect the per-inverter BMS reading directly (`bat_v × current_a`).

## [2.5.21] - 2026-03-30

### Changed

- **Calculated Sensor Device Routing**: All calculated sensors (`c_*`) are now grouped under the Main logical device.
- **Grouping Rule Simplification**: Main grouping now uses a prefix rule (`c_`) for calculated sensors, reducing manual key maintenance.

### Fixed

- **Grouping Consistency Tests**: Updated grouping tests to enforce that all calculated sensors resolve to Main.

## [2.5.20] - 2026-03-29

### Added

- **Energy Dashboard Battery Sensors**: Added calculated battery charge/discharge power and cumulative energy sensors (`c_battery_charge_power_w`, `c_battery_discharge_power_w`, `c_battery_charge_energy_kwh`, `c_battery_discharge_energy_kwh`) for Home Assistant Energy Dashboard use.
- **Energy Dashboard Grid Sensor**: Added calculated grid import power/energy sensors (`c_grid_import_power_w`, `c_grid_import_energy_kwh`) for grid consumption tracking.

### Changed

- **Energy Integration Logic**: Parser now computes battery/grid energy counters from power over elapsed time, scales by `INVERTER_COUNT`, and keeps counters monotonic as `total_increasing` values suitable for Energy Dashboard.
- **Test Coverage Expansion**: Added parser/sensor tests for calculated energy metadata, grouping, scaling, and accumulation behavior.

## [2.5.19] - 2026-03-29

### Fixed

- **Topology Config Export**: `run.sh` now exports `INVERTER_COUNT`, `BATTERY_COUNT`, and `BATTERY_CAPACITY_PER_BATTERY_AH` from add-on options so runtime no longer falls back to defaults.
- **Startup Version Consistency**: Updated launcher banner to `2.5.19` to match add-on and runtime version metadata.

### Changed

- **Startup Diagnostics**: Added explicit startup logging for battery topology values (`BATTERY_COUNT` and `BATTERY_CAPACITY_PER_BATTERY_AH`).

## [2.5.18] - 2026-03-29

### Changed

- **Release Version Bump**: Updated project and add-on version metadata to `2.5.18` for this release.

## [2.5.17] - 2026-03-29

### Changed

- **Startup Config Visibility**: Add-on startup logs now explicitly print `INVERTER_COUNT` so calculated `c_` power scaling configuration can be confirmed immediately in logs.

## [2.5.16] - 2026-03-29

### Changed

- **Main Device Sensor Layout**: `Mode` and `BMS Current SOC` are now published without diagnostic category so they appear in the Main `Sensors` card.
- **Main Summary Scaling**: Calculated main sensors `c_generation_power_w`, `c_mains_power_w`, and `c_load_w` now scale by `INVERTER_COUNT` for parallel inverter setups, while raw power sensors remain unscaled.

### Added

- **Parallel Topology Config**: Added `INVERTER_COUNT`, `BATTERY_COUNT`, and `BATTERY_CAPACITY_PER_BATTERY_AH` options with startup validation and UI translations.
- **Calculated Capacity Helper**: Added `c_bms_total_capacity_ah` main sensor computed from battery configuration.

### Fixed

- **CI Dependency Install Quoting**: Quoted pip version specifiers in `.github/workflows/ci.yml` so bash does not interpret `<` as shell redirection during dependency installation.

## [2.5.14] - 2026-03-29

### Changed

- **Main Summary Device**: The root HA device now publishes five key summary sensors (Mains Power, Output Active Power, PV Generation Power, Mode, BMS Current SOC) directly on the root `DEVICE_ID` with no `via_device` indirection.
- **Sensor Name Shortening**: Section prefixes (`Battery Status - `, `Load Status - `, etc.) are stripped from entity display names since sensors are already grouped by device card.

## [2.5.13] - 2026-03-29

### Changed

- **Home Assistant Device Split**: MQTT discovery now groups entities into multiple logical devices (`Battery`, `BMS`, `Grid`, `Load`, `PV`, `Diagnostics`) instead of one overloaded device.
- **Functional Diagnostics Routing**: Sensors from the app's "More" section are mapped by function (battery/grid/pv/load) when possible, with fallback to `Diagnostics`.
- **Per-Group MQTT Topics**: Discovery `state_topic` and `availability_topic` are now section-specific, and runtime publishes are routed per sensor group.
- **Shutdown Availability Handling**: Bridge shutdown now marks all grouped device availability topics offline.

### Added

- Added sensor grouping helpers in `sensors.py` and grouping validation tests in `tests/test_sensors.py`.

## [2.5.12] - 2026-03-29

### Added

- **Startup Config Validation**: Added `validate_config()` in `config.py` — validates IP addresses, port ranges (1–65535), non-empty hosts, and `UPDATE_INTERVAL_SEC ≥ 1` before any threads start. All errors are collected and reported together; the process exits immediately on misconfiguration.
- **Bounded TCP Flow State**: Added `_evict_stale_flows()` in `parsers.py`; called automatically every 200 flow-state lookups via an internal counter. Stale `FLOW_STATES` entries (inactive > `STREAM_STALE_SECONDS`) are pruned to prevent unbounded memory growth during long runs.
- **Shared State Module**: Introduced `state.py` to hold `LAST_STATE`, `DISCOVERY_PUBLISHED`, and `PUBLISHED_SENSOR_KEYS`. Eliminated the circular `parsers ↔ mqtt` dependency and the fragile `_get_mqtt_globals()` deferred-import shim.
- **CI Pipeline**: Added `.github/workflows/ci.yml` running `pytest` on Python 3.9, 3.11, and 3.12 on every push and pull request to `main`.
- **Python Project Metadata**: Added `pyproject.toml` with `requires-python = ">=3.9"`, pytest path configuration, and dev dependency extras (`pytest`, `pytest-cov`).
- **Expanded Tests**: Added `tests/test_config.py` (10 tests for `validate_config`) and `tests/test_flow_eviction.py` (7 tests for TCP flow eviction and `TcpFlowState.reset`). Total test count: 26.

### Fixed

- **Silent Cache Write Failure**: Replaced `except Exception: pass` on `STATE_CACHE_FILE` writes with `log(f"[CACHE WRITE ERROR] {exc}")` so disk/permissions failures appear in the add-on log.
- **Version String Deduplication**: Introduced `VERSION` constant in `core.py`; startup log now uses it instead of a repeated literal. `config.yaml` remains the single release-version source of truth.

## [2.5.11] - 2026-03-26

- Centralized `STATE_CACHE_FILE` in `config.py` for easier maintenance
- Cleaned up top-level imports in `parsers.py` (moved `os`, `json` to module level)
- Added `tests/test_sensors.py` automated validation suite for 220+ sensors
- Removed dynamic debug entities from HA Diagnostics; moved to add-on log stream

## [2.5.10] - 2026-03-26

- Added missing `mqtt_type_name()` function to `parsers.py`
- Moved `LAST_PUBLISH_TS` to `parsers.py` (cross-module `global` fix)

## [2.5.9] - 2026-03-26

- Fixed Dockerfile to use pinned `requirements.txt` instead of hardcoded packages
- Fixed circular import crash between `parsers.py` and `mqtt.py` via deferred imports
- Fixed 20+ missing name references in `parsers.py` (`json`, `datetime`, `log`, `SENSORS`, etc.)
- Fixed missing `mqtt_type_name` and `SEEN_MQTT_TOPICS` imports in `core.py`
- Added `MODEL_NAME` and `MANUFACTURER` exports to `run.sh`
- Removed duplicate cell sensor definitions in `sensors.py`
- Added `state.json` persistence write after every state update
- Created `.dockerignore` to reduce image size
- Cleaned up stray `import re` in `config.py`
- Removed unused `datetime` import from `core.py`

## [2.5.8] - 2026-03-26

### Changed

- **Modular Architecture**: Broke the 2000-line `siseli_bridge.py` monolith into a clean Python package (`src/siseli_bridge/`) with six focused modules: `config.py`, `loggers.py`, `sensors.py`, `parsers.py`, `mqtt.py`, and `core.py`. Each module has a single clear responsibility.
- **State Persistence**: State is now written to `/data/state.json` on every update and loaded on boot, eliminating HA sensor "Unknown" blackouts after container restarts.
- **Unit Test Framework**: Added `tests/test_parsers.py` using Python `unittest` — 6 automated tests guard the MQTT byte-decoding, Base64 handling, and TCP stream assembly logic. All pass.
- **Type Safety**: Added `# pyre-ignore-all-errors` pragma to `parsers.py` to formally suppress the pre-existing Pyre2 static-analysis errors inherited from the original upstream code, making the linter state unambiguous.

## [2.5.7] - 2026-03-26

### Changed

- **Enhanced Add-on Logging**: Upgraded the fundamental MQTT publish console output. Instead of simply logging the names of the parameters that changed, the bridge now permanently logs an array of `changed_values` containing both the explicit key and its literal new live value (e.g. `bat_v=54.5`) directly into the Home Assistant Add-on log stream!

## [2.5.6] - 2026-03-26

### Added

- **100% Data Parity**: Forensically cross-referenced the hardware's native app strings against our MQTT backend payload mappings. Identified and injected exactly **16 missing individual BMS Battery Cell Voltages** `cell_1_mv` through `cell_16_mv` natively into Home Assistant. The backend and the front-end App are now 100% completely matched!

## [2.5.5] - 2026-03-26

### Fixed

- Fixed a dictionary syntax error missing trailing commas in `siseli_bridge.py`.
- Synchronized internal python logging script version string to automatically match the add-on's release metadata.

## [2.5.4] - 2026-03-26

### Changed

- **Massive UI Decluttering**: Leveraged Home Assistant's `entity_category: diagnostic` feature to aggressively collapse all 60+ Advanced Hardware Settings and System Identity codes into a dedicated, minimized 'Diagnostic' card. The main 'Sensors' dashboard is now perfectly clean and only shows critical core metrics (Battery stats, Solar Wattage, etc.).

## [2.5.3] - 2026-03-26

### Changed

- **Sensor UI Categorization**: Dynamically injected string categories (e.g., _Battery Status, PV Panel Status, Grid Status_) to all 130+ Home Assistant entities. This allows the native Home Assistant Device UI to automatically sort and visually group related sensors together instead of displaying a massive randomized list.

## [2.5.2] - 2026-03-26

### Added

- **Configuration UI Localization**: Implemented native Home Assistant translation files (`en.yaml`), replacing raw backend variables with beautiful, user-friendly labels and helper descriptions directly inside the Add-on Configuration tab.

## [2.5.1] - 2026-03-26

### Added

- **Smart Configuration**: Added `LOG_LEVEL` (debug, info, warning) to dynamically control console output natively from the Home Assistant add-on UI.
- **Database Throttling**: Added `UPDATE_INTERVAL_SEC` to selectively throttle Home Assistant MQTT updates, dramatically reducing recorder database sizes.
- **Persistence Toggle**: Exposed `MQTT_RETAIN` boolean toggle to `config.yaml` to allow control over entity memory across reboot cycles.
- Added `ENTITY_PREFIX` UI parameter to support multi-inverter setups natively without entity ID collisions.

## [2.5.0] - 2026-03-25

### Changed

- **Generalization Overhaul**: Fully rebranded `powmr_bridge` to `siseli_bridge`.
- Decoupled hardcoded "PowMr" and "Taico" hardware references in favor of generic variables supporting 13+ sister brands (LUMINOUS NEO, SunSaviour, ECOmenic, etc).
- Consolidated fragmented setup instructions (`DOCS.md`) directly into a unified `README.md`.
- Default MQTT Discovery base topic changed from `powmr/` to `siseli/`.
- Updated repository metadata structure to support `fadmaz/siseli-ha`.

## [1.8.0] - 2026-03-05

### Added

- **Full Autonomous L2 Bridge**: Implemented a software switch that routes ALL inverter traffic (DNS, NTP, etc.) through HA.
- Fixed inverter "no internet" issue by manually forwarding non-MQTT packets to the real router.
- Added `DROP` rules in HA kernel to prevent system interference with bridged packets.
- Real-time Ethernet frame routing using Scapy.

## [1.7.0] - 2026-03-05

### Added

- **Autonomous Proxy Mode (MITM)**: Switched to a full Man-in-the-Middle proxy.
- HA now actively manages the connection between the Inverter and Siseli Cloud.
- Fixed data loss issue caused by HA kernel dropping transit packets.
- Implemented surgical `iptables` redirection restricted to the Inverter's source IP.

## [1.6.2] - 2026-03-05

### Fixed

- Re-implemented strict source IP filtering (`-s $INVERTER_IP`) in `iptables` to prevent intercepting internal HA traffic.
- Added background heartbeat (ping) to keep the inverter connection alive and ARP table warm.
- Enhanced proxy logging to show the actual IP of the connected device.

## [1.6.1] - 2026-03-05

### Added

- **Diagnostic Proxy Logging**: Added real-time tracking of data packets between Inverter and Cloud.
- Hex dump of incoming traffic to identify protocol issues.
- Added `iptables -F` to ensure a clean redirection state on startup.

## [1.6.0] - 2026-03-05

### Added

- **Transparent Proxy Mode**: Implemented a duplicator that forwards inverter traffic to Siseli Cloud while parsing data for Home Assistant.
- Fixed packet loss issue where HA would drop forwarded traffic due to read-only `ip_forward`.
- Dual-path data flow: Inverter -> HA (Proxy) -> Siseli Cloud.

## [1.5.1] - 2026-03-05

### Fixed

- Improved JSON payload detection in TCP packets (robust against MQTT headers).
- Broadened sniffer filters to capture traffic even if destination IP is modified by the router.
- Cleaned up legacy router firewall rules recommendation.

## [1.5.0] - 2026-03-05

### Added

- **Universal Mode**: Combined ARP Spoofing with Passive Packet Sniffing.
- No longer depends on `iptables` or router reconfiguration.
- Automatic discovery watchdog to keep Home Assistant sensors updated.
- Detailed capture logging for real-time status.

## [1.4.1] - 2026-03-05

### Added

- **Router-Assisted Mode**: Optimized the bridge to work with external port redirection (e.g., from OpenWrt).
- Restored active proxy server on port 18899.
- Removed ARP spoofing and sniffing logic to improve stability when using router-level NAT.

## [1.4.0] - 2026-03-05

### Changed

- Switched to **Direct Packet Capture Mode** using Scapy Sniffing.
- Removed all `iptables` and NAT redirection logic for maximum compatibility with HAOS/Docker.
- Implemented real-time packet parsing directly from the network interface.

## [1.3.0] - 2026-03-05

### Added

- Implemented Inverter Heartbeat (ICMP ping) to monitor connectivity.
- Enhanced Traffic Watchdog to capture ALL IP traffic from Inverter (TCP, UDP, ICMP).
- Added port 8080 to redirection rules.
- Explicit discovery logging for each sensor.

## [1.2.9] - 2026-03-05

### Added

- Implemented Traffic Watchdog (passive sniffer) to monitor inverter network activity and detect target ports.
- Added support for port 8883 (MQTT over SSL) redirection.
- Added `iptables -F` to ensure a clean state before applying new rules.

## [1.2.8] - 2026-03-05

### Fixed

- Added `iptables` rule cleanup loop to remove legacy redirection rules on startup.
- Implemented strict source IP filtering for port redirection to avoid intercepting HA internal traffic.
- Added verification log for active redirection rules.

## [1.2.7] - 2026-03-05

### Fixed

- Added `-s $INVERTER_IP` to `iptables` rule to avoid intercepting internal HA traffic.
- Added explicit logging for MQTT Discovery publication.
- Enhanced proxy logging to show data transfer size and direction.

## [1.2.6] - 2026-03-05

### Fixed

- Changed `iptables` rule from `-A` (Append) to `-I` (Insert) to ensure redirection takes priority over Docker rules.
- Added connection logging `[PROXY] New connection` to verify traffic interception.
- Corrected version string in Python bridge output.

## [1.2.5] - 2026-03-05

### Fixed

- Simplified `iptables` redirection to use the default binary (removed legacy reference).
- Confirmed successful ARP Spoofing and device discovery.

## [1.2.4] - 2026-03-05

### Fixed

- Fixed `unbound variable` crash in `run.sh` by reordering config export.
- Automatic network interface detection (`conf.iface`) for Scapy ARP operations.
- Suppressed non-fatal errors when setting `ip_forward` on read-only filesystems.

## [1.2.3] - 2026-03-05

### Added

- Verbose Debug Mode for network diagnostics.
- Detailed error reporting for `iptables` and `ip_forward`.
- Enhanced logging in `powmr_bridge.py` for ARP and Proxy operations.

## [1.2.2] - 2026-03-05

### Added

- Manual MAC address configuration for Inverter and Router in Add-on options.
- `privileged` mode with `NET_ADMIN` and `NET_RAW` capabilities.
- `apparmor: false` to allow advanced network operations.
- Restored SBU configuration sensors (`sbu_return_grid`, `sbu_return_bat`).

## [1.2.1] - 2026-03-05

### Added

- Detailed network and capability diagnostics in `run.sh`.
- `libcap` and `iproute2` packages for advanced network troubleshooting.
- Redirection error logging to `/tmp/ipt_err`.

## [1.2.0] - 2026-03-05

### Fixed

- Switched to `iptables-legacy` for better compatibility with Home Assistant OS.
- Improved ARP Spoofing reliability using `Ether` frames and `sendp`.
- Enabled unbuffered Python output (`-u`) for real-time logging.
- Restored configuration via Home Assistant Add-on options (environment variables).

## [1.1.7] - 2026-03-05

### Added

- Silenced Scapy library warnings in logs to provide cleaner output.

## [1.1.6] - 2026-03-05

### Fixed

- Fatal crash during startup caused by direct writes to `/proc/sys/net/ipv4/ip_forward` on Read-only filesystems in Home Assistant.
- Removed unnecessary `sysctl` calls as local `REDIRECT` does not require system-wide IP forwarding.

## [1.1.5] - 2026-03-05

### Fixed

- Added robust error handling in `run.sh` to prevent crashes on read-only OS filesystems.
- Added warnings about "Protection Mode" in logs if network redirection fails.

## [1.1.2] - 2026-03-05

### Fixed

- Docker build failure caused by PEP 668 in modern Alpine Linux (Home Assistant base images).
- Added `--break-system-packages` flag to `pip3 install` to allow global package installation in containers.

## [1.1.1] - 2026-03-05

### Added

- English documentation and README.
- Versioning support for Home Assistant Add-on Store.
- This CHANGELOG file.

### Fixed

- Docker build process for Home Assistant OS.
- Line ending issues (`run.sh` CRLF/LF) causing build failures on Windows-to-Linux deployments.
- Repository structure to comply with Home Assistant requirements.

## [1.1.0] - 2026-03-05

### Added

- ARP Spoofing support for automatic traffic interception.
- `iptables` redirection logic to capture inverter data without router changes.
- In-container network management (IP forwarding).

## [1.0.0] - 2026-03-05

### Added

- Initial bridge logic for PowMr RWB1 inverters.
- MQTT Auto-Discovery for Home Assistant sensors.
- Basic proxy server for Siseli cloud interception.
