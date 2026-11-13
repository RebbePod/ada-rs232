# ADA RS-232 for Home Assistant

![ADA RS-232 integration icon](custom_components/ada_rs232/brand/icon.png)

Local control of the **Audio Design Associates PTM-1645** over its PAC RS-232
connection. This is an installable custom integration, with a UI setup flow
modeled on [Denon RS-232](https://www.home-assistant.io/integrations/denon_rs232/).
It requires **Home Assistant 2026.11.0 or newer**.

## Supported functionality

- Eight zone power switches, grouped under one PTM-1645 device.
- Local USB/RS-232 ports, ESPHome native serial proxies, and serialx-supported
  network serial connections such as `socket://` and `rfc2217://`.
- Hardware-confirmed state, unsolicited feedback handling, and periodic polling
  (60 seconds by default).
- Automatic reconnection on the next poll after a connection failure; Home
  Assistant retries initial setup if the amplifier is offline.
- UI options for polling and timeout, connection reconfiguration that preserves
  entity IDs, and diagnostics that omit the connection endpoint and credentials.

The PTM-1645 is a power amplifier: this integration exposes zone power. Volume,
mute, source selection, playback and amplifier setup commands are not exposed.
It does not change zone power when Home Assistant starts or stops.

## Prerequisites

- A PTM-1645 with PAC data control and an existing address from **1 to 9**.
- The **default one-to-one trigger mapping**. PAC feedback reports output states,
  while data commands operate the configured triggers. A custom trigger mapping
  makes an independent output switch model ambiguous and is unsupported.
- An RS-232 connection to the amplifier, either directly from Home Assistant or
  through your ESPHome device and its existing RS-232 level converter.

The protocol settings are **19200 baud, 8 data bits, no parity, 1 stop bit, no
flow control**. GPIO UART pins require an appropriate RS-232 transceiver; a
software proxy does not perform electrical level conversion.

One amplifier per serial connection is supported. PAC daisy chains need a shared
bus manager and are outside this release. Adding the same port twice is blocked.

## Install with HACS

1. In **HACS**, open the **⋮** menu and choose **Custom repositories**.
2. Enter **https://github.com/RebbePod/ada-rs232** and select type **Integration**.
3. Add the repository, find **ADA RS-232**, and download the latest release.
4. Restart Home Assistant.
5. Open **Settings → Devices & services → Add integration → ADA RS-232**.
6. Select your serial port and enter the amplifier's existing PAC address.

For your existing ESPHome connection, follow the migration steps below before
adding the integration. HACS installs the Home Assistant files; the serial proxy
firmware is configured separately on the ESP32.

See [HACS custom repository instructions](https://www.hacs.xyz/docs/faq/custom_repositories/).
This repository is available as a custom repository; it is not in the default
HACS catalog or Home Assistant Core.

## Install manually

1. Copy `custom_components/ada_rs232` from this repository into
   `/config/custom_components/ada_rs232` on Home Assistant. The `manifest.json`
   should be at `/config/custom_components/ada_rs232/manifest.json`.
2. Restart Home Assistant.
3. Open **Settings → Devices & services → Add integration → ADA RS-232**.
4. Select your serial port and enter the amplifier's existing PAC address.
   Setup sends a read-only query to verify a valid eight-zone response.

For local USB adapters, prefer `/dev/serial/by-id/...`. For a network serial
server, enter its URL manually. A raw `socket://` server must already be
configured for 19200/8N1; a raw TCP connection cannot configure its UART.

Release bundles are available on the
[GitHub releases page](https://github.com/RebbePod/ada-rs232/releases).

## Migrate your ESPHome configuration

Your ESP32 remains connected to the amplifier. Home Assistant takes over the PAC
protocol, and ESPHome forwards serial bytes over its native API.

1. Keep your existing board, network, OTA, logger and encrypted `api:` settings.
2. Remove the old ADA scripts, periodic poll, eight template switches, custom
   command text/button and UART debugging block. They must not share the UART
   with the proxy.
3. Merge [examples/esphome-serial-proxy.yaml](examples/esphome-serial-proxy.yaml)
   into your device YAML. It preserves **TX GPIO4 / RX GPIO5** and 19200/8N1.
   The example is a fragment; your existing device configuration must include
   `api:`. Use an ESPHome version with the `serial_proxy` component.
4. Compile and install the updated ESPHome configuration yourself.
5. Add or reconnect the device through Home Assistant's **ESPHome integration**.
6. Add **ADA RS-232** and select the **ADA PTM-1645** proxy port from the serial
   selector. Home Assistant manages its `esphome-hass://` endpoint.
7. Update automations and dashboard cards that used the old ESPHome switch IDs
   to use the new zone switch entities. Zone names can be changed in the UI.

See the official [ESPHome serial proxy configuration](https://esphome.io/components/serial_proxy/)
and [Home Assistant serial connection guide](https://www.home-assistant.io/integrations/serial/).

## How state and commands work

`G1\r\n` requests the current outputs at address 1. A valid reply looks like
`1=10000000\r\n`. `S1=10000000\r\n` sends a complete eight-bit control mask.
The leftmost bit represents zone 1. The configured address replaces `1`.

Every switch change holds a transaction lock across a fresh read, one-bit
modification, full-mask write, 250 ms settling period and explicit readback.
Concurrent service calls therefore preserve each other's changes. A silent
`S` command is supported; a successful write alone never confirms switch state.
Unknown state is never filled with eight default-off bits and written to the amp.

The parser ignores echoed commands, other addresses and invalid bit strings.
It handles fragmented packets, CR/LF/CRLF, and complete unterminated replies after
a short idle gap. Timeouts close the connection so a late reply from the old
connection cannot satisfy the next request.

Hardware voltage triggers and bypass can override data control. A switch may
remain on after an off command if an external trigger holds that output on.
Feedback cannot distinguish a hardware trigger from a data trigger. Reading and
rewriting an externally enabled output can also latch that output into the data
mask; use independent serial control with default trigger mapping for predictable
operation. The PAC protocol has no transaction IDs or atomic single-zone command,
so an external change between read and write cannot be made atomic by software.

Connection options are under the integration's **Configure** menu. Use
**Reconfigure** to change the port/address. Reconfiguration saves the settings
and reconnects through normal setup; an offline connection will show setup retry.

## Validation and troubleshooting

This implementation has automated protocol and Home Assistant lifecycle tests.
Physical PTM-1645 and ESP32 validation still needs to be done on your equipment.
After installation, verify initial state, turn one unused zone on/off, and check
that another active zone is preserved. Then disconnect/reconnect the bridge and
check that entities recover after a poll.

If setup cannot read the amplifier, check the selected PAC address, RS-232
transceiver/cabling, amplifier power and network/API connection. Confirm the old
ESPHome scripts and custom UART commands have been removed. Configure the amp's
address and trigger mapping using its documented setup procedure, then exit
setup mode before connecting this integration. Other PAC models are untested.

The command reference is the manufacturer's **PAC Instructions for PTM-1645 &
PTM-8100 Amps**, available as a [manual reproduction](https://manualzz.com/doc/57518291/audio-design-associates-ada-pac-ptm-1645-instructions).
Framing and post-write readback also follow the supplied, working ESPHome YAML.

## Development

Use Python 3.14.2 or newer and [uv](https://docs.astral.sh/uv/):

```sh
uv sync --locked
uv run ruff check custom_components tests scripts
uv run ruff format --check custom_components tests scripts
uv run pytest --cov=custom_components.ada_rs232 --cov-report=term-missing
```

The locked test environment uses Home Assistant 2026.11.1. Tests cover protocol
framing, wrong-address replies, concurrent zone changes, hardware overrides,
timeouts, cancellation, disconnect/reconnect, config flows, switch services,
availability, unload and diagnostics. CI runs these checks on Linux.
