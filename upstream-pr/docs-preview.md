# ADA RS-232

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="../custom_components/ada_rs232/brand/dark_logo.png">
  <img alt="Audio Design Associates" src="../custom_components/ada_rs232/brand/logo.png" width="420">
</picture>

> Documentation review preview. The Home Assistant templates have been expanded
> so you can read the proposed page normally. The source wording is preserved;
> GitHub provides the presentation rather than the Home Assistant website theme.

The **ADA RS-232** integration connects Home Assistant to the Audio Design Associates PTM-1645 power amplifier over its RS-232 serial port. You can turn each of its eight stereo zones on or off using local control.

## Supported devices

- Audio Design Associates PTM-1645 with the PAC amplifier controller

## Prerequisites

This integration requires a serial connection to your device. You can connect the device to a serial port on the system that runs Home Assistant, or reach it over your network with an [ESPHome](https://www.home-assistant.io/integrations/esphome/) serial proxy. For more details, refer to [setting up a serial connection](https://www.home-assistant.io/integrations/serial/#setting-up-a-serial-connection-in-home-assistant).

1. Set the amplifier to its normal operating mode, with the default one-to-one trigger mapping.
2. Find the amplifier's existing PAC address, from 1 to 9.
3. If you use a raw TCP serial server, configure its serial port for 19200 baud, 8 data bits, no parity, 1 stop bit, and no flow control.

For an ESPHome connection, use an [ESPHome serial proxy](https://www.home-assistant.io/integrations/serial/#setting-up-an-esphome-serial-proxy). The proxy's UART must be dedicated to this integration; remove any previous amplifier polling scripts and template switches from that UART.

## Configuration

To add the **ADA RS-232** hub to your Home Assistant instance, use this My button:

[Add ADA RS-232 to Home Assistant](https://my.home-assistant.io/redirect/config_flow_start/?domain=ada_rs232)

<details open>
<summary>Manual configuration steps</summary>

If the above My button doesn't work, you can also perform the following steps manually:

- Browse to your Home Assistant instance.
- Go to **Settings > Devices & services**.
- In the bottom right corner, select the **Add integration** button.
- From the list, select **ADA RS-232**.
- Follow the instructions on screen to complete the setup.

</details>

**Port**

The local serial port or ESPHome serial proxy connected to your amplifier. You can also enter a network serial server URL manually.

**Amplifier address**

The amplifier's existing PAC address, from 1 to 9. The default is 1. This selects the amplifier to control; it does not change the address stored in the amplifier.

## Supported functionality

### Switches

- **Zone 1** through **Zone 8**
  - **Description**: Controls power to a stereo output pair and reports the output state received from the amplifier. All eight switches belong to one amplifier device.

You can turn a zone on or off from its switch entity or use the standard [switch actions](https://www.home-assistant.io/integrations/switch/). The PTM-1645 does not provide serial volume, mute, source selection, or playback controls through its PAC controller.

## Data updates

The integration polls the amplifier every 60 seconds and updates the switches when feedback arrives. After a zone command, it reads the output states again before reporting the result. Home Assistant reads the existing state when it starts; it does not restore or send saved zone states.

If communication fails, the switches become unavailable. The next scheduled poll attempts to reconnect.

## Known limitations

- Hardware voltage triggers and the amplifier's bypass control can override serial commands. A zone can remain on after you turn its switch off if a hardware trigger keeps that output active.
- Feedback reports output states without identifying whether a hardware trigger or a serial command enabled them. Preserving an externally enabled output in a later command can also keep it enabled through serial control.
- Custom trigger mappings and daisy-chained amplifiers are not supported. Use one amplifier per serial connection.

## Removing the integration

### To remove an integration instance from Home Assistant

1. Go to **Settings** > **Devices & services** and select the integration card.
2. Next to the entry you want to remove, select the three dots (⋮) menu. Then, select **Delete**.
   - Depending on the integration, the entries are listed under one of the following headings:
     - **Devices**
     - **Hubs**
     - **Services**
     - **Integration entries**
3. To confirm, select **Delete**.
   - Home Assistant also deletes the devices and entities of the entry.
4. If Home Assistant asks you to restart, [restart Home Assistant](https://www.home-assistant.io/common-tasks/general/restarting/#restarting-home-assistant).
5. If Home Assistant asks whether to also delete the application credentials, select **Remove** or **Keep**.
   - If you keep them, Home Assistant uses them automatically when you add the integration again.
   - To delete them later, refer to [Deleting application credentials](https://www.home-assistant.io/integrations/application_credentials/#deleting-application-credentials).

Removing the integration closes the serial connection and leaves the amplifier's zone power states unchanged. No additional amplifier cleanup is required.

---

[Proposed documentation source](https://github.com/RebbePod/home-assistant.io/blob/add-ada-rs232/source/_integrations/ada_rs232.markdown) · [Core PR description](core-pr.md) · [Documentation PR description](docs-pr.md) · [Branding PR description](brands-pr.md)
