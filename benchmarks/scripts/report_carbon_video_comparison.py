"""Offline numerical replay and source-adjudicated results for Scout109."""

import json
from decimal import Decimal

import run_carbon_video_comparison as campaign

E = campaign.E
R = campaign.RESULT
M = E.parent.parent / "story-236-carbon-20261110-manifest.json"


def build():
    source = campaign.read(E / "source-review.json")
    by_arm = {}
    rows = []
    for arm in campaign.ARMS:
        data = []
        for t in campaign.configured()[3]:
            case = t["vars"]["evaluation_id"]
            name = case + "-" + arm
            run_name = name
            if arm == "carbon" and not (E / f"{name}-subject.json").exists():
                run_name = name + "64"
            if not (E / f"{run_name}-subject.json").exists():
                missing = campaign.read(E / f"{run_name}-incomplete.json")
                rows.append(
                    dict(
                        case=case,
                        clip=t["vars"]["clip_id"],
                        arm=arm,
                        configuration="high65536",
                        state=missing["state"],
                        capability="unmeasured; no complete visible JSON output",
                        seconds=missing["elapsed_s"],
                        cost=float(missing["cost"]),
                    )
                )
                continue
            subject = campaign.read(E / f"{run_name}-subject.json")
            judge = campaign.read(E / f"{name}-opus.json")
            output = subject["response"]
            raw_path = E / f"{run_name}-raw.json"
            if not raw_path.exists():
                raw_path = E / "sanitized-native" / raw_path.name
            raw = campaign.read(raw_path)
            assert len(json.loads(output["output"])) == 13
            assert output["metadata"]["returned_model"] == campaign.MODELS[arm]
            assert output["metadata"]["frame_count"] == 5
            assert output["cached"] is False
            structural = campaign.get_assert(output["output"], {"vars": t["vars"]})
            assert structural == subject["structural"]
            dual = (structural["score"] + judge["score"]) / 2
            review = source[case][arm]
            quality = bool(structural["pass"] and judge["score"] >= 0.8 and dual >= 0.8)
            item = dict(
                case=case,
                clip=t["vars"]["clip_id"],
                arm=arm,
                model=campaign.MODELS[arm],
                configuration=subject.get(
                    "configuration",
                    {"carbon": "high32768", "sol": "low4096", "luna": "low1400"}[arm],
                ),
                structural=structural["score"],
                rubric=judge["score"],
                combined=dual,
                scoring_pass=quality,
                full_pass=quality and not review["critical_errors"],
                source_review=review,
                seconds=output["latencyMs"] / 1000,
                cost=output["cost"],
                timely=output["latencyMs"] <= 15000,
                affordable=output["cost"] <= 0.02,
                tokens=output["tokenUsage"],
                native_usage=raw.get("usageMetadata", raw.get("usage")),
            )
            data.append(item)
            rows.append(item)
        means = {
            k: sum(r[k] for r in data) / len(data)
            for k in ("structural", "rubric", "combined", "seconds", "cost")
        }
        by_arm[arm] = dict(
            means=means,
            valid_outputs=len(data),
            total_cases=6,
            full_pass=sum(r["full_pass"] for r in data),
            scoring_pass=sum(r["scoring_pass"] for r in data),
            timely=sum(r["timely"] for r in data),
            affordable=sum(r["affordable"] for r in data),
        )
    ledger = campaign.ledger() + campaign.read(E / "ledger64.json")
    assert all(r["state"] == "settled" for r in ledger)
    assert len({r["name"] for r in ledger}) == len(ledger)
    assert sum(r["name"].endswith("opus") for r in ledger) == sum(
        a["valid_outputs"] for a in by_arm.values()
    )

    def settled(row):
        # Rates have four decimal places or fewer per million tokens. Restore
        # exact decimal precision lost by the maintained float cost adapter.
        return Decimal(row["usd"]).quantize(Decimal("0.0000000001"))

    total = sum(settled(r) for r in ledger)
    assert total <= 11
    totals = {
        arm: str(sum(settled(r) for r in ledger if r["name"].endswith((arm, arm + "64"))))
        for arm in (*campaign.ARMS, "opus")
    }
    return dict(
        base=campaign.read(campaign.FREEZE)["base"],
        measured="2026-11-10",
        aggregate=by_arm,
        rows=rows,
        exact_estimated_usd=str(total),
        estimated_by_arm=totals,
        unknown_reserved_usd="0",
        calls=len(ledger),
        original_incomplete={
            p.name: campaign.read(p) for p in E.glob("*-incomplete.json") if p.is_file()
        },
        carbon_total_subject_mean_including_failed_attempts_usd=float(
            Decimal(totals["carbon"]) / 6
        ),
        cap_usd=11,
        december_carbon_mean_usd=2 * by_arm["carbon"]["means"]["cost"],
    )


def main():
    result = build()
    if R.exists():
        assert result == campaign.read(R)
    else:
        campaign.dump(R, result)
    private = campaign.read(E / "native-custody.json")
    local_paths = {campaign.ROOT / row["exact_local"] for row in private}
    for row in private:
        original = campaign.ROOT / row["exact_local"]
        if original.exists():
            assert campaign.inventory(original)["sha256"] == row["sha256"]
    paths = [
        p
        for p in E.rglob("*")
        if p.is_file() and p not in local_paths and p.name != ".ledger64.lock"
    ] + [
        R,
        *[
            campaign.ROOT / "benchmarks/scripts" / script
            for script in (
                "report_carbon_video_comparison.py",
                "run_carbon_video_comparison.py",
                "continue_carbon_frame_panel.py",
                "run_carbon_frame_output_repair.py",
            )
        ],
    ]
    files = [campaign.inventory(p) for p in sorted(paths)]
    if M.exists():
        assert files == campaign.read(M)["files"]
    else:
        campaign.dump(
            M,
            dict(
                files=files,
                replay="PYTHONPATH=src <owner-python> "
                "benchmarks/scripts/report_carbon_video_comparison.py",
            ),
        )
    print(json.dumps(result["aggregate"], indent=2))
    print(result["exact_estimated_usd"], result["estimated_by_arm"])


if __name__ == "__main__":
    main()
