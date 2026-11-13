# ADA RS-232

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="../custom_components/ada_rs232/brand/dark_logo.png">
  <img alt="Audio Design Associates" src="../custom_components/ada_rs232/brand/logo.png" width="420">
</picture>

> Documentation review preview. The Home Assistant templates have been expanded
> so you can read the proposed page normally. The source wording is preserved;
> GitHub provides the presentation rather than the Home Assistant website theme.

The **ADA RS-232** integration connects Home Assistant to Audio Design Associates PTM-1645 power amplifiers over their RS-232 serial connection. You can turn each stereo zone on or off using local control. Amplifiers in a daisy chain share one serial connection.

## Supported devices

- Audio Design Associates PTM-1645 with the PAC amplifier controller: eight stereo zones

The PTM-1645 zone controls and automatic address scan have been tested with an ESPHome serial proxy.

## Prerequisites

This integration requires a serial connection to your device. You can connect the device to a serial port on the system that runs Home Assistant, or reach it over your network with an [ESPHome](https://www.home-assistant.io/integrations/esphome/) serial proxy. For more details, refer to [setting up a serial connection](https://www.home-assistant.io/integrations/serial/#setting-up-a-serial-connection-in-home-assistant).

1. Set each amplifier to its normal operating mode, with the default one-to-one trigger mapping.
2. If you connect multiple amplifiers in a daisy chain, give each one a different PAC address from 1 to 9 before connecting the chain. The integration reads existing addresses; it does not change the address stored in an amplifier.
3. If you use a raw TCP serial server, configure its serial port for 19200 baud, 8 data bits, no parity, 1 stop bit, and no flow control.

For an ESPHome connection, use an [ESPHome serial proxy](https://www.home-assistant.io/integrations/serial/#setting-up-an-esphome-serial-proxy). The proxy's UART must be dedicated to this integration; remove any previous amplifier polling scripts and template switches from that UART.

## Configuration

To add the **ADA RS-232** hub to your Home Assistant instance, use this My button:

[Add ADA RS-232 to Home Assistant](https://my.home-assistant.io/redirect/config_flow_start/?domain=ada_rs232)

<details open>
<summary>Manual configuration steps</summary>

If the above My button doesn't work, you can also perform the following steps manually:

- Browse to your Home Assistant instance.
- Go to [**Settings > Devices & services**](https://my.home-assistant.io/redirect/integrations/).
- In the bottom right corner, select the **Add integration** button.
- From the list, select **ADA RS-232**.
- Follow the instructions on screen to complete the setup.

</details>

Select your serial connection. Setup scans for responding amplifiers without changing their settings or zone power states. If one available amplifier responds, it is selected automatically. If several respond, select one from the discovered list. Addresses that already have an integration entry are excluded from the list.

**Port**

The local serial port or ESPHome serial proxy connected to your amplifier. You can also enter a network serial server URL manually.

**Amplifier**

The existing PAC address of the amplifier to add. This field is shown only when several available amplifiers respond to the scan.

### Adding daisy-chained amplifiers

You can connect up to nine uniquely addressed amplifiers to one serial connection. Connect the RS-232 output of one amplifier to the RS-232 input of the next.

To add another amplifier in the chain, go to [**Settings** > **Devices & services**](https://my.home-assistant.io/redirect/integrations/), select **ADA RS-232**, and select **Add hub**. Select the same serial connection. Setup scans the chain again and offers addresses that are not already configured. Each amplifier gets its own device and zone switches, while all entries on that port share one serial connection.

## Supported functionality

### Switches

- **Zone 1** through **Zone 8**
  - **Description**: Controls power to a stereo output pair and reports the output state received from the amplifier.

Each amplifier's switches belong to one device.

You can turn a zone on or off from its switch entity or use the standard [switch actions](https://www.home-assistant.io/integrations/switch/). Hardware-trigger changes update these same switches when feedback arrives or at the next poll. The PAC controller does not provide serial volume, mute, source selection, or playback controls.

## Data updates

The integration polls each configured amplifier every 60 seconds and updates its switches when feedback arrives. After a zone command, it reads the output states again before reporting the result. Home Assistant reads the existing state when it starts; it does not restore or send saved zone states.

If communication fails, the affected switches become unavailable. A shared-connection failure can affect all amplifiers on that connection. The next scheduled poll attempts to reconnect.

## Known limitations

- Hardware voltage triggers and the amplifier's bypass control can override serial commands. A zone can remain on after you turn its switch off if a hardware trigger keeps that output active.
- Feedback reports output states without identifying whether a hardware trigger or a serial command enabled them. Preserving an externally enabled output in a later command can also keep it enabled through serial control.
- Independent zone switches require default one-to-one trigger mappings. Custom trigger mappings are not supported.
- Hardware configuration, including stored addresses, trigger mappings, and Quick Turn On, is not changed by the integration.
- Operation with multiple physical amplifiers in a daisy chain has not been verified on hardware.

## Removing the integration

### To remove an integration instance from Home Assistant

1. Go to [**Settings** > **Devices & services**](https://my.home-assistant.io/redirect/integrations/) and select the integration card.
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

Removing an amplifier entry leaves its zone power states unchanged. The shared serial connection closes when the last entry using it is removed. No additional amplifier cleanup is required.

---

[Proposed documentation source](https://github.com/RebbePod/home-assistant.io/blob/add-ada-rs232/source/_integrations/ada_rs232.markdown) · [Core PR description](core-pr.md) · [Documentation PR description](docs-pr.md) · [Branding PR description](brands-pr.md)
