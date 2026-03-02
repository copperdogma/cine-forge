# Golden Fixture Inbox

Drop new inputs here for automatic golden output creation.
See `docs/runbooks/golden-build.md` for the convention.

Each input gets its own subdirectory:

```
_inbox/
  new-screenplay-characters/
    input.txt               # the screenplay or excerpt
    notes.txt               # optional: what this tests, what to extract
```

The `/golden-verify` skill picks these up automatically and invokes `/golden-create`
for each one. Or run `/golden-create` directly for immediate processing.
