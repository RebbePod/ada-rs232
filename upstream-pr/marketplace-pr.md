<!--
DO NOT REQUEST REVIEWS, THAT IS JUST RUDE, IF YOU DO THE PULL REQUEST WILL BE CLOSED!
Make sure to check out the guide here: https://hacs.xyz/docs/publish/start
-->
## Checklist

<!-- Do not open a pull request before you have completed all these, it will be closed. -->

- [x] I've read the [publishing documentation](https://hacs.xyz/docs/publish/start).
- [x] I've added the [HACS action](https://hacs.xyz/docs/publish/action) to my repository.
- [x] (For integrations only) I've added the [hassfest action](https://developers.home-assistant.io/blog/2020/04/16/hassfest/) to my repository.
- [x] The actions are passing without any disabled checks in my repository.
- [x] I've added a link to the action run on my repository below in the links section.
- [x] I've created a new release of the repository after the validation actions were run successfully.

## Links

<!-- Do not open a pull request before you have provided all these, it will be closed. -->

Link to current release: https://github.com/RebbePod/ada-rs232/releases/tag/v0.2.2
Link to successful HACS action (without the `ignore` key): https://github.com/RebbePod/ada-rs232/actions/runs/43464267062/job/132019046274
Link to successful hassfest action (if integration): https://github.com/RebbePod/ada-rs232/actions/runs/43464267062/job/132019046315

<!-- tid:73253df5-5376-4e68-8c16-b234da6a2de3 -->

Adds ADA RS-232, a stable local integration for Audio Design Associates PAC amplifiers over USB/RS-232, ESPHome native serial proxies, or network serial connections. The full package includes zone power switches, automatic address discovery, shared daisy-chain transports, explicit trigger/setup actions, optional output sensors, and diagnostics. Brand images are bundled in the integration's `brand/` directory.

The repository owner confirmed PTM-1645 zone switching and automatic discovery on physical hardware through ESPHome. Setup actions, physical daisy chains, and PTM-8100 support have automated coverage and still need hardware verification. The release passes 58 Home Assistant tests with 99% statement coverage, plus Ruff lint and formatting checks.
