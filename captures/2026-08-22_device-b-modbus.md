# Device B — Beve Mega 6kW L1PE-ECO — a different protocol

Reported in [issue #30](https://github.com/fadmaz/siseli-ha/issues/30) against add-on 2.6.16
with every sensor reading `Unknown`. **This device is not supported and this file is not a
decode.** It records what the one capture proves, so the work is not redone from scratch if
support is ever attempted.

The add-on behaved correctly: it recognised nothing and published nothing. What it lacked
was a way to *say* so, which 2.6.17 adds.

## What is shared, and what is not

| | Device A (supported) | Device B |
|---|---|---|
| MQTT topic | `dtu/<id>/pub/event/dev_prop_post` | **same** |
| Envelope | JSON, base64 blocks under `b.ct`, `cn`/`co` keys | **same** |
| Block names | `2ONL 2l0E 93VQ COST Mpod V4W3 WdRR Yavb dHrK eo8w noeP` | `CLNi EsQL FDFm Jl4X PS4Z Sgx0 ZMnp aKuG aRv4 hIg6 r8BV seO5 xvq9` — **no overlap** |
| Block body | ASCII, `(`-framed, space-separated tokens | **binary Modbus RTU** |

One block, `aRv4` = `(ACK9\r`, *is* in Device A's ASCII framing. So the DTU wrapper is
common to both and only the inverter's own payload differs — which is why the transport,
the interception and the reassembly all worked perfectly for this reporter.

## The framing is Modbus RTU — proven, not inferred

Each body is `address, function, byte count, data…, CRC16` with the CRC stored
little-endian. **10 of 13 blocks verify** against CRC16/Modbus (poly `0xA001`, init
`0xFFFF`). A single false positive would need a 16-bit collision; ten simultaneously is
conclusive.

The three that do not verify are explained, not ignored:

| Block | Why |
|---|---|
| `CLNi` | Length-complete, but function code `0x21` (vendor, not standard) and the CRC bytes are swapped relative to the others |
| `r8BV` | Declares 146 data bytes; only 61 survived. **Truncated by our own `hex_preview` logger**, not by the device |
| `Sgx0` | Verifies, but its sibling frames in the second payload were likewise preview-truncated |

Address is `0x05` and function `0x03` (read holding registers) throughout — this is a DTU
polling an inverter over Modbus and forwarding the raw responses.

## Registers decode as little-endian 16-bit

Note **little-endian**, which is unusual for Modbus and is the thing most likely to be got
wrong on a first attempt. The nameplate confirms it: `hIg6[0]` reads `0x1770` = **6000**
byte-swapped, matching the reporter's "Beve Mega **6kw**". Big-endian would give 28695.

`hIg6` — static across both payloads, so a settings/nameplate block:

| reg | raw | reading |
|---|---|---|
| 0, 1 | 6000 | rated power W — matches the "6kw" model name |
| 2, 5 | 230 | nominal AC voltage |
| 4 | 480 | **48 V battery bank** (÷10) |
| 6 | 500 | 50.0 Hz |

`PS4Z` — live AC measurements. Values that moved between the two payloads are the
persuasive ones:

| reg | payload 1 → 2 | reading |
|---|---|---|
| 1, 9 | 2165 | 216.5 V |
| 2, 10 | 503 → 504 | 50.3 → 50.4 Hz |
| 5 | 540 → 539 | 54.0 → 53.9 V battery (correct for a charged 48 V bank) |
| 6 | 100 | 100 % SOC |
| 11 | 983 → 967 | W |
| 12 | 797 → 785 | W |
| 16 | 500 | 50.0 Hz setpoint |

`aKuG` — regs 0 and 1 rise monotonically (1917 → 1927, 294 → 333); regs 4/5/6 sit at 276,
318, 344, plausible as temperatures ÷10. Not established.

## What supporting this device would actually take

Adding it is a **second parser family**, not a variant: a Modbus register map has no
relationship to the ASCII token positions everything in `parsers.py` is built around, and
it would need its own sensor namespace.

The blocker is ground truth, not effort. Every position in Device A's map was pinned by
pairing a capture with the vendor portal *to the second* — see
[`../sensor_mapping_verified.md`](../sensor_mapping_verified.md). Nothing here has that.
What would be needed from the reporter:

1. Their portal or app **Data Overview** screenshot, captured the same minute as a log.
2. Captures in several states — charging, discharging, on grid, after dark — so a moving
   register can be tied to a moving displayed value rather than guessed at.
3. The full `[BLOCK RAW]` bodies for `r8BV` and `Sgx0`, which our own preview truncated.

Fixtures for the frames that *are* byte-faithful live in `tests/captures.py` as
`CAPTURE_DEVICE_B_FOREIGN`. They exist to test the unsupported-protocol diagnostic against
a real foreign device, and are not decode targets.
