Ideas, links, and resources captured for triage. Newest first.
Triaged via `/triage-inbox` skill. Processed items are deleted — the inbox is a queue, not an archive.

## Untriaged

- 2026-05-06 - From Conductor inbox: OpenAI's 2026-05-05 GPT-5.5
  Instant release says the ChatGPT default now uses GPT-5.5 Instant and the
  API exposure is `chat-latest`. Treat this as a cheap/default-lane challenger,
  not a repeat of the April GPT-5.5 frontier sweep. First pass: run
  `scripts/discover-models.py` to confirm the callable slug and pricing, then
  add it only to fast/default text lanes where GPT-5.4 mini/nano or GPT-5.4
  currently compile, normalize, or judge pipeline outputs. Compare quality,
  latency, and cost before touching defaults; do not rerun the full GPT-5.5
  Pro/frontier matrix unless the default-lane screen wins. Source:
  https://openai.com/index/gpt-5-5-instant/
