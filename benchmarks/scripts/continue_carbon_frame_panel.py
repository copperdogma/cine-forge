"""Finish complementary cases after a terminal Google output-allowance miss."""

import time
from decimal import Decimal
from pathlib import Path

import run_carbon_video_comparison as panel


def account_incomplete(test, elapsed):
    case = test["vars"]["evaluation_id"]
    name = case + "-carbon"
    raw = panel.read(panel.E / (name + "-raw.json"))
    assert raw.get("modelVersion") == "gemini-4-carbon" and raw.get("responseId")
    candidates = raw["candidates"]
    assert len(candidates) == 1 and candidates[0]["finishReason"] == "MAX_TOKENS"
    parts = candidates[0].get("content", {}).get("parts", [])
    text = "".join(part.get("text", "") for part in parts if not part.get("thought"))
    usage = raw["usageMetadata"]
    inp, visible, thoughts = [
        usage[k] for k in ("promptTokenCount", "candidatesTokenCount", "thoughtsTokenCount")
    ]
    assert inp + visible + thoughts == usage["totalTokenCount"] and visible + thoughts <= 32768
    cached = usage.get("cachedContentTokenCount", 0)
    assert 0 <= cached <= inp
    cost = (2 * (inp - cached) + Decimal(".1") * cached + 10 * (visible + thoughts)) / 1000000
    panel.record(name, cost, "settled")
    panel.dump(
        panel.E / (name + "-incomplete.json"),
        dict(
            state="terminal-output-allowance",
            model=raw["modelVersion"],
            response_id=raw["responseId"],
            usage=usage,
            cost=str(cost),
            elapsed_s=elapsed,
            finish_reason="MAX_TOKENS",
            text_bytes=len(text.encode()),
            inference_repeat=False,
            semantics="unmeasured; complete original schema absent; no judge on truncated answer",
        ),
    )
    print(name, "MAX_TOKENS", elapsed, cost, flush=True)


def main():
    panel.verify_freeze()
    assert not panel.RESULT.exists()
    freeze = panel.read(panel.E / "continuation-producer.json")
    assert panel.inventory(Path(__file__)) == freeze["producer"]
    for test in panel.configured()[3][1:]:
        case = test["vars"]["evaluation_id"]
        for arm in panel.ARMS:
            name = case + "-" + arm
            if (panel.E / (name + "-incomplete.json")).exists():
                continue
            if (
                arm == "carbon"
                and (panel.E / (name + "-raw.json")).exists()
                and not (panel.E / (name + "-subject.json")).exists()
            ):
                # Previous process preserved provider's terminal raw bytes before its
                # fail-closed native adapter raised. No new HTTP request is needed.
                account_incomplete(test, freeze["case002_elapsed_s"])
                continue
            start = time.monotonic()
            try:
                row = panel.subject(arm, test)
            except RuntimeError as error:
                if arm != "carbon" or str(error) != "Gemini 4 did not reach terminal STOP":
                    raise
                account_incomplete(test, time.monotonic() - start)
                continue
            panel.judge(row)


if __name__ == "__main__":
    main()
