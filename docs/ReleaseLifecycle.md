# Tongwen Release Lifecycle

This repository is the public binary distribution boundary for Tongwen. It does not build the
application and does not decide which installed versions remain supported.

## Repository relationship

| Boundary | Repository | Responsibility |
| --- | --- | --- |
| Product source and build | [`FsDiG/TongWen`](https://github.com/FsDiG/TongWen) | Source code, contracts, release workflow, MSI build and internal symbols |
| Website update policy | [`FeiSiPub/feisi-website`](https://github.com/FeiSiPub/feisi-website) | Publishes the static stable policy used by Tongwen clients |
| Public downloads | [`FeiSiPub/TongWenReleases`](https://github.com/FeiSiPub/TongWenReleases) | Mirrors user-facing MSI packages and `SHA256SUMS.txt` |

The source release workflow creates a Release in `FsDiG/TongWen` and then mirrors the same Tag,
release notes, MSI and checksum file here. Internal Sentry symbols, PDB files and Reactor mapping
files are intentionally not public assets.

Mirroring a public Release does **not** update the client update-policy URL. The release workflow
does not write to the website repository; after the public MSI is verified, a release owner must
make an explicit, reviewed change to `feisi-website`'s `stable.json`. That website commit then
automatically publishes both static site profiles. This deliberate separation prevents a new Tag
from accidentally starting the old-version grace period.

Related operational documentation:

- Source release operations: <https://github.com/FsDiG/TongWen/blob/main/docs/guides/StableUpdateReleaseOperations.md>
- Client lifecycle decision: <https://github.com/FsDiG/TongWen/blob/main/docs/adr/0015-StableUpdatePolicyAndVersionRetirement.md>
- Website policy operations: <https://github.com/FeiSiPub/feisi-website/blob/main/docs/tongwen-release-lifecycle.md>
- Live stable policy: <https://fscad.xyz/updates/tongwen/stable.json>

## Initial stable-policy release pair

| Version | Purpose | MSI SHA-256 |
| --- | --- | --- |
| [`v0.2.22`](https://github.com/FeiSiPub/TongWenReleases/releases/tag/v0.2.22) | First stable baseline containing the policy client | `6b57352aab1f59f12c69eaaf863d5fdb151ed50f43a932d5b778d20695cc4dfb` |
| [`v0.2.23`](https://github.com/FeiSiPub/TongWenReleases/releases/tag/v0.2.23) | Current stable version and upgrade target | `f62667e2c46e61ed5c0d514d0cc486f12a1e8a623000bcfd2c59cdcfb8e2f067` |

Both packages were built from source commit
`9a86100fa33314eb3941eb44b7960f3149c6930a`. They share the same feature source but carry distinct
assembly/MSI versions so the `v0.2.22` to `v0.2.23` discovery, grace-period and Windows Installer
upgrade path can be tested without claiming an additional feature difference.

The MSI packages currently do not carry an Authenticode publisher signature. Windows may therefore
display an unknown-publisher warning. `SHA256SUMS.txt` verifies download integrity but is not a
substitute for publisher identity signing.

## User verification

1. Download the MSI and `SHA256SUMS.txt` from the same Release Tag.
2. Calculate the local MSI SHA-256 and compare it with the checksum file.
3. Prefer the current stable Release unless a test procedure explicitly requires the baseline
   package.
4. Install upgrades manually. Tongwen does not automatically download or execute an MSI.

PowerShell example:

```powershell
Get-FileHash .\TongWen_Installer_v0.2.23.msi -Algorithm SHA256
```

## Maintenance rules

- A stable Release must not be published here before the source workflow has built and audited its
  MSI.
- Every mirrored Tag must have exactly one matching MSI and one `SHA256SUMS.txt`.
- Release titles, source-authored notes, stable/prerelease status, asset size and SHA-256 must match
  the source Release. The public workflow appends one source-Release backlink to the notes; that
  expected backlink is not drift.
- Do not manually upload internal symbols, debug files, credentials or source-only artifacts.
- The website must not raise `latest_version` or `minimum_supported_version` until the corresponding
  public stable MSI is available here.
- If mirroring fails, rerun the same source Tag after fixing the external condition. Do not invent a
  new version merely to hide a partial upload.
