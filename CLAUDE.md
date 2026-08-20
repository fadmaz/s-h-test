# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A Home Assistant add-on that ARP-spoofs a solar inverter, passively reassembles its
MQTT stream to the Siseli cloud, decodes the telemetry, and republishes it to Home
Assistant via MQTT auto-discovery. Traffic is forwarded on to the cloud so the vendor
app keeps working — the bridge observes, it never terminates a connection.

`CONTRIBUTING.md` covers dev setup, test conventions, the block-capture procedure and
the release checklist. This file covers what the code does not say about itself.

## Commands

```bash
pytest siseli_bridge/tests -q                                   # full suite
pytest siseli_bridge/tests/test_parsers.py -q                   # one file
pytest siseli_bridge/tests -q -k "test_output_relay_can_report_off"   # one test
ruff check .                                                    # defect-only lint
bash scripts/smoke-test.sh                                      # start the image, wait for a running sniffer
```

Coverage floors, matching CI:

```bash
pytest siseli_bridge/tests --cov=siseli_bridge/src --cov-report=
python -m coverage report --fail-under=78
python -m coverage report --include="*/siseli_bridge/mqtt.py,*/siseli_bridge/core.py" --fail-under=65
```

CI runs seven jobs: tests on 3.9/3.11/3.12, `ruff`, the Home Assistant add-on linter,
a `docker build`, and the smoke test.

## Architecture

One process, three threads, one shared dict.

```
scapy AsyncSniffer ──> core.packet_callback ──> core.handle_inverter_tcp_packet
                                                        │
                                     parsers.append_stream_data   (TCP reassembly)
                                                        │
                                     parsers.extract_mqtt_packets_from_stream
                                                        │
                                     parsers.SolarParser.parse_payload
                                                        │
                                        state.LAST_STATE ──> mqtt.publish_grouped_state
```

- **`core.py`** — capture, ARP spoofing, forwarding, lifecycle, the availability watchdog.
- **`parsers.py`** — TCP reassembly, MQTT framing, and `SolarParser`, which turns
  base64 blocks into sensor values. The bulk of the project.
- **`mqtt.py`** — discovery payloads, topic derivation, the stale-discovery sweep.
- **`sensors.py`** — the declarative sensor registry. All topics derive from it.
- **`state.py`** — shared mutable state, the lock, and atomic JSON persistence.
- **`config.py`** — every option, read from the environment at import.

Threads: the scapy callback (parses and publishes), the paho network thread
(`on_connect`), and the watchdog (`health_logger`, ticks every 10s). They share
`state.LAST_STATE` under `state.STATE_LOCK`.

### How decoding works

The inverter publishes JSON containing base64 blocks keyed by four-character names
(`2ONL`, `WdRR`, `Yavb`, `93VQ`, …). Each decodes to space-separated ASCII tokens read
**by position**. There is no schema — positions were reverse-engineered from one
device.

**Payloads carry different block subsets.** A real capture showed two payloads with
*zero* overlap. Never assume a field is present because it was present last time.

**The rule that governs this file: publish a value only when this payload contains
evidence for it.** The parser used to fall back on constants memorised from one
inverter — fault flags that could never report a fault, `mode` as a literal string.
`tests/test_truthfulness.py` pins their absence. Do not reintroduce a default,
a cross-block alias, or a value derived from a different quantity.

## Gotchas that have caused real breakage

**`from .config import *`** in `core.py`, `mqtt.py` and `parsers.py` means those
modules hold *bound copies* of every option. Two consequences:

- Patch constants on the **consuming** module in tests
  (`patch_consts("src.siseli_bridge.parsers", INVERTER_COUNT=2)`); reloading
  `config.py` does nothing.
- Names starting with `_` are **not** exported by the star import. Referencing one
  resolves at runtime, and these files carry a ruff `F405` exemption, so neither lint
  nor tests catch it. This crash-looped a release.

**`core.py`'s runtime lives under `if __name__ == "__main__"`,** which no test
executes. Anything that must be verified belongs in a module-level function called
from there — `log_startup_configuration()` and `load_cached_state()` are the pattern.

**Home Assistant validates *stored* options against the new schema before installing
an update.** Tightening a schema can block the upgrade for existing installs. A
trailing `?` means the option may be *absent*; it does not exempt an empty string.
Removing an option entirely also blocks it. `tests/test_packaging.py` guards both.

**A stored option shadows the shipped default forever.** Supervisor pins every
option's value the first time the user saves the configuration page, and
`bashio::config` then reads that pin. Changing a default in `config.yaml` fixes fresh
installs *only* — every existing user keeps the old value however many releases ship.
So a default is not a fix. If a wrong value can break the add-on, the runtime has to
defend itself against its own configuration: `effective_telemetry_timeout()` is the
pattern. Print any option of this kind in `log_startup_configuration()`, or the
running value is invisible in a user's log.

**`/data/state.json` outlives the code.** Removing a sensor from the parser does not
remove it from anyone's dashboard — the cached value is restored and republished.
Purge it in `load_cached_state` via `UNDECODED_SENSOR_KEYS`.

**Timing defaults must come from measured cadence,** not from another option. This
inverter reports every ~300s with 600s gaps; a timeout derived from
`UPDATE_INTERVAL_SEC` made every sensor flap. The observed cadence is a fixture in
`tests/test_core.py`. Better still, measure it at runtime — the availability watchdog
floors its timeout on the intervals it actually sees, which is what makes it immune to
the pinned-option trap above.

**`gh` defaults to the upstream fork.** Always pass `--repo fadmaz/siseli-ha`.

## Verification

Passing tests and a successful `docker build` are both compatible with an add-on that
cannot start — that combination shipped twice. Run `scripts/smoke-test.sh` before
claiming a change works, and prefer a debug log from a real installation over any
local reasoning. Every deployment-shaped bug in this project's history was found by
running it, not by reading it.

Fixtures in `tests/captures.py` are byte-faithful captures from real hardware, with
golden expected values. `SYNTH_*` blocks are hand-built and must never be used for
value-parity assertions.
