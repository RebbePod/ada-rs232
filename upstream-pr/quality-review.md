# Bronze quality review

Target: `quality_scale: bronze`, PTM-1645, switch platform and initial user flow
only. This is an AI-assisted technical review, not an upstream approval or a
replacement for the contributor's personal review.

## Bronze rules

The review used the exact current requirements for all 20 Bronze rules and
Home Assistant's integration-review skill. The manifest remains Bronze. The
scorecard includes all 54 keys required by hassfest; higher-tier work is left
`todo` or marked intrinsically exempt where it does not apply.

| Rule | Result and evidence |
| --- | --- |
| [`action-setup`](https://contributors.home-assistant.io/core/quality-scale/rules/action-setup/) | Exempt: no custom actions are registered. |
| [`appropriate-polling`](https://contributors.home-assistant.io/core/quality-scale/rules/appropriate-polling/) | Fixed 60-second polling plus feedback; polling is not configurable. |
| [`brands`](https://contributors.home-assistant.io/core/quality-scale/rules/brands/) | **External availability pending.** Eight assets are prepared and validated in the companion fork; they must be available upstream before Core merges. |
| [`common-modules`](https://contributors.home-assistant.io/core/quality-scale/rules/common-modules/) | Coordinator and typed shared-connection ownership live in separate common modules. |
| [`config-flow`](https://contributors.home-assistant.io/core/quality-scale/rules/config-flow/) | Native serial-port selector, read-only scan, and discovered-address dropdown. |
| [`config-flow-test-coverage`](https://contributors.home-assistant.io/core/quality-scale/rules/config-flow-test-coverage/) | 53/53 config-flow lines covered; known, unexpected, and empty-scan errors recover to `CREATE_ENTRY`; duplicates abort. |
| [`dependency-transparency`](https://contributors.home-assistant.io/core/quality-scale/rules/dependency-transparency/) | Public MIT-licensed `ada-rs232==0.2.0`, tagged source, wheel and source distribution, public build/publish CI. |
| [`docs-actions`](https://contributors.home-assistant.io/core/quality-scale/rules/docs-actions/) | Exempt: standard switch actions only. |
| [`docs-conditions`](https://contributors.home-assistant.io/core/quality-scale/rules/docs-conditions/) | Exempt: no custom conditions. |
| [`docs-high-level-description`](https://contributors.home-assistant.io/core/quality-scale/rules/docs-high-level-description/) | Documentation describes the amplifier, connection, and zone-power use. |
| [`docs-installation-instructions`](https://contributors.home-assistant.io/core/quality-scale/rules/docs-installation-instructions/) | UI setup, serial prerequisites, default mappings, and unique physical addresses are documented. |
| [`docs-removal-instructions`](https://contributors.home-assistant.io/core/quality-scale/rules/docs-removal-instructions/) | Shared removal template and last-owner connection cleanup are documented. |
| [`docs-triggers`](https://contributors.home-assistant.io/core/quality-scale/rules/docs-triggers/) | Exempt: no Home Assistant triggers are provided. |
| [`entity-event-setup`](https://contributors.home-assistant.io/core/quality-scale/rules/entity-event-setup/) | `CoordinatorEntity` manages entity subscriptions; coordinator shutdown releases the library subscription and ownership. |
| [`entity-unique-id`](https://contributors.home-assistant.io/core/quality-scale/rules/entity-unique-id/) | Stable config-entry ID plus zone number. |
| [`has-entity-name`](https://contributors.home-assistant.io/core/quality-scale/rules/has-entity-name/) | Entities use translated zone names under an amplifier device. |
| [`runtime-data`](https://contributors.home-assistant.io/core/quality-scale/rules/runtime-data/) | Typed coordinator runtime data and typed `HassKey` for the shared registry. |
| [`test-before-configure`](https://contributors.home-assistant.io/core/quality-scale/rules/test-before-configure/) | Read-only GA scan before an entry is created; temporary ownership is released even on cancellation. |
| [`test-before-setup`](https://contributors.home-assistant.io/core/quality-scale/rules/test-before-setup/) | First coordinator refresh completes before the switch platform is forwarded. |
| [`unique-config-entry`](https://contributors.home-assistant.io/core/quality-scale/rules/unique-config-entry/) | Port/address pairs are filtered and checked again after selection; no hardware identity is fabricated. |

The locally checkable rules pass or are exempt as stated. The external brands
condition remains open; the integration must not be described as having an
awarded Bronze tier yet.

## Test evidence

The Core suite passes 22 tests and 16 entity/state snapshots against the public
PyPI wheel on upstream `cdba0080`, with its updated runtime and Ruff 0.17.4 pins. Measured line coverage:

| Module | Covered / total |
| --- | --- |
| `__init__.py` | 20 / 20 |
| `config_flow.py` | 53 / 53 |
| `connection.py` | 24 / 25 |
| `const.py` | 2 / 2 |
| `coordinator.py` | 48 / 48 |
| `switch.py` | 30 / 30 |

Tests exercise actual Home Assistant config-entry and switch-service interfaces.
They cover read-only setup, automatic and multiple-address selection, duplicate
rechecks, error recovery, cancellation, overlapping probe cleanup, shared bus
ownership, addressed feedback, hardware overrides, command failures,
reconnection, shutdown, and successful/failed unloads. A review found and fixed
an overlapping-close race by checking registry-record identity before removal.

Independent library validation: 54 tests pass (335/344 lines covered), strict
mypy passes all five source modules, Ruff check/format pass, and public CI passes
on Python 3.12, 3.13, and 3.14. Its tests include a real serialx pseudo terminal,
framing, concurrent writes, late address-9 broadcast replies, and disconnects.

The contributor confirmed physical PTM-1645 zone control and automatic discovery
through ESPHome. Physical daisy-chain operation, setup actions, and PTM-8100
operation are not claimed as tested by this submission.

## Repository checks

The following required checks pass with the repository's pinned environment:

- Ruff check and format, codespell, JSON, YAML, and Prettier.
- Strict mypy, pylint, generated requirements, full hassfest, and strict-typing
  configuration validation through the prescribed `prek` command.
- Documentation remark and textlint, plus independent source/UI review.
- Eight PNGs checked for dimensions, transparency, pairing, and distinct data.

The full development bootstrap was attempted earlier and encountered an unrelated
DTLSSocket/autoconf build failure on this Mac. Required pinned runtime, test,
and validation dependencies were installed explicitly. Mypy workers need local
IPC and therefore run outside the filesystem/network sandbox. Optional native
TurboJPEG acceleration is unavailable and does not fail the integration tests.

## Future work outside this PR

Additional HACS features are intentionally excluded. In particular, custom PAC
actions need Core-style global action registration in `async_setup`, translatable
action metadata, complete permissions/error tests, and documented hardware setup
prerequisites. Output sensors, reconfiguration, diagnostics, and other models
should be separate changes after the initial integration is accepted.
