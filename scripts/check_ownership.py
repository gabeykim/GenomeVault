"""Fail if any commit touches files its agent tag does not own (AGENTS.md §1, §3)."""
import argparse, fnmatch, re, subprocess, sys

OWN = {
    "A": ["data/*", "core/ingest.py", "core/graph.py", "core/capture.py",
          "core/normalize.py", "core/rules.py", "tests/A/*"],
    "B": ["core/router.py", "core/generalize.py", "core/decoys.py", "core/kb.py",
          "core/cloud.py", "core/ledger.py", "core/validator.py", "data/buckets/*", "tests/B/*"],
    "C": ["app.py", "ui/*", "phone/*", "core/merge.py", "core/actions.py", "tests/C/*"],
    "D": ["eval/*", "docs/*", "slides/*", "tests/D/*"],
    "I": ["*"],  # integrator / humans
}
NOT_A = ["data/buckets/*"]
NEW_ONLY = ["coord/inbox/*", "coord/proposals/*"]
TAG = re.compile(r"^\[([ABCDI])\]")

def git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True, check=True).stdout

def allowed(tag, path, status):
    if tag == "I":
        return True
    if fnmatch.fnmatch(path, f"coord/agents/{tag}/STATUS.md") or fnmatch.fnmatch(path, f"coord/agents/{tag}/LOG.md"):
        return True
    if any(fnmatch.fnmatch(path, p) for p in NEW_ONLY):
        return status == "A"
    if tag == "A" and any(fnmatch.fnmatch(path, p) for p in NOT_A):
        return False
    return any(fnmatch.fnmatch(path, p) for p in OWN[tag])

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--range", required=True)
    rng = ap.parse_args().range
    if rng.startswith("0000000"):
        rng = "HEAD~1..HEAD"
    errors = []
    for sha in git("rev-list", "--no-merges", rng).split():
        subject = git("log", "-1", "--format=%s", sha).strip()
        body = git("log", "-1", "--format=%b", sha)
        m = TAG.match(subject)
        if not m:
            errors.append(f"{sha[:7]}: subject must start with [A]/[B]/[C]/[D]/[I]: {subject!r}")
            continue
        tag = m.group(1)
        changes = [l.split("\t") for l in git("diff-tree", "--no-commit-id", "--name-status", "-r", sha).splitlines()]
        code = False
        for status, *paths in changes:
            path = paths[-1]
            if not path.startswith("coord/"):
                code = True
            if not allowed(tag, path, status[0]):
                errors.append(f"{sha[:7]} [{tag}] may not change {path} (status {status})")
        if code and tag != "I" and "Class:" not in body:
            errors.append(f"{sha[:7]} [{tag}] code commit missing 'Class:' trailer (AGENTS.md §6)")
    if errors:
        print("\n".join(errors)); sys.exit(1)
    print("ownership ok")

if __name__ == "__main__":
    main()
