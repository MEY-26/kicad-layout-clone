# Official KiCad PCM submission

[Türkçe](PUBLISHING.tr.md)

The public project is `MEY-26/kicad-layout-clone`. Its package identifier is
`com.github.mey-26.kicad-layout-clone`. Version 0.3.1 is a Windows testing release.

## Current submission

[Official metadata merge request !683](https://gitlab.com/kicad/addons/metadata/-/merge_requests/683)
was opened on 8 October 2026 and is ready for KiCad maintainer review.
The source branch is being updated for 0.3.1. This is not an accepted catalogue listing.
Installation from the generated PCM catalogue has not been verified.

## Release artifacts

Run `python build_pcm.py` at the repository root. It produces:

- `dist/Layout_Clone-0.3.1-pcm.zip`: installable through PCM's Install from File.
- `dist/SHA256SUMS.txt`: archive integrity hash.
- `dist/submission/packages/com.github.mey-26.kicad-layout-clone/metadata.json`:
  official-repository metadata containing the download URL, hash and sizes.
- `dist/submission/packages/com.github.mey-26.kicad-layout-clone/icon.png`:
  64×64 catalogue icon.

The ZIP's metadata deliberately omits download fields. The version declares
`runtime: ipc`, preventing it from being treated as a legacy SWIG plugin.
Upload the ZIP and checksum to the public GitHub release tagged `v0.3.1`.
Verify that the download works without signing in and matches SHA256SUMS.
Do not replace an archive after its hash is submitted; publish a new version.

## Make it discoverable in the default catalogue

1. Sign in to GitLab and fork [kicad/addons/metadata](https://gitlab.com/kicad/addons/metadata).
2. Create a branch such as `add-layout-clone` in the fork.
3. Copy the generated `packages/com.github.mey-26.kicad-layout-clone/`
   directory into the metadata repository's `packages/` directory.
4. Commit it and open a merge request to the upstream default branch.
   Use [PCM_SUBMISSION.md](PCM_SUBMISSION.md) as the description.
5. Respond to maintainer review. Only after acceptance and catalogue refresh
   should users be told to search for **Layout Clone** in the default PCM list.

A GitHub release and a local ZIP do not constitute an accepted PCM listing.
A GitLab account is needed to submit and maintain the merge request.
KiCad controls acceptance and timing; no guaranteed review deadline exists here.

## Development checks

Install `jsonschema` to run package-validation tests, then:

```sh
python -m unittest discover -s tests -p "test_*.py"
python build_pcm.py
```

Tests use synthetic circuits; the public repository contains no project boards
or schematic files. A GitHub Actions workflow runs these tests and builds the ZIP.
For a runtime smoke test, install the ZIP in a separate KiCad configuration and
try source capture, target capture, preview, apply and undo on a disposable board.

Official references: [PCM packaging and submission](https://dev-docs.kicad.org/en/addons/index.html),
[IPC plugin development](https://dev-docs.kicad.org/en/apis-and-binding/ipc-api/for-addon-developers/).
