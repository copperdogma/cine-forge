# Runbook: npm Supply-Chain Hardening

Use this when an npm compromise, suspicious package release, dependency upgrade,
lockfile change, package-manager install script change, or GitHub Actions
release/workflow change could affect this repo.

## Quick Scan

Run the repo-local scanner from this checkout:

```bash
python3 scripts/npm_supply_chain_scan.py
```

Use strict mode when the check should fail on a known affected package/version
or incident IOC:

```bash
python3 scripts/npm_supply_chain_scan.py --strict
```

If this repo exposes a convenience command, prefer it:

```bash
make supply-chain-scan
npm run supply-chain:scan
```

The scanner is self-contained. It reads this repo's
`docs/security/npm-supply-chain-incidents.json` and scans this checkout's
package manifests, lockfiles, and `.github/workflows` files. It does not call
Conductor and it does not install dependencies.

## When To Run

Run the scanner:

- when triaging an npm, package, dependency, CI, release, or supply-chain
  incident;
- before and after dependency upgrades or lockfile refreshes;
- when changing `package.json`, lockfiles, package-manager scripts, install
  scripts, or workspace package boundaries;
- when changing `.github/workflows`, publish jobs, deploy jobs, cache behavior,
  or OIDC/token permissions;
- during validation when a story or diff touched any of those surfaces.

Do not run it for unrelated product or docs-only triage.

## What Counts As Evidence

- A package name plus affected version in a lockfile is exposure evidence.
- An affected package name in `package.json` without the affected lockfile
  version is a dependency lead, not proof that malware ran.
- An IOC such as a malicious optional dependency, file name, or git ref is
  exposure evidence until disproven.
- A clean related package note, such as TanStack Query in the 2026-05 incident,
  is not an incident finding when official incident sources say that package
  family was clean.
- CI logs and local shell history are needed to prove whether an affected
  install actually executed in a credential-bearing environment.

## GitHub Actions Checklist

Flag workflows that combine untrusted code or dependency installs with
privileged repo context:

- `pull_request_target` plus checkout or execution of fork-controlled code.
- `pull_request_target` plus dependency install, build, test, or cache writes.
- `actions/cache` keys that can be poisoned from untrusted branches and reused
  by privileged jobs.
- `id-token: write` available in jobs that run dependency installs before a
  tightly scoped release step.
- npm publish, package provenance, cloud deploy, or SSH credentials exposed to
  install/build/test jobs instead of only to the final release step.
- Lifecycle scripts allowed during audit-only dependency checks when
  `--ignore-scripts` would be sufficient.

## Response Rule

If a scan finds an affected version or IOC in a credential-bearing local or CI
environment:

1. stop installs from that lockfile or cache;
2. remove `node_modules` and package-manager caches for the affected checkout;
3. rotate credentials available to the install environment;
4. review GitHub, npm, cloud, and provider audit logs for the exposure window;
5. route repo-specific fixes through this repo's normal story/worktree flow.
