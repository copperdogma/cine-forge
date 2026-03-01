---
name: discover-models
description: Discover available AI models across all configured providers and compare against eval registry.
user-invocable: true
---

# /discover-models

Query OpenAI, Anthropic, and Google model APIs to see what's available, flag untested models, and identify new SOTA options for eval work.

## Steps

1. **Run the discovery script**:

```bash
.venv/bin/python scripts/discover-models.py --check-new
```

2. **Analyze the output**:
   - Which providers have API keys configured?
   - What models are available that we haven't tested yet?
   - Are there new SOTA models since our last eval run?
   - Are there new cheap models that might be cost-effective alternatives?

3. **Report to user**:
   - Summarize key findings: new models worth testing, missing API keys
   - Highlight models that are likely interesting for eval work (new SOTA, new cheap tier)
   - Skip dated snapshots and aliases — focus on canonical model IDs

4. **Optionally cache results**:

```bash
.venv/bin/python scripts/discover-models.py --cache
```

This writes to `docs/evals/models-available.yaml` for other skills to reference.

## Notes

- The script checks environment variables for API keys: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`
- If a key is missing, the script reports setup instructions
- Models are filtered to chat/completion models only (no embeddings, TTS, image gen, etc.)
- `[TESTED]` means the model appears in `docs/evals/registry.yaml`
- `[NEW]` means it hasn't been evaluated yet
