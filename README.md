# ☀️ Siseli Inverter Bridge for Home Assistant

[![Version](https://img.shields.io/badge/version-2.6.11-blue.svg)](siseli_bridge/CHANGELOG.md)
[![HA Add-on](https://img.shields.io/badge/Home%20Assistant-Add--on-green.svg)](https://www.home-assistant.io/)

A Home Assistant add-on that reads your Siseli-compatible solar inverter **locally**, by
decoding the telemetry it already sends to the vendor cloud — and publishes it to Home
Assistant through MQTT auto-discovery.

Your inverter keeps talking to the cloud, so the official mobile app carries on working.
The bridge only listens in.

> **Acknowledgment:** an expanded and generalized fork of the original work at
> [yuraantonov11/siseli-ha](https://github.com/yuraantonov11/siseli-ha). Huge thanks to
> the original author.

---

## Contents

- [How it works](#how-it-works)
- [Requirements](#requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [What you get](#what-you-get)
- [Parallel inverters and battery banks](#parallel-inverters-and-battery-banks)
- [Network setup](#network-setup)
- [Troubleshooting](#troubleshooting)
- [Known limitations](#known-limitations)
- [Supported hardware](#supported-hardware)
- [Contributing](#contributing)

---

## How it works

Your inverter's WiFi dongle publishes telemetry over MQTT to the Siseli cloud at
`8.212.18.157:1883`. The add-on:

1. **Puts itself in the path** using ARP interception, so the inverter's packets reach
   the Home Assistant host.
2. **Reassembles the TCP stream** and pulls out the MQTT PUBLISH frames.
3. **Decodes the payload** — base64 blocks keyed by four-character names (`2ONL`, `WdRR`,
   `Yavb`, …), each a list of space-separated values read by position.
4. **Publishes to your broker** with MQTT auto-discovery, so entities appear on their own.
5. **Forwards the traffic onward** to the cloud, unchanged.

It never terminates a connection and never opens a listening socket. It observes, decodes,
and relays.

**What this means in practice:** if the add-on stops, your inverter keeps working and the
vendor app keeps working. You lose the Home Assistant sensors, nothing else.

---

## Requirements

| | |
|---|---|
| **Architecture** | `aarch64` or `amd64`. 32-bit builds (`armv7`, `armhf`, `i386`) are not published — the add-on will not appear in the store on those systems. |
| **Home Assistant** | Supervised or Home Assistant OS. The add-on needs `host_network`, `NET_ADMIN` and `NET_RAW` to capture and inject frames, and runs with AppArmor disabled. |
| **MQTT broker** | Any broker Home Assistant already uses. The [Mosquitto add-on](https://github.com/home-assistant/addons/tree/master/mosquitto) is the usual choice. |
| **Network** | The inverter and Home Assistant must be on the same layer-2 network for ARP interception to work. |

---

## Installation

### 1. Set up MQTT

Install the **Mosquitto broker** add-on if you have not already, and create a Home
Assistant user for the bridge to log in with (**Settings → People → Users → Add user**).
You will need that username and password in step 3.

### 2. Add this repository

**Settings → Add-ons → Add-on Store → ⋮ → Repositories**, then add:

```
https://github.com/fadmaz/siseli-ha
```

### 3. Install and configure

Install **Siseli Inverter Bridge**, open its **Configuration** tab, and set at minimum:

| Option | What to enter |
|---|---|
| `MQTT_USER` / `MQTT_PASSWORD` | The credentials you created in step 1 |
| `INVERTER_IP` | Your inverter's local IP — find it in your router's DHCP client list |
| `ROUTER_IP` | Your router / gateway IP |
| `INVERTER_COUNT` | How many inverters you have, if running in parallel |
| `BATTERY_COUNT` and `BATTERY_CAPACITY_PER_BATTERY_AH` | If you want a configured bank-capacity sensor |

Leave `AUTO_INTERCEPT` on unless you have arranged the traffic yourself — see
[Network setup](#network-setup).

### 4. Start it

Enable **Watchdog** and **Start on boot**, then start the add-on. Within a couple of
minutes the log should show:

```
--- Siseli Inverter Bridge 2.6.11 ---
[ARP] Interception ACTIVE: 192.168.x.x <-> 192.168.x.x
[HA MQTT] Connected to ...
[HA MQTT] Discovery published
[Bridge] Sniffer started
```

Entities appear under **Settings → Devices & Services → MQTT** once the first telemetry
payload arrives. Inverters typically report every few minutes, so give it up to ten
minutes before concluding something is wrong.

---

## Configuration

Every option, with its shipped default. Most installations only need the handful listed
in step 3 above.

### Connection

| Option | Default | Notes |
|---|---|---|
| `MQTT_HOST` | `core-mosquitto` | Use the default with the official Mosquitto add-on |
| `MQTT_PORT` | `1883` | |
| `MQTT_USER` / `MQTT_PASSWORD` | *(blank)* | Leave blank only if your broker allows anonymous access |
| `TARGET_HOST` | `8.212.18.157` | The Siseli cloud. Do not change unless the cloud IP changes |
| `TARGET_PORT` | `1883` | |
| `INVERTER_IP` | `192.168.1.139` | **Must be set to your inverter's real IP** |
| `ROUTER_IP` | `192.168.1.1` | **Must be set to your gateway** |
| `INVERTER_MAC` / `ROUTER_MAC` | *(blank)* | Optional. Pin these if auto-detection picks the wrong device |
| `AUTO_INTERCEPT` | `true` | ARP interception. Turn off only if you route the traffic yourself |
| `SNIFF_IFACE` | *(blank)* | Advanced. Pin the capture interface if auto-detection fails |
| `FORWARD_ALL_INVERTER_TRAFFIC` | `false` | See [the caveat below](#a-caveat-on-forwarding) |

### Identity and scaling

| Option | Default | Notes |
|---|---|---|
| `DEVICE_ID` | `siseli_inverter_1` | Letters, digits, `_` and `-` only. Changing it renames every entity |
| `DEVICE_NAME` | `Siseli Inverter 1` | Shown in Home Assistant |
| `MODEL_NAME` / `MANUFACTURER` | `Siseli Inverter 1` / `Siseli Compatible` | Cosmetic |
| `ENTITY_PREFIX` | `Siseli` | Prefixed to every entity name |
| `INVERTER_COUNT` | `1` | Scales the calculated power sensors — see below |
| `BATTERY_COUNT` | `1` | |
| `BATTERY_CAPACITY_PER_BATTERY_AH` | `0.0` | `0` disables the configured bank-capacity sensor |
| `MQTT_DISCOVERY_PREFIX` | `homeassistant` | Only change for a custom discovery setup |
| `STATE_TOPIC` / `AVAILABILITY_TOPIC` | *(blank)* | Blank derives both from `DEVICE_ID` |
| `MQTT_RETAIN` | `true` | Keeps sensor states across a Home Assistant restart |

### Timing

| Option | Default | Notes |
|---|---|---|
| `UPDATE_INTERVAL_SEC` | `10` | Publish throttle. Raising it saves database storage |
| `EXPIRE_AFTER_SEC` | `1800` | How long a value stays valid before Home Assistant marks it unavailable. `0` disables |
| `TELEMETRY_TIMEOUT_SEC` | `1800` | How long without a decoded reading before the bridge marks sensors unavailable |

These three interact, and the add-on **refuses to start** if they contradict each other:

- `UPDATE_INTERVAL_SEC` must be less than `EXPIRE_AFTER_SEC`
- `TELEMETRY_TIMEOUT_SEC` must not exceed `EXPIRE_AFTER_SEC`, or Home Assistant would
  expire the sensors before the bridge decided they were stale

`TELEMETRY_TIMEOUT_SEC` is also raised automatically at runtime if the bridge measures
your inverter reporting less often than the configured value, so entities cannot flap.

> **If you installed a version before 2.6.6:** Home Assistant pins an option's value the
> first time you save the Configuration page, so an old default can outlive the release
> that changed it. If your entities cycle between available and unavailable, check that
> `TELEMETRY_TIMEOUT_SEC` and `EXPIRE_AFTER_SEC` both read `1800`.

### Diagnostics and maintenance

| Option | Default | Notes |
|---|---|---|
| `LOG_LEVEL` | `info` | `debug` for deep troubleshooting, `warning` for quiet logs |
| `DEBUG_FLAGS` | *(none)* | See [Troubleshooting](#troubleshooting). Requires `LOG_LEVEL` of `info` or `debug` |
| `DISCOVERY_CLEANUP` | `true` | Clears entities left behind by earlier versions that grouped sensors differently |
| `RESET_ENERGY_COUNTERS` | `false` | Zeroes the calculated kWh totals. Turn on, restart once, turn back off |

### Deprecated

`LISTEN_PORT` and `LOG_VERBOSE` are **ignored**. They remain in the schema only so
Supervisor does not reject the stored options on existing installations, and both are
removed in 2.7.0. `LISTEN_PORT` in particular never did anything — the bridge has never
opened a socket. You can ignore the `[CONFIG WARNING]` about it.

---

## What you get

**203 sensors across 7 devices.** 146 are enabled on a fresh install; the rest are
disabled by default and can be switched on individually in Home Assistant.

| Device | Sensors | Covers |
|---|---|---|
| **Main** | 12 | The calculated power and energy sensors, state of charge, mode |
| **Battery** | 45 | Voltage, current, capacity, charge/discharge state, charging setpoints |
| **BMS** | 25 | Per-cell voltages (16), pack min/max/delta, nominal and remaining Ah, limits |
| **Grid** | 30 | Voltage, frequency, flow direction, mains loss thresholds, relay status |
| **Load** | 21 | Active and apparent power, load percentage, output voltage and frequency |
| **PV** | 18 | Per-string voltage/current/power, temperatures, daily/monthly/yearly/total energy |
| **Diagnostics** | 52 | Fan speeds, temperatures, firmware, settings echoes, raw block dumps |

The Battery, BMS, Grid, Load, PV and Diagnostics devices are nested under Main in Home
Assistant, so they appear together on one page.

**Calculated sensors** are prefixed `c_` and are derived rather than read from the wire —
battery charge/discharge power and energy, grid import power and energy, generation power,
load power, and the configured bank capacity. The three `kWh` counters are
`total_increasing`, so they feed the Home Assistant Energy Dashboard directly.

For a value-by-value map against the vendor portal — every block, every token position,
and the exact list of fields the bridge cannot yet decode — see
[`sensor_mapping_verified.md`](sensor_mapping_verified.md). An earlier map is kept at
[`sensor_mapping.md`](sensor_mapping.md).

---

## Parallel inverters and battery banks

Set `INVERTER_COUNT` to the number of inverters sharing the dongle. The inverter reports
per-unit figures, so the calculated sensors scale them:

```
c_load_w             = load_w            × INVERTER_COUNT
c_generation_power_w = generation_power_w × INVERTER_COUNT
c_mains_power_w      = mains_power_w     × INVERTER_COUNT
```

Battery power is handled differently: the BMS reports the **whole bank** already, so it is
used unscaled. When the bridge has to fall back to the inverter's own ammeter it scales
that by `INVERTER_COUNT` instead, so both sources stay on one basis.

A quick sanity check on your own data: generation + battery discharge − battery charge
should roughly equal load. If it does not, `INVERTER_COUNT` is probably wrong.

For the configured bank capacity sensor, set `BATTERY_COUNT` and
`BATTERY_CAPACITY_PER_BATTERY_AH` to the number of packs and the Ah printed on one of
them. Leaving the capacity at `0` disables that sensor. Note it is a **configuration
echo**, not a measurement — your BMS reports its own figure separately.

---

## Network setup

### Method A — ARP interception (default, recommended)

With `AUTO_INTERCEPT: true` the add-on tells the inverter that Home Assistant is the
gateway, and tells the router that Home Assistant is the inverter. Traffic then passes
through the Home Assistant host, where it is decoded and forwarded on.

Nothing else is required. On shutdown the add-on restores both ARP caches so the inverter
goes straight back to the real gateway.

> **Some networks fight this.** UniFi, pfSense/OPNsense and enterprise switches may have
> ARP inspection or IP-source-guard features that block spoofed replies. If interception
> never establishes, use Method B.

#### A caveat on forwarding

By default the bridge relays only the inverter's **broker traffic** to
`TARGET_HOST:TARGET_PORT`. Everything else it sends — DNS, NTP, anything to a secondary
endpoint — is dropped, because the add-on is now the inverter's gateway but is not a
router.

For most inverters this is fine. If yours fails to reconnect, or the health line reports
dropped packets:

```
[HEALTH] Last packet seen 12s ago; ... dropped_non_broker={'udp/53': 40}
```

set `FORWARD_ALL_INVERTER_TRAFFIC: true`.

### Method B — router-side redirect (advanced, unsupported)

Set `AUTO_INTERCEPT: false` and arrange for the inverter's traffic to reach the Home
Assistant host yourself. This works only if all three hold:

1. **The destination IP is preserved.** The bridge matches on
   `TARGET_HOST:TARGET_PORT`, so a NAT or DNS rewrite that changes the destination is
   never matched.
2. **The host forwards packets.** The add-on does not enable `net.ipv4.ip_forward` and
   will not relay anything in this mode. Without forwarding, the inverter loses its cloud
   connection entirely.
3. **The traffic is actually on the wire.** A **switch port mirror (SPAN)** to the Home
   Assistant host is the cleanest way to satisfy all of this, and is fully passive.

> **A DNS override does not work.** Pointing the Siseli domain at Home Assistant produces
> nothing, because there is no listener — the bridge observes traffic, it does not
> terminate it. The inverter's connection simply fails.

---

## Troubleshooting

### No entities appear

- Check the log for `[HA MQTT] Connected` and `[HA MQTT] Discovery published`. If the
  connection fails, the MQTT credentials are wrong.
- Check for `[ARP] Interception ACTIVE`. If it never appears, the MAC addresses could not
  be resolved — set `INVERTER_MAC` and `ROUTER_MAC` manually.
- The health line every 30 seconds reports which MACs the bridge is seeing:
  `[HEALTH] Last packet seen 12s ago; inverter_macs=[...]`. If `inverter_macs` is empty,
  no inverter traffic is reaching the capture — check `INVERTER_IP`, or pin `SNIFF_IFACE`.

### Entities go unavailable and come back

Check that `TELEMETRY_TIMEOUT_SEC` and `EXPIRE_AFTER_SEC` are both `1800` on the
Configuration page. Values stored by an older release are not updated by an upgrade.

### Energy Dashboard totals look wrong

If the totals are inflated or were accumulated by a version before 2.6.7, set
`RESET_ENERGY_COUNTERS` to `true`, restart the add-on once, then set it back to `false`.

### PV1 reads zero on a single-string system

Expected. Some inverters report the live string on the second MPPT input, and the official
app shows the same split. `c_generation_power_w` sums both, so the total is still correct.

### Your inverter is not decoded

Set **Debug Flags** to `blocks` and `unparsed_publish`, and **Log Level** to `info`, for
about two minutes — then turn them back off, because the output is per-packet. Open an
issue with the [unsupported inverter template](.github/ISSUE_TEMPLATE/unsupported_inverter.yml)
and attach the `[BLOCK RAW]` lines.

> **Scrub your log before posting it.** The `topic=` values contain your device serial.

---

## Known limitations

**Around 38 sensors read `Unknown` and cannot be decoded.** Earlier versions filled them
with hardcoded constants — fault flags that could never report a fault, a `Mode` that was
a fixed string in the source. Those were removed in 2.6.1. The entities remain, disabled
by default, and publish an explicit "no value" rather than a comforting lie. If your
inverter emits blocks that would decode them, an issue with a capture is welcome.

**Two current sources disagree, and there is no way to tell which is right.** The BMS and
the inverter's own ammeter can differ by a factor of two or more, in either direction. The
official app displays both and they disagree there too. The bridge uses the BMS figure and
logs `[ENERGY SOURCE DISAGREEMENT]` when the two diverge, rather than silently picking a
winner. Settling this needs a clamp meter on the DC bus.

**Block positions were reverse-engineered from one device.** There is no published schema.
Values are read by position from blocks whose meaning was inferred. Where a position was
not understood, nothing is published.

---

## Supported hardware

Anything using the Siseli IoT cloud platform, which includes inverters sold as:

Solar of Things · LUMINOUS NEO · SUN WISE · Queen Tech · LIB Life · Sun house · LeiLing ·
SunSaviour · ECOmenic · HC solar · 沐能低碳 · PowMr · Taico

**Verified in detail:** one device — `HPVINV04`, firmware `0010.11`, two inverters in
parallel with a 32-cell battery bank. Its captures are byte-faithful fixtures in the test
suite, and the decoded values are checked against the official app.

Other brands on that list are reported to work but are not covered by captures. If you
have one, a debug capture is the single most useful contribution you can make — see
[Troubleshooting](#your-inverter-is-not-decoded).

---

## Contributing

Development setup, test conventions, how to add a capture from your own inverter, and the
release checklist are in [`CONTRIBUTING.md`](CONTRIBUTING.md).

Release history is in [`siseli_bridge/CHANGELOG.md`](siseli_bridge/CHANGELOG.md), which
Home Assistant also renders on the add-on's **Changelog** tab.

Bug reports: use the [issue templates](.github/ISSUE_TEMPLATE/). Always include your
add-on version and a scrubbed log — this project's experience is that almost every real
defect was found by running it on someone's hardware, not by reading the code.

---

## License

MIT. Free to use and modify.
