# Full Marketplace package and catalog submission

**Stable v0.2.2 is published and installable now.** The public catalog listing
is prepared but has not been submitted. Automatic approval review requires the
repository owner's personal review and understanding confirmation before the
upstream PR can be opened.

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
- [Exact proposed catalog PR description](marketplace-pr.md)
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
- The catalog JSON passes the repository's sorting script and JSON validation;
  the diff adds exactly one line.
- The release archive contains 22 integration files, including all eight brand
  images, and its manifest identifies version 0.2.2.

The owner confirmed zone switching and automatic discovery on a physical
PTM-1645 through ESPHome. Hardware setup actions, physical daisy chains, and
PTM-8100 support still need hardware verification. Automated tests do not replace
that hardware validation.

## Confirmation needed

After reviewing the release code, the catalog diff, and the exact PR text,
confirm that you understand the changes and approve opening the Marketplace
catalog PR. This confirmation applies to the catalog submission; the separate
Core, documentation, and brands submissions retain their own pending review.
