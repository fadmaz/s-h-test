# ☀️ Siseli Solar Cloud Home Assistant Bridge

[![Version](https://img.shields.io/badge/version-2.6.8-blue.svg)](CHANGELOG.md)
[![HA Add-on](https://img.shields.io/badge/Home%20Assistant-Add--on-green.svg)](https://www.home-assistant.io/)

> **Acknowledgment:** This project is an expanded and generalized fork of the excellent work originally created at [yuraantonov11/siseli-ha](https://github.com/yuraantonov11/siseli-ha). Huge thanks to the original author!

Unleash your Siseli-compatible inverter into Home Assistant — **100% locally and instantly** — without relying on external clouds for HA data. The bridge intercepts MQTT traffic to the Siseli Cloud, decodes it locally, and creates sensors via MQTT Auto-Discovery.

> **🔒 Privacy Note:** Your Home Assistant instance intercepts the data for local use, but it simultaneously transparently forwards the traffic to the Siseli Cloud. This ensures your official mobile app continues to work flawlessly.

---

## ✨ What is New (2.6.0)

**This release removes sensors that were never read from your inverter.**

Three blocks of the parser filled in around 37 sensors with hardcoded values whenever
a raw field matched one specific inverter's configuration. That included twelve BMS
alarm flags and eight fault indicators — `overloaded`, `machine_over_temperature`,
`low_battery_alarm` and others — which were literal `"No"` strings in the source code.
They could not report a fault under any circumstances. `mode` on the Main card was
likewise the fixed string `"Battery Mode"`.

Those sensors now report **Unknown**. That is not a regression: the previous value was
not a reading. They stay in place, disabled by default on new installations, so that a
future real decode brings them back with the same entity.

Also fixed:

- **Overload is now visible.** Output load above 100 % was being discarded, so an
  overloaded inverter kept showing its last normal reading.
- **The output relay can report Off.** It could previously only ever read `On`.
- **Energy counters can no longer be poisoned.** BMS currents are range-checked, and
  the calculated energy sensors only run on payloads that actually carry battery data.
  A payload with no battery readings at all used to keep integrating a cached current.
- **Six sensors had two sources disagreeing.** One temperature decoded as 117.5 °C from
  one block and 51.0 °C from another; a state-of-charge percentage was being written
  into a sensor measured in amps.
- **`UPDATE_INTERVAL_SEC` now actually throttles.** It previously published on every
  change, so the option did nothing despite being documented as saving database storage.
- **Cell voltages no longer shift.** A collapsed cell used to renumber every cell after
  it, so `cell_3_mv` would show physical cell 4.

### If your energy totals look too high

The calculated energy sensors are `total_increasing`, so an inflated value can never
correct itself downward. Turn on **Reset Calculated Energy Counters**, restart the
add-on once, then turn it back off.

### New options

- **Sensor Expiry (`EXPIRE_AFTER_SEC`)** — how long a value stays valid before Home
  Assistant marks it unavailable. Default 600 seconds.
- **Reset Calculated Energy Counters (`RESET_ENERGY_COUNTERS`)** — see above.


## 📘 Add-on Page Documentation

The add-on **Info** page in Home Assistant can show a "Visit ... page" link. This repository now points that link directly to this README.

If you do not see the updated link yet:

1. Open **Settings -> Add-ons -> Siseli Inverter Bridge**.
2. Click **Rebuild**.
3. Refresh the add-on page.

---

## 🌟 Supported Brands

This add-on supports a wide range of inverter brands that utilize the Siseli IoT cloud platform, including but not limited to:

- Solar of Things
- LUMINOUS NEO
- SUN WISE
- Queen Tech
- LIB Life
- Sun house
- LeiLing
- SunSaviour
- ECOmenic
- HC solar
- 沐能低碳
- PowMr
- Taico

---

## 🚀 Quick Setup

### Step 1: Prepare Home Assistant

Ensure the official **Mosquitto Broker** add-on is installed and configured:

1. Go to **Settings -> Add-ons -> Add-on Store**.
2. Install **Mosquitto Broker**.
3. Start it and ensure you have an MQTT user created.

### Step 2: Add Repository

1. Copy this repository URL: `https://github.com/fadmaz/siseli-ha`
2. In Home Assistant, go to **Settings -> Add-ons -> Add-on Store**.
3. Click the three dots in the top right -> **Repositories**.
4. Paste the URL and click **Add**.

### Step 3: Install & Configure

1. Find **Siseli Inverter Bridge** in the store and click **Install**.
2. Go to the **Configuration** tab.
3. Fill in the required fields:
   - **INVERTER_IP**: The local IP of your inverter (e.g., `192.168.1.139`).
   - **ROUTER_IP**: The local IP of your router (e.g., `192.168.1.1`).
   - **AUTO_INTERCEPT**: Keep `true` to use ARP Spoofing (automatic interception).

- Optional parallel-system fields:
  - **INVERTER_COUNT**: Number of parallel inverters.
  - **BATTERY_COUNT**: Number of batteries in the bank.
  - **BATTERY_CAPACITY_PER_BATTERY_AH**: Capacity per battery in Ah.

4. Go to the **Info** tab, enable **Watchdog**, and click **Start**.

### Parallel Inverter/Battery Scaling

When using multiple inverters in parallel, main summary power sensors are scaled with:

`c_scaled_power = raw_power * INVERTER_COUNT`

This is applied to:

- `c_generation_power_w`
- `c_mains_power_w`
- `c_load_w`

For battery-bank visibility, the bridge also publishes calculated BMS capacity helper sensors on the Main device:

- `c_bms_total_capacity_ah`

All calculated sensors use the `c_` prefix so they are easy to distinguish from raw inverter values.

---

## 🛠 How it Works (Technical)

The add-on uses multiple methods for traffic interception. For the inverter to start sending data to this add-on, it needs to "think" it is sending it to the Siseli cloud:

### Method A: ARP interception (recommended, default)

With `AUTO_INTERCEPT` enabled, the add-on tricks the inverter into sending its data to Home Assistant instead of the router. The bridge parses the data and transparently forwards it to the Siseli cloud.

> **⚠️ WARNING:** You are using ARP spoofing, which is a sensitive network technique. It can trigger security alerts on advanced network setups or enterprise routers (like UniFi or pfSense).

### Method B: Router-side redirect (advanced, unsupported)

Route traffic destined for the Siseli cloud IP through your Home Assistant host, and
set `AUTO_INTERCEPT` to `false`.

This works only if all three hold, which is why it is not supported:

- the redirect must preserve `TARGET_HOST` (`8.212.18.157`) as the **destination IP**.
  The bridge matches on that address, so anything that rewrites the destination — a DNS
  override, a NAT redirect — is not seen at all;
- the Home Assistant host must have `net.ipv4.ip_forward` enabled, or the inverter loses
  its connection entirely;
- your router must support policy routing of a single destination address.

If you cannot use ARP interception, **switch port mirroring (SPAN) is the better
answer**: mirror the inverter's port to the Home Assistant host and leave
`AUTO_INTERCEPT` off. The sniffer is passive, so nothing else is required, and the
inverter's traffic is never touched.

> A DNS override pointing the Siseli domain at Home Assistant does **not** work. There
> is no listener — the bridge observes traffic, it does not terminate it — so the
> inverter's connection is simply refused.

---

## 📊 Available Sensors

This bridge dynamically extracts and exposes **almost every single sensor and data point available in the official Siseli app** (100+ entities) directly into Home Assistant via MQTT Auto-Discovery.

Sensors are now split across multiple Home Assistant devices instead of one large combined device:

- **Battery**
- **BMS**
- **Grid**
- **Load**
- **PV**
- **Diagnostics** (for non-functional or fallback settings)

The "More" tab diagnostics are functionally routed where possible (battery-related settings to Battery, mains/grid settings to Grid, PV/solar settings to PV, output/parallel settings to Load).

The exposed data includes:

- **🔋 Battery & BMS Status**
  - Overall Voltage, Capacity (%), Charge/Discharge Currents, Battery Type
  - Remaining Capacity (Ah), Nominal Capacity (Ah), Min/Max Cell Voltages, and individual cell voltages (1-16)
- **⚡ Grid & Load Status**
  - AC Input Voltage & Mains Frequency
  - Active Load (W), Apparent Power (VA), Output Voltage/Frequency, and Load Percentage
- **☀️ PV Panel Status**
  - Daily, Monthly, Yearly, and Total Electricity Generation (kWh)
  - PV1 & PV2 Voltages, Currents, Wattage, and PV Temperatures
- **⚙️ Advanced Device Settings ("More" tab)**
  - Dozens of configuration points including Working Mode (SBU, UTI, etc.), Charging Priority, Output Frequencies
  - Fan Speeds, Warning Lights, Hardware Switches (AC Charging, Main Output Relay)
  - Customizable thresholds (Float Charging Voltage, Low Battery Alarm, Overvoltage Shutdown)
  - Diagnostic booleans (Abnormal Fan Speed, EEPROM errors, Machine Over Temperature)

---

## ❓ Compatibility

Tested on:

- RWB1
- PowMr variants
- Taico variants

_Note: It may work out-of-the-box on other Siseli-based devices listed in the Supported Brands section._

---

## 🧪 Troubleshooting

**No data appearing in Home Assistant?**

- **Check MQTT Connection:** Ensure your Mosquitto broker is running and the add-on logs show a successful connection.
- **Verify Inverter IP:** Double-check that `INVERTER_IP` and `ROUTER_IP` are exactly correct in the configuration.
- **Set `SNIFF_IFACE` explicitly:** auto-detection picks the wrong interface on hosts with several.
- **Pin the MAC addresses:** fill in `INVERTER_MAC` and `ROUTER_MAC` rather than relying on discovery.
- **Check the health line:** it reports the addresses actually seen, and any non-broker inverter packets that were dropped.
- **Turn on the right diagnostics:** set **Debug Flags** to `blocks` and `unparsed_publish` and **Log Level** to `info`. If `unparsed_publish` produces output, the payload is arriving but the block layout is unrecognised — open an issue with those lines.
- **If ARP interception is blocked by your network:** use switch port mirroring (SPAN) toward the Home Assistant host and set `AUTO_INTERCEPT` to `false`.

**After upgrading, I see duplicate or stale entities in Home Assistant**

This is handled automatically from 2.6.1. On the first start after an upgrade the
bridge clears retained discovery messages left behind by earlier versions that grouped
sensors differently, so no manual broker cleanup is needed. The **Clean Up Stale
Entities** option controls it if you ever need to turn it off.

**Some sensors show "Unknown"**

From 2.6.0 the bridge publishes a value only when it decoded one from your inverter.
Around 38 sensors — the fault indicators, the BMS alarm flags, `Mode` and the light
statuses — previously showed hardcoded values that were never read from the device, so
they now read Unknown until a real decode exists for them. They are disabled by default
on new installations.

**PV Voltage, PV Current and PV Power all read zero**

Expected on a single-string system: your array reports on the channel the inverter
calls PV2, and the official app shows the same split. `Generation Power` sums both
channels, so your totals are correct.

---

## 🇺🇦 Українською (Ukrainian)

Цей додаток дозволяє інтегрувати інвертори, сумісні з Siseli Cloud, у Home Assistant без використання зовнішніх хмар (підтримуються бренди Solar of Things, LUMINOUS NEO, PowMr, Taico та інші). Він перехоплює трафік, що йде до хмари Siseli, та автоматично створює сенсори. Повна інструкція з налаштування доступна в розділі README вище (англійською).

---

## 📄 License

MIT License. Free to use and modify.
