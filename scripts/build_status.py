"""Build coord/STATUS.md from coord/agents/*/STATUS.md (integrator runs `make status`)."""
import pathlib, datetime
rows = []
for f in sorted(pathlib.Path("coord/agents").glob("*/STATUS.md")):
    d = {}
    for line in f.read_text().splitlines():
        if ":" in line and not line.startswith(" "):
            k, v = line.split(":", 1)
            d[k.strip()] = v.split("#")[0].strip()
    rows.append(f"| {d.get('agent','?')} | {d.get('state','?')} | {d.get('current_task','')} | "
                f"{d.get('blocked_on','')} | {d.get('last_commit','')} | {d.get('next','')} |")
out = ["# STATUS board", "",
       f"Generated {datetime.datetime.now():%Y-%m-%d %H:%M} by `make status`. Do not edit by hand.", "",
       "| Agent | State | Current task | Blocked on | Last commit | Next |",
       "| --- | --- | --- | --- | --- | --- |", *rows]
pathlib.Path("coord/STATUS.md").write_text("\n".join(out) + "\n")
print("\n".join(out))
