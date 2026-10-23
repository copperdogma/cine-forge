# Media accounting and provider lifecycle — 2026-10-23

Problem class: pricing non-token asynchronous generation, preserving incurred work when a later unit fails, and avoiding duplicate submission after an uncertain job outcome. Arithmetic/identity/provenance belong in deterministic code; no decision model or LLM is justified for ledger math.

## Primary sources inspected

- https://docs.x.ai/developers/models/grok-imagine-video — current output rates USD0.05/second at480p and0.07/second at720p. Input media has separate prices; CineForge's existing xAI video path is prompt-only. These are list-price estimates, not account billing receipts.
- https://ai.google.dev/gemini-api/docs/video — updated2026-10-22; explicitly says Veo3.1 preview models shut down2026-10-22. Replacement Gemini Omni requires a different transport and qualification; Vertex/Enterprise GA rates cannot be applied to this Developer API path.
- https://ai.google.dev/gemini-api/docs/deprecations — current table confirms all configured Imagen4 variants shut down2026-08-17, configured Veo3.1 preview variants2026-10-22.
- https://developers.openai.com/api/docs/models/sora-2 — fetched through official OpenAI Docs; Videos API and Sora2 shut down2026-09-24 with no one-to-one replacement.
- https://developers.openai.com/api/docs/deprecations — corroborates Sora shutdown. Official documentation search returned irrelevant rows before fetching the exact model page; no pricing was inferred from those results.

## Decision

Never treat benchmark metadata as current runtime pricing. Use explicit model/provider/resolution pricing evidence for currently qualified transport, distinguish estimates from confirmed billing, fail before paid work for known retired or unpriced targets, preserve known compiler and successful video costs across partial failure, and retain uncertain submission/job evidence rather than blindly resubmitting. Reuse existing immutable artifacts and driver cost aggregation; add a focused typed cost-bearing failure boundary if needed. No new spend reservation framework, migration compatibility path or automatic provider adoption.

## Remaining uncertainty and next experiment

No live video/image request was made. Catalog discovery earlier today listed chat-capable models, so its success did not establish media endpoint availability. Exact account billing/access, future replacement quality, and crash recovery remain unqualified. Use offline captured transport/module fixtures and driver/API boundaries to prove accounting and no-call failure first. Resume full229 only once current transport and an inspectable execution envelope are established.

## Download credentials — bounded review follow-through

The rewritten transport retained a pre-existing issue: it sent the xAI API bearer key to the response's media download URL. Current official video-generation documentation (https://docs.x.ai/developers/model-capabilities/video/generation, inspected2026-10-23, asynchronous request/status section) authenticates API polling and describes directly accessible temporary hosted media URLs. Adopt the standard separation: authenticate only API submission/polling, download the returned HTTPS media URL without the API bearer header, including redirects. A mocked HTTP boundary can prove header separation without exposing or using any real credential. This is an inference from the documented direct temporary-URL contract; live CDN/account behavior remains untested. No new host allowlist or generic security framework is needed for this narrow credential-separation correction.

## Credential-free offline validation

An integrated mocked test accidentally read a prefixed real xAI key, and a failing header assertion included it in diagnostic output. The persistent log was sanitized; no provider request occurred. The new tests stub credential lookup. For the broad offline run, clear provider variables in the test subprocess and use the installed python-dotenv `PYTHON_DOTENV_DISABLED=1` switch to prevent repository dotenv reload. Run the dedicated dotenv-loading tests separately in a cleared process so their temporary fake `.env` fixtures still exercise real loading. No credentials, local secret files or production settings are changed. Primary guidance inspected: https://github.com/theskumar/python-dotenv (disable-load_dotenv section; installed load_dotenv source confirms support) and https://docs.pytest.org/en/stable/how-to/monkeypatch.html (environment/attribute patching). This is a standard isolation choice, not relaxed assertions.
