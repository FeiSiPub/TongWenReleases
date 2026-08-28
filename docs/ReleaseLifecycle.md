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

## Release title and notes contract

Every source Release and its public mirror use the exact immutable title `同文 vX.Y.Z`, where the
version matches the Release Tag. The GitHub `Latest` and `Pre-release` badges are the only release
state indicators; titles must not include changing labels such as “current stable”, “latest”, or a
feature theme. User-facing themes, fixes, upgrade notes and limitations belong in the Release Notes.

## Download presentation

The public Release body begins with a direct `下载 Windows 安装包 (MSI)` link. It is the supported
download entry for end users, followed by a short `SHA256SUMS.txt` verification reminder, the source
Release Notes, and one source-Release backlink. GitHub automatically renders `Source code (zip)` and
`Source code (tar.gz)` for every tagged Release; they are repository snapshots, not Tongwen installer
packages or a supported source distribution. Keep the MSI link prominent rather than presenting those
generated archives as product downloads.

For a published stable Release, successful mirroring is the prerequisite for the source workflow
to request the website policy sync. The website verifies this Release is not draft/prerelease and
has the matching MSI plus `SHA256SUMS.txt` before it advances the client update-policy URL and
publishes both static site profiles. Beta, draft and prerelease assets never update the stable
policy. If this final sync fails, rerun the same stable Tag after repairing the external condition;
do not create a fictitious version to hide the partial publication.

Related operational documentation:

- Source release operations: <https://github.com/FsDiG/TongWen/blob/main/docs/guides/StableUpdateReleaseOperations.md>
- Client lifecycle decision: <https://github.com/FsDiG/TongWen/blob/main/docs/adr/0015-StableUpdatePolicyAndVersionRetirement.md>
- Website policy operations: <https://github.com/FeiSiPub/feisi-website/blob/main/docs/tongwen-release-lifecycle.md>
- Live stable policy: <https://fscad.xyz/updates/tongwen/stable.json>

## Stable-policy release history

| Version | Purpose | MSI SHA-256 |
| --- | --- | --- |
| [`v0.2.22`](https://github.com/FeiSiPub/TongWenReleases/releases/tag/v0.2.22) | First stable baseline containing the policy client | `6b57352aab1f59f12c69eaaf863d5fdb151ed50f43a932d5b778d20695cc4dfb` |
| [`v0.2.23`](https://github.com/FeiSiPub/TongWenReleases/releases/tag/v0.2.23) | First stable upgrade target used to verify the grace-period lifecycle | `f62667e2c46e61ed5c0d514d0cc486f12a1e8a623000bcfd2c59cdcfb8e2f067` |
| [`v0.2.24`](https://github.com/FeiSiPub/TongWenReleases/releases/tag/v0.2.24) | Current stable version; includes the installer completion-page product-link correction | `c773a9b178060cfad61479dc60038a014afca82ba62675455f0ebcfaf6e4b5c2` |

The `v0.2.22` / `v0.2.23` validation pair was built from source commit
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
Get-FileHash .\TongWen_Installer_v0.2.24.msi -Algorithm SHA256
```

## Maintenance rules

- A stable Release must not be published here before the source workflow has built and audited its
  MSI.
- Every mirrored Tag must have exactly one matching MSI and one `SHA256SUMS.txt`.
- Release titles, source-authored notes, stable/prerelease status, asset size and SHA-256 must match
  the source Release. The public workflow prepends the supported MSI direct-download section and
  appends one source-Release backlink to the notes; those expected wrappers are not drift.
- Titles must be exactly `同文 vX.Y.Z`. Keep the version theme in Release Notes and use GitHub's
  `Latest` / `Pre-release` badges for release state.
- Do not manually upload internal symbols, debug files, credentials or source-only artifacts.
- The website must not raise `latest_version` or `minimum_supported_version` until the corresponding
  public stable MSI is available here.
- If mirroring fails, rerun the same source Tag after fixing the external condition. Do not invent a
  new version merely to hide a partial upload.
