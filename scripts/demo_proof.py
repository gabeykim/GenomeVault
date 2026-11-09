"""Proof that the demo works with the adaptive features ON, and stays private (PLAN P8, D-040).

Run from the repo root on the demo machine, venv active:

    GV_FUZZY=1 GV_TAIL=1 GV_DEMO_LIVE_FALLBACK=1 GV_INTENT=1 GV_DIRECT=1 \
    DEMO=1 GV_DELAY_S=0,0 GV_COVER_INTERVAL_S=3600 python scripts/demo_proof.py

Part 1 re-runs the scripted beats (S2-S7). Part 2 proves each adaptive feature and the privacy checks
that go with it. The live long-tail check needs ANTHROPIC_API_KEY and a network; without them it is
reported as SKIP (never as a pass). Exit code 0 only if nothing FAILs.
"""
import json
import os
import pathlib
import sys
import time
from datetime import date

os.environ.setdefault("DEMO", "1")
sys.path.insert(0, os.getcwd())
from fastapi.testclient import TestClient  # noqa: E402

import app as appmod  # noqa: E402
from core import kb, validator  # noqa: E402

ROOT = pathlib.Path.cwd()
FLAGS = ["GV_FUZZY", "GV_TAIL", "GV_DEMO_LIVE_FALLBACK", "GV_INTENT", "GV_DIRECT"]
rows: list[tuple[str, str, str]] = []   # (name, PASS|FAIL|SKIP, detail)
answers: list[str] = []                 # every answer text shown, for the I7 sweep


def check(name: str, ok: bool, detail: str) -> None:
    rows.append((name, "PASS" if ok else "FAIL", detail))


def skip(name: str, detail: str) -> None:
    rows.append((name, "SKIP", detail))


def ledger(c):
    return c.get("/api/ledger").json()


def ask(c, q: str, **kw) -> dict:
    a = c.post("/api/ask", json={"question": q, **kw}).json()
    if a.get("text"):
        answers.append(a["text"])
    return a


def first_para(a: dict) -> str:
    return (a.get("text") or "").split("\n\n")[0]


def keys_of(a: dict) -> list[str]:
    return sorted(f["key"] for f in a.get("facts", []))


def new_entries(c, since: int) -> list[dict]:
    return [e for e in ledger(c)["entries"] if e["seq"] > since]


with TestClient(appmod.app) as c:
    # ------------------------------------------------------------ part 1: scripted beats
    st = c.get("/api/status").json()
    check("Disclaimer visible", "not medical advice" in (st.get("disclaimer") or "").lower(),
          f"{st.get('disclaimer')!r}")
    img = (ROOT / "phone/samples/clopidogrel.png").read_bytes()
    r = c.post("/api/capture", content=img, headers={"content-type": "image/png"}).json()
    got = [d["ingredient"] for d in r.get("drugs", [])]
    check("S2 label photo", got == ["clopidogrel"], f"clopidogrel.png -> {got} (GV_OCR={os.environ.get('GV_OCR', 'auto')})")
    r = c.post("/api/check", json={"text": "Plavix 75 mg"}).json()
    check("S2 typed brand", [d["ingredient"] for d in r.get("drugs", [])] == ["clopidogrel"], "'Plavix 75 mg' -> clopidogrel")
    t0 = ledger(c)["totals"]
    ids = sorted({x["id"] for x in c.get("/api/flags").json()["flags"]})
    t1 = ledger(c)["totals"]
    check("S3 flags X1-X4, 0 bytes", {"X1", "X2", "X3", "X4"} <= set(ids) and t1["bytes_out"] == t0["bytes_out"],
          f"flags {ids}, bytes_out {t0['bytes_out']}->{t1['bytes_out']}")

    q18 = "What should I bring up with my cardiologist?"
    n0 = ledger(c)["totals"]["count"]
    a18 = ask(c, q18)
    buckets = [e for e in new_entries(c, n0) if e["kind"] == "bucket"]
    texts = c.get(f"/api/ledger/{buckets[0]['seq']}/outbound").json()["texts"] if buckets else []
    check("S4 group of 8 sent", bool(buckets) and len(texts) == 8, f"state={a18['state']}, buckets={len(buckets)}, texts={len(texts)}")
    n1 = ledger(c)["totals"]
    ask(c, q18)
    kinds = [e["kind"] for e in new_entries(c, n1["count"])]
    check("S6 repeat answered on device", "bucket" not in kinds and ledger(c)["totals"]["bytes_out"] == n1["bytes_out"],
          f"new entries {kinds}")
    pa = ask(c, "Is pantoprazole okay with my clopidogrel?")
    k = [f["key"] for f in pa.get("facts", [])]
    check("S6 pantoprazole uses its own key", pa["state"] == "no_data" or (k and k[0] == "clopidogrel|pantoprazole"),
          f"state={pa['state']}, first key={k[:1]}")
    c.post("/api/offline", json={"offline": True})
    o0 = ledger(c)["totals"]
    x5 = "X5" in {x["id"] for x in c.post("/api/check", json={"text": "ibuprofen"}).json()["flags"]}
    ask(c, "Can I take ibuprofen?")
    o1 = ledger(c)["totals"]
    check("S6 offline ibuprofen X5, 0 bytes", x5 and o1["bytes_out"] == o0["bytes_out"], f"X5={x5}")
    c.post("/api/offline", json={"offline": False})
    ph = c.get("/api/actions/pharmacist").json().get("text", "")
    rm = c.get("/api/actions/reminders").json().get("reminders", [])
    check("S6 actions", len(ph) > 50 and len(rm) >= 1, f"pharmacist {len(ph)} chars, reminders {len(rm)}")

    # ------------------------------------------------------------ part 2: adaptive features
    on = {f: os.environ.get(f, "") not in ("", "0") for f in FLAGS}
    check("Adaptive flags ON", all(on.values()), json.dumps(on))

    # Typos (A part 1 + C part 4)
    r = c.post("/api/check", json={"text": "simvastatn 40 mg"}).json()
    check("Typo assumed: simvastatn", [d["ingredient"] for d in r.get("drugs", [])] == ["simvastatin"] and bool(r.get("assumed")),
          f"drugs={[d['ingredient'] for d in r.get('drugs', [])]}, assumed={r.get('assumed')}")
    r = c.post("/api/check", json={"text": "clopidogral"}).json()
    ch = (r.get("choices") or [{}])[0].get("choices", [])
    check("Look-alike asks first: clopidogral", r.get("held") and not r.get("drugs") and "clopidogrel" in ch,
          f"held={r.get('held')}, choices={ch}, nothing checked yet")
    r = c.post("/api/check", json={"text": "lisinoprl-hydrochlorothiazide"}).json()
    dr = {d["ingredient"] for d in r.get("drugs", [])}
    fl = {x["id"] for x in r.get("flags", [])}
    check("Typo in a combo pill keeps every part", {"lisinopril", "hydrochlorothiazide"} <= dr,
          f"drugs={sorted(dr)}, flags={sorted(fl)}")
    held = ask(c, "is clopidogral ok with my aspirin")
    check("Typo question waits for a pick", held["state"] == "held" and not held["sent_to_cloud"],
          f"state={held['state']}, sent={held['sent_to_cloud']}")

    # Paraphrases get the canonical answer (I intent)
    for canon, variants in [
        (q18, ["what should i ask my heart doctor about", "wat shoud i ask my cardiolgist", "what do i tell my cardiologist"]),
        ("Could pantoprazole work instead of omeprazole with my clopidogrel?",
         ["could i swap my omeprazole for pantoprazole", "is it ok to trade omeprazole for pantoprazole"]),
        ("Can I take ibuprofen for a headache?", ["advil ok for a headache?", "can i take ibuprofin for a headache"]),
    ]:
        ca = ask(c, canon)
        for v in variants:
            va = ask(c, v)
            check(f"Paraphrase: {v!r}", va["state"] == ca["state"] and keys_of(va) == keys_of(ca),
                  f"state {va['state']} vs {ca['state']}; understood_as={va.get('understood_as')!r}")

    # Answer-first lead line (I direct)
    for q, must in [(q18, "cardiologist"), ("does ibuprofen help a headache", "ibuprofen"),
                    ("Which of my new prescriptions should I ask my pharmacist about first?", "start with")]:
        a = ask(c, q)
        lead = first_para(a)
        check(f"Direct first line: {q[:40]!r}", must in lead.lower() and "checked on your device" not in lead.lower(),
              lead[:110])

    # Long-tail pair: whole fixed group of 8, then answered on device (B parts 2-3)
    from core import decoys, router
    vocab = set(router._vocab()) | set(router._tail_vocab())
    today = date.today()
    tail_pairs = [k for k in decoys.tail_universe()
                  if k.count("|") == 1 and all(p in vocab for p in k.split("|")) and kb.get(k, today) is None]
    live = bool(os.environ.get("ANTHROPIC_API_KEY")) and on["GV_DEMO_LIVE_FALLBACK"]
    if not tail_pairs:
        check("Long-tail pair found", False, "no unanswered drug-drug key in the tail partition")
    else:
        familiar = ("warfarin", "amoxicillin", "fluconazole", "metformin", "sertraline", "prednisone")
        key = sorted(tail_pairs, key=lambda k: (not any(d in k for d in familiar), k))[0]
        x, y = key.split("|")
        q = f"Does {x} interact with {y}?"
        n2 = ledger(c)["totals"]
        a = ask(c, q)
        new = new_entries(c, n2["count"])
        tb = [e for e in new if e["kind"] == "bucket" and str(e.get("bucket_id", "")).startswith("tail-")]
        tt = c.get(f"/api/ledger/{tb[0]['seq']}/outbound").json()["texts"] if tb else []
        pf = ledger(c)["totals"]["personal_fields_sent"]
        check(f"Long-tail sent as a group of 8 ({key})", bool(tb) and len(tt) == 8 and pf == 0,
              f"bucket={tb[0]['bucket_id'] if tb else None}, texts={len(tt)}, personal_fields_sent={pf}")
        if live:
            check("Long-tail live answer", a["state"] in ("known", "none_listed") and bool(a.get("facts")),
                  f"state={a['state']}: {first_para(a)[:100]}")
            n3 = ledger(c)["totals"]
            ask(c, q)
            k3 = [e["kind"] for e in new_entries(c, n3["count"])]
            check("Long-tail repeat answered on device", "bucket" not in k3 and ledger(c)["totals"]["bytes_out"] == n3["bytes_out"],
                  f"new entries {k3}")
        else:
            skip("Long-tail live answer", f"needs ANTHROPIC_API_KEY + GV_DEMO_LIVE_FALLBACK=1 (got state={a['state']}, honest no_data)")
        # offline: a different tail pair sends nothing
        if len(tail_pairs) > 1:
            x2, y2 = sorted(tail_pairs)[-1].split("|")
            c.post("/api/offline", json={"offline": True})
            o2 = ledger(c)["totals"]
            ao = ask(c, f"Does {x2} interact with {y2}?")
            o3 = ledger(c)["totals"]
            check("Long-tail offline sends nothing", o3["bytes_out"] == o2["bytes_out"], f"state={ao['state']}")
            c.post("/api/offline", json={"offline": False})

    # Privacy sweep
    tot = ledger(c)["totals"]
    check("Personal fields sent, whole run", tot["personal_fields_sent"] == 0, f"{tot['personal_fields_sent']} (bytes_out {tot['bytes_out']})")
    bad = [(t[:60], validator.wording_problems(t)) for t in answers if validator.wording_problems(t)]
    check("No 'safe' / start-stop wording (I7)", not bad, f"{len(answers)} answers checked; problems: {bad[:2]}")

w = max(len(n) for n, _, _ in rows)
print(f"{'Check':<{w}}  Result  Detail")
for n, res, d in rows:
    print(f"{n:<{w}}  {res:<6}  {d}")
fails = sum(r == "FAIL" for _, r, _ in rows)
skips = sum(r == "SKIP" for _, r, _ in rows)
print(f"\n{sum(r == 'PASS' for _, r, _ in rows)} passed, {fails} failed, {skips} skipped")
sys.exit(1 if fails else 0)
