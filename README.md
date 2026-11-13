# ADA RS-232 for Home Assistant

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="custom_components/ada_rs232/brand/dark_logo.png">
  <img alt="Audio Design Associates" src="custom_components/ada_rs232/brand/logo.png" width="480">
</picture>

Local control of the **Audio Design Associates PTM-1645** over its PAC RS-232
connection. This is an installable custom integration, with a UI setup flow
modeled on [Denon RS-232](https://www.home-assistant.io/integrations/denon_rs232/).
It requires **Home Assistant 2026.11.0 or newer**.

[![Open ADA RS-232 in your Home Assistant Marketplace.](https://my.home-assistant.io/badges/marketplace_repository.svg)](https://my.home-assistant.io/redirect/marketplace_repository/?owner=RebbePod&repository=ada-rs232&category=integration)

## Full serial package

The stable release includes the documented PAC serial commands, automatic
amplifier discovery, and hardware setup actions. Zone switches and automatic
discovery were tested on a physical PTM-1645 through ESPHome. Setup actions,
daisy chains, and PTM-8100 support have automated coverage and still need hardware
testing.

## Supported functionality

- Eight stereo-zone power switches for PTM-1645, or four for PTM-8100.
- Up to nine uniquely addressed amplifiers on one shared serial connection.
- Atomic trigger-mask writes, a whole-chain state query, and broadcast all-off.
- Explicit setup actions for trigger mapping, Quick Turn On, and stored address.
- Firmware, address, Quick Turn On, and mapping readback from the setup screen.
- Optional output binary sensors that report actual outputs with any mapping.
- Local USB/RS-232 ports, ESPHome native serial proxies, and serialx-supported
  network serial connections such as `socket://` and `rfc2217://`.
- Hardware-confirmed state, unsolicited feedback handling, and periodic polling
  (60 seconds by default).
- Automatic reconnection on the next poll after a connection failure; Home
  Assistant retries initial setup if the amplifier is offline.
- UI options for polling and timeout, connection reconfiguration that preserves
  entity IDs, and diagnostics that omit the connection endpoint and credentials.

The PTM-1645 is a power amplifier: this integration exposes zone power. Volume,
mute, source selection, and playback have no commands in this PAC manual.
It does not change zone power when Home Assistant starts or stops.

## Prerequisites

- A PTM-1645 or PTM-8100 with PAC data control and an existing address from **1 to 9**.
- The **default one-to-one trigger mapping**. PAC feedback reports output states,
  while data commands operate the configured triggers. A custom trigger mapping
  makes an independent output switch model ambiguous. When setup readback shows
  custom mappings, zone switches become unavailable. Use explicit trigger-mask
  actions and the optional output binary sensors instead.
- An RS-232 connection to the amplifier, either directly from Home Assistant or
  through your ESPHome device and its existing RS-232 level converter.

The protocol settings are **19200 baud, 8 data bits, no parity, 1 stop bit, no
flow control**. GPIO UART pins require an appropriate RS-232 transceiver; a
software proxy does not perform electrical level conversion.

For a daisy chain, add one integration entry per amplifier using exactly the same
port URL. Setup filters out addresses that already have entries. Each amplifier
must already have a unique PAC address. All entries share one transport and command
queue. Duplicate port/address pairs are blocked. A failed shared transport makes
its amplifiers unavailable until the next successful poll. Response timeout uses
the largest timeout requested by entries sharing the connection.

## Install from the Marketplace

1. Open **Settings → Marketplace → Add from link**, or use the badge above.
2. Enter **https://github.com/RebbePod/ada-rs232** and select **Add**. Connect
   GitHub if prompted. If asked for a type, select **Integration**.
3. Open **ADA RS-232** and install the latest stable release, **v0.2.2** or newer.
4. Restart Home Assistant.
5. Open **Settings → Devices & services → Add integration → ADA RS-232**.
6. Select your serial port and amplifier model. Setup discovers existing PAC
   addresses automatically. If several available amplifiers respond, choose one
   from the discovered list. The scan does not change hardware settings.

For your existing ESPHome connection, follow the migration steps below before
adding the integration. The Marketplace installs the Home Assistant files; the
serial proxy firmware is configured separately on the ESP32.

See the official [Marketplace custom repository instructions](https://www.home-assistant.io/integrations/marketplace/#custom-repositories).
This repository is available as a custom repository; it is not in the default
Marketplace catalog or Home Assistant Core. The full package remains available
here while a smaller, Bronze-scoped Core integration is prepared separately.

Existing HACS installations carry over to the Marketplace in Home Assistant
2026.11. The package still uses `hacs.json` and the HACS validation action because
the Marketplace uses the same repository format and catalog.

### Logo or version still looks old

The release includes the supplied ADA artwork in `brand/`, including separate
light and dark icons and logos. Home Assistant serves these local images through
its brands API. After updating in the Marketplace, perform a full **Home Assistant restart**;
reloading the integration alone can leave cached integration metadata. Reload
the browser or Companion app afterward. If necessary, use a hard refresh of the
browser. The integration page should show the installed version **0.2.2** or newer.

If the page still reports **0.1.0** or shows a generic amplifier icon, first check
the Marketplace has installed the current release. Verify that
`/config/custom_components/ada_rs232/brand/` contains the PNG artwork. A new API
test verifies every shipped light, dark, and high-resolution image is served
by Home Assistant instead of a placeholder.

## Install manually

1. Copy `custom_components/ada_rs232` from this repository into
   `/config/custom_components/ada_rs232` on Home Assistant. The `manifest.json`
   should be at `/config/custom_components/ada_rs232/manifest.json`.
2. Restart Home Assistant.
3. Open **Settings → Devices & services → Add integration → ADA RS-232**.
4. Select your serial port and amplifier model. Setup scans for existing
   amplifiers using a read-only query. One available amplifier is selected
   automatically; if several respond, choose one from the discovered list.

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

The parser rejects echoed commands and invalid bit strings, and routes each
valid feedback frame to the matching amplifier address.
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
**Reconfigure** to change the connection or select another discovered amplifier.
To change the address stored in hardware, use the explicit setup action below.
A scan only reads existing addresses.

## PAC actions

Open **Developer tools → Actions** and choose an **ADA RS-232** action. Select
an amplifier entry in its form. All custom PAC actions require an administrator;
normal zone switches use Home Assistant's usual entity permissions. Every action
can return its confirmed settings or actual output states as response data.

| Action | Function |
| --- | --- |
| `ada_rs232.query_all` | `GA`: read all responding amplifiers on the selected entry's connection. |
| `ada_rs232.set_trigger_states` | `S<address>=<mask>`: write eight trigger bits in one command. |
| `ada_rs232.all_off` | `SA=00000000`: turn off the serial triggers on the entire connection, including unconfigured amplifiers. |
| `ada_rs232.read_setup` | Enter: read the hardware setup screen. |
| `ada_rs232.set_trigger_mapping` | `T1`–`T8`: assign a trigger to output bits. |
| `ada_rs232.set_quick_turn_on` | Read the setting, toggle `Q` only when needed, then verify. |
| `ada_rs232.set_address` | `A1`–`A9`: change the address stored in the amplifier. |
| `ada_rs232.restore_trigger_defaults` | `D`: restore one-to-one trigger mappings. |
| `ada_rs232.resume` | Verify normal operation after physically exiting setup. |

Masks contain exactly eight `0`/`1` characters, leftmost bit first. With default
mapping, `10000000` activates zone 1 and `00000000` clears every serial trigger.
For PTM-8100, bits 5 through 8 must be zero. Hardware voltage triggers and bypass
can keep outputs on even after all-off; responses report actual outputs.

### Change hardware setup

1. Disable other amplifier entries sharing this connection and physically
   disconnect all loop-through amplifiers. Only one amplifier may be connected.
2. Hold its rear **Setup** button for more than five seconds and release it.
3. Run **Read hardware setup**, confirming the single-amplifier condition.
   The response shows firmware, address, Quick Turn On, and all trigger mappings.
4. Run the desired setup action. Each write verifies the resulting setup screen.
   Quick Turn On keeps the power supply running for immediate audio response;
   otherwise initial audio activation can take about three seconds.
5. Press **Setup** once to exit, then run **Resume normal operation**. A confirmed
   address change is saved immediately so it survives a restart. Resume applies
   that address to the running connection and preserves entity IDs.
6. Reconnect the chain and enable its other integration entries.

The amplifier leaves setup after 60 seconds of inactivity. If a command loses its
confirmation, read setup again before retrying. A mapping write with uncertain
results keeps zone switches unavailable until a complete screen confirms the
mapping. Custom mapping status is saved across restarts. Output binary sensors
are disabled by default; enable them on the amplifier's device page to monitor
physical outputs when using custom mappings. A model selected as PTM-8100 has
four output sensors and four zone switches.

## Validation and troubleshooting

This implementation has automated protocol and Home Assistant lifecycle tests.
Zone switches and automatic amplifier discovery worked on the maintainer's
PTM-1645 through ESPHome. The other commands, setup screen parser, daisy chains,
and PTM-8100 handling still need verification on real equipment.
After installation, verify initial state, turn one unused zone on/off, and check
that another active zone is preserved. Then disconnect/reconnect the bridge and
check that entities recover after a poll.

If setup cannot read the amplifier, check the selected PAC address, RS-232
transceiver/cabling, amplifier power and network/API connection. Confirm the old
ESPHome scripts and custom UART commands have been removed. Configure the amp's
address and trigger mapping using its documented setup procedure, then exit
setup mode before normal power control. PTM-8100 support is untested on hardware.

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

The locked test environment uses Home Assistant 2026.11.1. Home Assistant tests
cover configuration, lifecycle, shared ownership, permissions, setup guards,
command responses, and model-specific behavior. Protocol tests live in the
[ada-rs232 library](https://github.com/RebbePod/ada-rs232-python). CI runs on Linux.
