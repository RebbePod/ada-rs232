<!--
  You are amazing! Thanks for contributing to our project!
  Please, DO NOT DELETE ANY TEXT from this template! (unless instructed).
-->
## Proposed change
<!--
  Describe the big picture of your changes here to communicate to the
  maintainers why we should accept this pull request. If it fixes a bug
  or resolves a feature request, be sure to link to that issue in the
  additional information section.
-->

Add local zone-power control for the Audio Design Associates PTM-1645 using its PAC RS-232 connection. The initial user flow selects a native serial port or proxy, scans existing addresses without changing hardware settings, and selects a single available amplifier or offers a dropdown. Each amplifier exposes eight feedback-confirmed zone switches; addressed entries share one serial connection and command queue.

The public MIT-licensed [ada-rs232 0.2.0 library](https://pypi.org/project/ada-rs232/0.2.0/) owns the protocol and transport. [Matching source, release, and changelog](https://github.com/RebbePod/ada-rs232-python/releases/tag/v0.2.0). Core reads current state before exposing switches, polls every 60 seconds, handles incoming feedback, and releases shared connections after the last owner unloads. Hardware triggers can override serial control; the documentation explains the feedback and trigger-mapping limitations.

This first contribution declares Bronze and includes one switch platform and the initial user flow only. It excludes custom actions, output sensors, diagnostics, options, reconfiguration, and PTM-8100 support. The serial selector and setup style follow Denon RS-232.

The contributor tested zone control and automatic amplifier discovery on a physical PTM-1645 through ESPHome using HACS v0.2.1 and the same published library. The new Core wrapper is tested through Home Assistant interfaces. Multiple physical daisy-chained amplifiers have not been tested.

Validation:

- 22 Core tests and 16 snapshots pass. Config-flow coverage is 53/53 lines; all six modules are at least 96% covered.
- The complete prescribed prek suite passes, including Ruff, strict mypy, pylint, generated requirements, and full hassfest.
- Library CI passes on Python 3.12, 3.13, and 3.14; its 54 tests pass, and wheel/source distributions are public.
- Companion branding assets are prepared and validated; upstream availability remains a merge prerequisite.

## Type of change
<!--
  What type of change does your PR introduce to Home Assistant?
  NOTE: Please, check only 1! box!
  If your PR requires multiple boxes to be checked, you'll most likely need to
  split it into multiple PRs. This makes things easier and faster to code review.
-->

- [ ] Dependency upgrade
- [ ] Bugfix (non-breaking change which fixes an issue)
- [x] New integration (thank you!)
- [ ] New feature (which adds functionality to an existing integration)
- [ ] Deprecation (breaking change to happen in the future)
- [ ] Breaking change (fix/feature causing existing functionality to break)
- [ ] Code quality improvements to existing code or addition of tests

## Additional information
<!--
  Details are important, and help maintainers processing your PR.
  Please be sure to fill out additional details, if applicable.
-->

- This PR fixes or closes issue: Not applicable (new integration).
- This PR is related to issue: Not applicable.
- Link to documentation pull request: Pending submission; [prepared documentation diff](https://github.com/home-assistant/home-assistant.io/compare/next...RebbePod:add-ada-rs232).
- Link to contributors documentation pull request: Not applicable.
- Link to frontend pull request: Not applicable.

Brands companion: pending submission; [prepared branding diff](https://github.com/home-assistant/brands/compare/master...RebbePod:add-ada-rs232).

## Checklist
<!--
  Put an `x` in the boxes that apply. You can also fill these out after
  creating the PR. If you're unsure about any of them, don't hesitate to ask.
  We're here to help! This is simply a reminder of what we are going to look
  for before merging your code.

  AI tools are welcome, but contributors are responsible for *fully*
  understanding the code before submitting a PR. Please follow our AI policy:
  https://contributors.home-assistant.io/start/ai-policy/
-->

- [ ] I understand the code I am submitting and can explain how it works.
- [x] The code change is tested and works locally.
- [x] Local tests pass. **Your PR cannot be merged unless tests pass**
- [x] There is no commented out code in this PR.
- [x] I have followed the [development checklist][dev-checklist]
- [x] I have followed the [perfect PR recommendations][perfect-pr]
- [x] The code has been formatted using Ruff (`ruff format homeassistant tests`)
- [x] Tests have been added to verify that the new code works.
- [ ] Any generated code has been carefully reviewed for correctness and compliance with project standards.

If user exposed functionality or configuration variables are added/changed:

- [x] Documentation added/updated for [www.home-assistant.io][docs-repository]

If the code communicates with devices, web services, or third-party tools:

- [x] The [manifest file][manifest-docs] has all fields filled out correctly.  
      Updated and included derived files by running: `python3 -m script.hassfest`.
- [x] New or updated dependencies have been added to `requirements_all.txt`.  
      Updated by running `python3 -m script.gen_requirements_all`.
- [x] For the updated dependencies a diff between library versions and ideally a link to the changelog/release notes is added to the PR description.

<!--
  This project is very active and we have a high turnover of pull requests.

  Unfortunately, the number of incoming pull requests is higher than what our
  reviewers can review and merge so there is a long backlog of pull requests
  waiting for review. You can help here!
  
  By reviewing another pull request, you will help raise the code quality of
  that pull request and the final review will be faster. This way the general
  pace of pull request reviews will go up and your wait time will go down.
  
  When picking a pull request to review, try to choose one that hasn't yet
  been reviewed.

  Thanks for helping out!
-->

To help with the load of incoming pull requests:

- [ ] I have reviewed two other [open pull requests][prs] in this repository.

[prs]: https://github.com/home-assistant/core/pulls?q=is%3Aopen+is%3Apr+-author%3A%40me+-draft%3Atrue+-label%3Awaiting-for-upstream+sort%3Acreated-desc+review%3Anone+-status%3Afailure

<!--
  Thank you for contributing <3

  Below, some useful links you could explore:
-->
[dev-checklist]: https://contributors.home-assistant.io/core/development/checklist/
[manifest-docs]: https://contributors.home-assistant.io/core/integrations/manifest/
[quality-scale]: https://contributors.home-assistant.io/core/quality-scale/
[docs-repository]: https://github.com/home-assistant/home-assistant.io
[perfect-pr]: https://contributors.home-assistant.io/start/pull-requests/#before-you-open-it
