# Layout Clone 0.2.1

Toolbar icon fix for Windows / KiCad 10.0:

- Separate 24x24 toolbar artwork with a 48x48 high-DPI variant. The toolbar
  no longer uses the 64x64 PCM catalogue icon.
- README screenshots now use an opaque application capture and a new image
  URL so dark GitHub themes and older browser caches do not hide the interface.
- Placement, matching and language behavior are unchanged from 0.2.0.

Close and reopen the PCB Editor after updating so KiCad reloads the toolbar icons.

Community testing release for **Windows / KiCad 10.0**, tested with KiCad 10.0.5.

- English by default; switch to Turkish in the upper-right language selector.
- Language choice is remembered, and switching keeps groups and preview state.
- Capture source and target groups directly from PCB selection.
- Match by connectivity and apply one placement to multiple targets.
- Preview mappings, positions and angles; rotation and centre-only reflection.
- Remove selected targets or remove all targets while retaining the source.
- Native KiCad undo; no automatic board save.

## Install

Download **Layout_Clone-0.2.1-pcm.zip**, then use KiCad's Plugin and Content
Manager → **Install from File…**. Enable the API server in Preferences →
Common → API. Initial dependency installation requires internet access.
Close the schematic editor before applying; this release guards against a
reported KiCad 10 IPC transaction crash. Read the README for limits and DRC.

If upgrading from the private manual build `com.sharkesc.layout-clone`, back up
and remove the old plugin installation before using this community PCM package
to avoid duplicate actions.

The default KiCad PCM catalogue listing requires a separate maintainer-reviewed
metadata submission; this release alone does **not** mean it is listed there.

[English documentation](https://github.com/MEY-26/kicad-layout-clone#readme) ·
[Türkçe açıklama](https://github.com/MEY-26/kicad-layout-clone/blob/main/README.tr.md) ·
[Issue tracker](https://github.com/MEY-26/kicad-layout-clone/issues)

Validation: 22 public-source/package tests passed, including toolbar icon sizes,
manifest references and reproducible packaging. The 0.2.0 development build
passed 58 tests. Linux/macOS and a new real-server placement test for 0.2.1
remain unverified. The installed toolbar still needs visual confirmation after
reopening the PCB Editor.
This is a **prerelease**; use a disposable board copy for your first trial.
MIT licensed. SHA-256 checksums are included in `SHA256SUMS.txt`.
