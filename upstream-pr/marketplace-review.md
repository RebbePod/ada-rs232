# Full Marketplace package and catalog submission

**Stable v0.2.2 is published and installable now.** After the repository owner
confirmed personal review, understanding, and approval, the public catalog
listing was submitted as [PR #14106](https://github.com/hacs/default/pull/14106).
It is open for maintainer review and allows maintainer edits.

## What users get

The complete stable custom integration retains eight PTM-1645 zone switches,
automatic amplifier discovery, shared daisy-chain connections, trigger-mask and
broadcast all-off actions, hardware setup/readback actions, optional output
sensors, reconfiguration, diagnostics, and the supplied ADA artwork. PTM-8100
model support remains available with its documented hardware-testing limitation.

The small initial Bronze Core proposal stays separate. This Marketplace
submission adds the existing full custom package to the catalog used by both the
Marketplace and HACS.

## Review the exact changes

- [Stable release v0.2.2](https://github.com/RebbePod/ada-rs232/releases/tag/v0.2.2)
- [Full integration source at the release revision](https://github.com/RebbePod/ada-rs232/tree/726cfb3634a6b3659aafa376b8ef10ec2a68903f/custom_components/ada_rs232)
- [Changes since v0.2.1](https://github.com/RebbePod/ada-rs232/compare/v0.2.1...v0.2.2)
- [Catalog diff: one added repository name](https://github.com/hacs/default/compare/master...RebbePod:add-ada-rs232)
- [Exact submitted catalog PR description](marketplace-pr.md)
- [Installation and full functionality guide](https://github.com/RebbePod/ada-rs232/blob/v0.2.2/README.md)

The catalog change adds this one line to the alphabetically sorted `integration`
list in `hacs/default`:

```json
"RebbePod/ada-rs232"
```

It points to the repository; it does not copy the integration code into the
catalog. The catalog maintainers decide whether to merge it. The integration is
already installable from its link while that decision is pending.

## Correctness review

The v0.2.2 runtime change preserves a replacement connection if two old cleanup
operations overlap. Before the fix, the second old close could delete the new
connection's registry entry. Cleanup now removes a record only when it is still
the same record that was closed and has no owners.

A new regression test controls the close order with async events, confirms the
replacement transport is reused, checks shared timeout updates, and confirms it
closes only after its final owner releases it. The test fails on v0.2.1's cleanup
and passes with the fix. The remaining changes update Marketplace installation
instructions and synchronize the package version at 0.2.2.

## Validation

- 58 Home Assistant tests pass; statement coverage is 99%.
- Ruff lint and formatting pass; the dependency lock is current.
- [Marketplace/HACS validation](https://github.com/RebbePod/ada-rs232/actions/runs/43464267062/job/132019046274) passes without ignored checks.
- [Hassfest](https://github.com/RebbePod/ada-rs232/actions/runs/43464267062/job/132019046315) passes.
- The full stable release was published after these validations succeeded.
- [Upstream catalog checks](https://github.com/hacs/default/actions/runs/43483775597)
  pass, including owner, release, maintainer-edit permission, core domain
  conflict, repository status, HACS validation, and hassfest checks.
- [Catalog lint checks](https://github.com/hacs/default/actions/runs/43483764843)
  pass, including JSON schema, JSON syntax, and sorting. The diff adds exactly
  one line.
- The release archive contains 22 integration files, including all eight brand
  images, and its manifest identifies version 0.2.2.

The owner confirmed zone switching and automatic discovery on a physical
PTM-1645 through ESPHome. Hardware setup actions, physical daisy chains, and
PTM-8100 support still need hardware verification. Automated tests do not replace
that hardware validation.

## Submission status

The owner confirmed personal review, understanding, and approval of the catalog
submission. All upstream automated checks pass. The PR is open in the maintainer
review queue; the package is not in the default catalog until it is merged.

This approval applies to the Marketplace catalog submission. The separate Core,
documentation, and brands submissions retain their own pending review.

## Comparison with other open catalog PRs

On November 13, 2026, the audit sampled the 100 most recently updated open
`hacs/default` PRs and read 32 substantive maintainer reviews across 22 of those
submissions. This is a sample of the open queue, not an assertion that every open
PR was examined. The comparison used the published v0.2.2 source at `726cfb3`
and its pinned `ada-rs232` 0.2.0 library, rather than this review branch's older
custom-component files.

### Remaining hardware-validation risk

Maintainers requested removal or physical verification of untested setting
writes in [Reef Factory Local](https://github.com/hacs/default/pull/13395#pullrequestreview-5877846902)
and [Centrometal](https://github.com/hacs/default/pull/13531#pullrequestreview-5826026359).
The [Envisalink review](https://github.com/hacs/default/pull/11057#pullrequestreview-5764587324)
also required confirmed programming mode before sending setting commands.

This is relevant to ADA's trigger mapping, Quick Turn On, stored-address, and
trigger-default writes: physical testing of these actions and their setup-screen
readback has not been confirmed. PTM-8100 and physical multi-amplifier testing
also remain unconfirmed. Zone switching and automatic PTM-1645 discovery are the
two hardware-tested paths reported by the owner.

ADA already requires administrator access, a single loaded connection owner,
physical setup mode, a completely parsed setup screen, and command readback.
Mapping uncertainty is persisted before a write, and Quick Turn On reads the
current value before toggling. These are useful protections, but neither these
guards nor emulator tests establish actual firmware compatibility. The
single-amplifier confirmation is a user's assertion: software cannot count
physically connected amplifiers in setup mode.

**This remains a potential catalog review blocker.** The reviewers have not
reviewed our submission yet, so their decision cannot be predicted from other
PRs. Physical validation is the next priority. If that cannot be completed, the
unverified write paths may need to be withheld from the catalog-facing release.
The audit did not remove the full package's requested features, change the
release, or mark the catalog PR as draft.

### Other recurring problems checked

| Problem in open PRs | ADA v0.2.2 finding |
| --- | --- |
| [Configuration writes available to ordinary users](https://github.com/hacs/default/pull/12316#pullrequestreview-5764383679) | Every custom PAC action uses `async_register_admin_service`. The permission test confirms a non-admin cannot reach hardware setup. Normal zone switching uses standard entity permissions. |
| [Probing unrelated serial adapters and missing dependencies](https://github.com/hacs/default/pull/13569#pullrequestreview-5877849649) | A read-only GA query is sent only to the port the user selected. There is no automatic sweep of USB or UART devices. The manifest pins the published protocol library, which declares serialx as a dependency. |
| [Unknown values overwritten with guessed defaults](https://github.com/hacs/default/pull/13535#pullrequestreview-5877847848) | Zone updates first read current output state under the shared transaction lock. A failed read sends no write; tests verify this and preservation of other zones during concurrent changes. Explicit mask actions require all eight bits. |
| [Stale state and competing sessions](https://github.com/hacs/default/pull/9491#pullrequestreview-5058841046) | Entries share a bus and transaction lock. Failures mark entities unavailable; a later poll reconnects. Whole-chain queries invalidate missing amplifiers. Failed commands are not silently replayed. |
| [Blocking filesystem calls and registry-wide deletion](https://github.com/hacs/default/pull/13465#pullrequestreview-5825325973) | The reviewed runtime paths have no direct filesystem stat/read/write operations or registry-wide entity removal. Transport selection in serialx runs in an executor. |
| [Broken options flow and exposed diagnostics](https://github.com/hacs/default/pull/10373#pullrequestreview-5566460681) | The options flow uses the base class's `config_entry` property. Diagnostics omit the connection endpoint and credentials. No raw request, password, or header dumps are added by the ADA code. |
| [Incorrect configuration documentation](https://github.com/hacs/default/pull/10733#pullrequestreview-5568334331) | The README matches Port + Model selection, conditional discovered-amplifier selection, options, and reconfiguration. Actions match the shipped forms. English translations equal `strings.json`. |
| [Missing version floor](https://github.com/hacs/default/pull/9491#pullrequestreview-5058841046) | `hacs.json` declares Home Assistant 2026.11.0. Serial port selection, the options property, and `async_unload_platforms_or_raise` were checked in that exact Core tag. |
| [Missing licenses, lost saved data, and release contents](https://github.com/hacs/default/pull/8293#pullrequestreview-4987376862) | The repository has an MIT license; the library declares its own license. Brand provenance and its separate trademark status are documented. Settings use config-entry storage rather than the replaceable install directory. All 22 archive files match stable source, include all eight distinct brand variants, and exclude bytecode. No frontend bundle or runtime CDN import is used. |
| [Catalog conflicts](https://github.com/hacs/default/pull/9160#pullrequestreview-5060442243) | Our PR is mergeable, adds one repository line, allows maintainer edits, and passes all 13 current checks. Historical canceled runs were superseded by the successful labeled run. Maintainer approval is still pending. |

The relevant Home Assistant flow, permissions, setup-guard, connection, and
lifecycle tests were rerun against stable source: **50 passed**. Ruff lint and
formatting also passed. The prior complete release run includes all eight
branding HTTP tests, for 58 total tests. No runtime code changes were needed for
the issues checked above; hardware validation remains outstanding.

Once the catalog PR is merged, the README should lead with searching for ADA
RS-232 in the Marketplace and retain Add from link as a fallback. Multiple
reviewers requested that documentation change after listing. While the PR is
pending, the current Add from link instructions describe the available route
accurately. No comments, review requests, or unrelated catalog updates were sent
as part of this audit.
