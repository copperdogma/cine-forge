"""Run one already admitted authored variant with its own three-hop ledger and lock."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
import urllib.error
from decimal import Decimal
from pathlib import Path
from urllib.parse import quote

from preflight_carbon_workspace import E, FIXTURES, MODEL, ROOT, dump, google_request, sha
from run_carbon_workspace import HOP, ONE, PRIVATE, TOTAL, protected, read_interaction, settlement, verify
from whole_story_workspace_contract import consumer_smoke, decode_native_envelope, materialize_workspace


def sse_events(raw):
    for line in raw.splitlines():
        if line.startswith(b"data:") and line[5:].strip() not in (b"",b"[DONE]"):
            yield json.loads(line[5:].strip())


def reconcile_failed_stream(raw_path, row):
    events=list(sse_events(raw_path.read_bytes()))
    first=next(e["interaction"] for e in events if e["event_type"]=="interaction.created")
    assert first["model"]==MODEL
    identity=first["id"]
    with google_request("/interactions/"+quote(identity,safe=""),timeout=90) as resp:
        raw=resp.read()
    dest=raw_path.with_suffix(".get.json")
    with protected(dest) as f:f.write(raw)
    obj=json.loads(raw)
    assert obj["id"]==identity and obj["model"]==MODEL
    row["read_only_get"]={"path":str(dest.relative_to(ROOT)),"sha256":sha(dest),
                          "status":obj["status"],"errors":obj.get("errors",[])}
    if obj.get("usage") and obj["status"] in {"completed","requires_continuation","incomplete"}:
        text="".join(p["text"] for s in obj.get("steps",[]) if s["type"]=="model_output"
                     for p in s.get("content",[]) if p["type"]=="text")
        return obj,text,None
    assert obj["status"]=="failed" and any(e["code"]=="DEADLINE_EXCEEDED" for e in obj["errors"])
    usable=[i for i,e in enumerate(events) if e.get("status")=="in_progress" and e.get("continuation_token")]
    assert usable
    i=usable[-1]
    assert not any(e.get("delta",{}).get("type")=="text" for e in events[i+1:]), "text beyond checkpoint"
    checkpoint=events[i]
    assert checkpoint["interaction_id"]==identity
    text="".join(e.get("delta",{}).get("text","") for e in events[:i+1] if e.get("delta",{}).get("type")=="text")
    usage=checkpoint["usage"]
    row.update(interaction_id=identity,status="failed",interim_usage=usage,
               checkpoint_visible_chars=len(text),checkpoint_index=i)
    return None,text,(identity,checkpoint["continuation_token"],
                      usage["total_output_tokens"]+usage.get("total_thought_tokens",0))


def run(case):
    verify()
    auth=json.loads((E/"variant-admission.json").read_text())
    assert case in auth["case_logical_reservations_usd"]
    assert Decimal(auth["case_logical_reservations_usd"][case])==ONE
    assert Decimal(auth["admitted_subjects_conservative_total_usd"]) < Decimal(auth["total_subjects_pool_usd"])
    ledger=E/(case+"-ledger.json")
    # Dedicated per-case disk lock, kept to prevent implicit repeats of a paid case.
    fd=os.open(E/(case+"-started.lock"),os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
    os.close(fd)
    assert not ledger.exists()
    body0=json.loads((E/(case+"-request.json")).read_text())
    rows=[]; parts=[]; progress=0; previous=token=None
    for hop in (1,2,3):
        body=dict(body0)
        if previous:
            del body["input"]
            body.update(previous_interaction_id=previous,continuation_token=token)
        inputs=26000+(hop-1)*HOP
        outputs=min(HOP,TOTAL-progress)
        assert outputs>0
        reserve=Decimal(2*inputs+10*outputs)/1_000_000
        assert sum(Decimal(r["accounted_usd"]) for r in rows)+reserve<=ONE, "Hard per-case cap"
        encoded=json.dumps(body,ensure_ascii=False).encode()
        name=f"{case}-hop{hop}"
        wire=PRIVATE/(name+".wire")
        with protected(PRIVATE/(name+".request")) as f:f.write(encoded)
        row={"logical":case,"hop":hop,"input_bound":inputs,"output_bound":outputs,
             "reserve_usd":str(reserve),"accounted_usd":str(reserve),"state":"unknown-held",
             "request_sha256":hashlib.sha256(encoded).hexdigest(),"wire":str(wire.relative_to(ROOT)),
             "producer_sha256":sha(Path(__file__)),"previous_interaction_id":previous}
        rows.append(row);dump(ledger,rows)
        start=time.monotonic()
        try:
            with google_request("/interactions",body,timeout=1200) as resp:
                row["http_status"]=resp.status
                try:
                    obj,text=read_interaction(resp,wire)
                except (AssertionError, OSError) as exc:
                    row["stream_fault"]=type(exc).__name__
                    obj,text,checkpoint=reconcile_failed_stream(wire,row)
                    if checkpoint:
                        assert hop==1, "Repeated deadline: stop permanently"
                        previous,token,new=checkpoint
                        progress+=new
                        parts.append(text)
                        continue
            assert obj["model"]==MODEL
            cost,gen=settlement(obj["usage"],inputs,outputs)
            assert cost<=reserve
            row.update(state="settled",accounted_usd=str(cost),model=MODEL,interaction_id=obj["id"],
                       usage=obj["usage"],status=obj["status"],visible_chars=len(text))
            parts.append(text);progress+=gen
            (E/(case+"-visible.txt")).write_text("".join(parts))
            if obj["status"]=="completed":break
            assert obj["status"]=="requires_continuation" and hop<3
            previous,token=obj["id"],obj["continuation_token"]
        except urllib.error.HTTPError as exc:
            row.update(error_type="HTTPError",error_http_status=exc.code)
            with protected(PRIVATE/(name+".http-error.json")) as f:f.write(exc.read())
            raise
        finally:
            row["elapsed_ms"]=round((time.monotonic()-start)*1000)
            if wire.exists():row["wire_sha256"]=sha(wire)
            dump(ledger,rows)
    source=FIXTURES/(case+".fountain")
    envelope=json.loads("".join(parts))
    decoded=json.loads(envelope["bundle_json"])
    dump(E/"blind-v2"/(case+"-B-semantic-object.json"),decoded)
    bundle=decode_native_envelope(envelope,source_bytes=source.read_bytes(),
                                  source_filename=source.name).model_dump(mode="json")
    dump(E/(case+"-bundle.json"),bundle)
    project=ROOT/"output"/("carbon-20261110-"+case)
    materialize_workspace(bundle,source_bytes=source.read_bytes(),project_dir=project,
                          run_context={"producer":MODEL,"logical":case})
    smoke=consumer_smoke(repo_root=ROOT,project_dir=project,payload=bundle,source_bytes=source.read_bytes())
    dump(E/(case+"-consumer.json"),smoke)
    print(case,smoke)


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("case",choices=["last_ferry","matinee_echo"])
    run(parser.parse_args().case)
