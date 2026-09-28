# Sonnet 5.5 — coordinator-retained source notes

These are notes from successful Stage1 web retrieval in this conversation on
2026-09-28, not a saved full webpage or independently repeated owner retrieval.
Direct urllib fetching now returns403; owner web retrieval may also fail.

Source: https://platform.claude.com/docs/en/models/sonnet-5-5/whats-new-sonnet-5-5
Successfully retrieved by web.open/click, internal reference turn4view2 /
turn5view0. Relevant displayed lines77-90:

> To turn off up-front thinking on Claude Sonnet 5.5, send `thinking: {"type": "between_tools"}` instead of `"disabled"`.

> `between_tools` is accepted at `low`, `medium`, and `high` effort.

For xhigh/max, use adaptive (omit thinking or send type adaptive).
between_tools accepts no display/budget_tokens/block_binding. Manual enabled
budget_tokens is rejected. Forced any/named tool_choice returns400; auto and
none work. Auto with strict:true or output_config.format provide schema shape.
No-tool between_tools responses contain only text. Default API effort high.

Source: https://platform.claude.com/docs/en/models/sonnet-5-5/overview
Successfully retrieved via web.click, turn2view1/turn3view0. Lines98-178:
exact direct ID claude-sonnet-5-5, text+images to text,1M context,128K max output;
USD2/10 input/output per million, cache5m write2.50,1h4,read.20. Non-default
temperature/top_p/top_k return400; omit sampling. Released September28,2026.

Source: https://platform.claude.com/docs/en/build-with-claude/structured-outputs
Successfully retrieved turn4view0. Native JSON uses output_config.format
type json_schema; SDK schema projection can remove unsupported bounds and
requires canonical local validation. Never call projected bounds native strict.

Owner successful exact native receipts provide additional live identity and
contract proof; these source notes do not replace native/parity qualification.
