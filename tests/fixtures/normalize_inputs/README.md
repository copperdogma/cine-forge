# Normalization Input Fixtures

These are repo-authored, deliberately tiny contract fixtures:

- `valid_screenplay.fountain` is an already-valid passthrough control. Tests
  must preserve its heading, both character names, and both dialogue lines.
- `malformed_screenplay.txt` is a malformed screenplay-like remediation case.
  Tests must recover a parseable heading without losing Mara or the source
  phrase `begin now without proper formatting or structure`.
- `sample_script.fdx` is a minimal Final Draft interoperability control. Tests
  must preserve `INT. GARAGE - NIGHT`, `ALEX`, and `Start the engine.`.

The former `normalize_responses/` files were unreferenced mock artifacts and
were removed during Story 208. They provided no executed test evidence.
