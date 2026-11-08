// GenomeVault two-pane UI (Agent C, M10). Plain JS, no external assets, so demo mode works offline (I8).
// Wording rule (I7): the UI never tells the user a drug is fine to take; it prepares them for a pharmacist.
"use strict";

const $ = (id) => document.getElementById(id);

function el(tag, attrs = {}, ...children) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v === null || v === undefined || v === false) continue;
    if (k === "class") node.className = v;
    else if (k === "dataset") Object.assign(node.dataset, v);
    else node.setAttribute(k, v === true ? "" : v);
  }
  for (const c of children.flat()) {
    if (c === null || c === undefined || c === false) continue;
    node.append(c instanceof Node ? c : document.createTextNode(String(c)));
  }
  return node;
}

async function api(path, body) {
  const opts = body === undefined ? {} : {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
  };
  const res = await fetch(path, opts);
  if (!res.ok) throw new Error(`${path} → ${res.status}`);
  return res.json();
}

// ---------- formatting ----------

const humanize = (s) => s.replace(/_/g, " ");
const cap = (s) => s.charAt(0).toUpperCase() + s.slice(1);

const CONDITIONS = {
  CAD_post_stent: "Coronary artery disease (post-stent)",
  hypertension: "High blood pressure",
  hyperlipidemia: "High cholesterol",
  GERD: "GERD (acid reflux)",
};

const ENGINES = {
  gene_drug: "Gene–drug", drug_drug: "Drug–drug", drug_lab: "Drug–lab",
  allergy: "Allergy", class_rule: "Drug class rule",
};

const STATES = {
  known: "Known",
  none_listed: "No interaction listed",
  no_data: "No data: ask your pharmacist",
};

const LEDGER_KINDS = {
  local_only: "Answered on device",
  kb_hit: "Knowledge base hit",
  bucket: "Decoy group of 8 sent",
  cover: "Cover traffic",
  blocked: "Blocked by leakage check",
};

function formatBytes(n) {
  if (n < 1024) return `${n} B`;
  return `${(n / 1024).toFixed(n < 10240 ? 1 : 0)} KB`;
}

function formatDate(iso) {
  const d = new Date(iso + (iso.length === 10 ? "T00:00:00" : ""));
  return d.toLocaleDateString(undefined, { month: "short", year: "numeric" });
}

// Turn an exact key into a readable title.
// "CYP2C19:poor_metabolizer|clopidogrel" → "Clopidogrel × CYP2C19 poor metabolizer"
// "SLCO1B1:decreased_function|simvastatin|dose>20mg" → "Simvastatin × SLCO1B1 decreased function (dose > 20mg)"
function flagTitle(key) {
  const drugs = [], context = [], conditions = [];
  for (const part of key.split("|")) {
    if (part.includes(":")) {
      const [gene, pheno] = part.split(":");
      context.push(`${gene} ${humanize(pheno)}`);
    } else if (/[<>]/.test(part)) {
      const cond = part.replace(/\s*([<>]=?)\s*/, " $1 ");
      (part.startsWith("dose") ? conditions : context).push(cond);
    } else {
      drugs.push(cap(part));
    }
  }
  const title = [...drugs, ...context].join(" × ");
  return conditions.length ? `${title} (${conditions.join(", ")})` : title;
}

// ---------- profile ----------

function renderProfile(p) {
  const root = $("profile");
  root.replaceChildren();

  const genes = el("ul", { class: "kv" }, Object.entries(p.genotypes).map(([gene, gt]) => {
    const pheno = p.phenotypes[gene] || "";
    const notable = pheno && !/^(normal|reference)/.test(pheno);
    return el("li", {}, el("span", { class: "k" }, gene, " ", el("span", { class: "muted" }, gt)),
      el("span", { class: notable ? "v notable" : "v" }, humanize(pheno)));
  }));

  const meds = el("ul", { class: "kv" }, p.meds.map((m) =>
    el("li", {}, el("span", { class: "k" }, cap(m.ingredient)),
      el("span", { class: "v" }, m.dose_mg != null ? `${m.dose_mg} mg` : ""))));

  // Labs: latest value per test, with the previous value when there is one.
  const byTest = new Map();
  for (const lab of p.labs) {
    if (!byTest.has(lab.test)) byTest.set(lab.test, []);
    byTest.get(lab.test).push(lab);
  }
  const labs = el("ul", { class: "kv" }, [...byTest.entries()].map(([test, rows]) => {
    rows.sort((a, b) => b.date.localeCompare(a.date));
    const [latest, prev] = rows;
    return el("li", {},
      el("span", { class: "k" }, test, latest.stale ? el("span", { class: "stale" }, "stale") : null),
      el("span", { class: "v" },
        prev ? el("span", { class: "trend" }, `${prev.value} → `) : null,
        `${latest.value} ${latest.unit}`,
        el("span", { class: "muted small" }, ` · ${formatDate(latest.date)}`)));
  }));

  const conditions = el("div", { class: "tags" },
    p.conditions.map((c) => el("span", { class: "tag" }, CONDITIONS[c] || humanize(c))));
  const allergies = el("div", { class: "tags" },
    p.allergies.length ? p.allergies.map((a) => el("span", { class: "tag allergy" }, cap(a)))
      : el("span", { class: "muted" }, "None recorded"));

  root.append(
    el("section", {}, el("h3", {}, "Genes"), genes),
    el("section", {}, el("h3", {}, "Medications"), meds),
    el("section", {}, el("h3", {}, "Labs"), labs),
    el("section", {}, el("h3", {}, "Conditions"), conditions, el("h3", { style: "margin-top:12px" }, "Allergies"), allergies),
  );
}

// ---------- flags ----------

function flagItem(f) {
  return el("li", { class: `flag ${f.severity}` },
    el("div", { class: "flag-top" },
      el("span", { class: "flag-id" }, f.id),
      el("span", { class: "flag-title" }, flagTitle(f.key)),
      el("span", { class: "sev" }, f.severity)),
    el("div", { class: "flag-meta" },
      el("span", {}, ENGINES[f.engine] || f.engine),
      el("code", {}, f.key),
      f.needs_cloud ? el("span", {}, "More context available via a private question") : null),
    f.evidence.length ? el("ul", { class: "evidence" }, f.evidence.map((e) => el("li", {}, e))) : null);
}

function renderFlags(data) {
  const n = data.flags.length;
  $("flags-summary").textContent = n
    ? `${n} thing${n === 1 ? "" : "s"} to raise with your pharmacist or doctor, from ${data.checked.length} medications.`
    : "No flags from the local tables. A missing entry is not the same as no interaction; ask your pharmacist.";
  $("flags").replaceChildren(...data.flags.map(flagItem));
}

async function onCheck(ev) {
  ev.preventDefault();
  const input = $("check-input"), button = ev.submitter || ev.target.querySelector("button");
  const text = input.value.trim();
  if (!text) return;
  button.disabled = true;
  const out = $("check-result");
  try {
    const data = await api("/api/check", { text });
    if (!data.drugs.length) {
      out.replaceChildren(el("div", { class: "note" }, `Couldn't recognize "${text}" as a medication. Try the generic name.`));
    } else if (!data.flags.length) {
      const names = data.drugs.map((d) => d.ingredient).join(", ");
      out.replaceChildren(el("div", { class: "note" },
        el("strong", {}, `No local data for ${names}. `),
        "A missing entry does not mean there is no interaction. Ask your pharmacist before taking it."));
    } else {
      out.replaceChildren(el("ol", { class: "flags check-result" }, data.flags.map(flagItem)));
    }
    input.value = "";
  } catch (err) {
    out.replaceChildren(el("div", { class: "note" }, `Check failed: ${err.message}`));
  } finally {
    button.disabled = false;
    pollLedger();
  }
}

// ---------- chat ----------

function answerBubble(a) {
  const meta = el("div", { class: "msg-meta" },
    el("span", { class: `badge state-${a.state}` }, STATES[a.state] || a.state),
    a.sent_to_cloud
      ? el("span", { class: "badge route-cloud" }, "Asked privately · decoy group of 8")
      : el("span", { class: "badge route-local" }, "Answered on device"));
  const facts = a.facts.length ? el("ul", { class: "facts" }, a.facts.map((f) =>
    el("li", {}, el("span", { class: `tier ${f.tier}` }, f.label), " · ", f.text))) : null;
  return el("div", { class: "msg agent" }, el("div", {}, a.text), facts, meta);
}

async function ask(question) {
  const chat = $("chat");
  chat.querySelector(".suggestion")?.remove();
  chat.append(el("div", { class: "msg user" }, question));
  const pending = el("div", { class: "msg agent pending" }, "Checking locally first…");
  chat.append(pending);
  const button = $("ask-form").querySelector("button");
  button.disabled = true;
  try {
    pending.replaceWith(answerBubble(await api("/api/ask", { question })));
  } catch (err) {
    pending.textContent = `Couldn't answer: ${err.message}`;
    pending.classList.remove("pending");
  } finally {
    button.disabled = false;
    pollLedger();
  }
}

function onAsk(ev) {
  ev.preventDefault();
  const input = $("ask-input");
  const q = input.value.trim();
  if (!q) return;
  input.value = "";
  ask(q);
}

// ---------- ledger ----------

let lastSeq = 0;
let polling = false;

function ledgerEntry(e) {
  const time = new Date(e.ts).toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit", second: "2-digit" });
  const sub = [`#${e.seq}`, time, e.bucket_id, `personal fields ${e.personal_fields_sent}`].filter(Boolean).join(" · ");
  return el("li", { class: "entry" },
    el("span", { class: `kind kind-${e.kind}` }, humanize(e.kind)),
    el("span", { class: "desc" }, LEDGER_KINDS[e.kind] || e.kind),
    el("span", { class: "bytes" }, formatBytes(e.bytes_out)),
    el("span", { class: "sub" }, sub));
}

async function pollLedger() {
  if (polling) return;
  polling = true;
  try {
    const data = await api(`/api/ledger?since=${lastSeq}`);
    const list = $("ledger");
    if (data.entries.length) {
      list.querySelector(".ledger-empty")?.remove();
      for (const e of data.entries) {
        list.prepend(ledgerEntry(e));
        lastSeq = Math.max(lastSeq, e.seq);
      }
    }
    const t = data.totals;
    $("ledger-count").textContent = t.count;
    $("ledger-bytes").textContent = formatBytes(t.bytes_out);
    $("total-bytes").textContent = formatBytes(t.bytes_out);
    for (const id of ["ledger-personal", "total-personal"]) $(id).textContent = t.personal_fields_sent;
    $("ledger-personal").className = t.personal_fields_sent ? "bad" : "ok";
  } catch {
    // server restarting; try again next tick
  } finally {
    polling = false;
  }
}

// ---------- boot ----------

async function boot() {
  $("check-form").addEventListener("submit", onCheck);
  $("ask-form").addEventListener("submit", onAsk);
  $("chat").addEventListener("click", (ev) => {
    const q = ev.target.closest(".suggestion")?.dataset.q;
    if (q) ask(q);
  });

  try {
    const status = await api("/api/status");
    $("demo-badge").hidden = !status.demo;
    const mocks = Object.entries(status.modules).filter(([, m]) => m === "mock").map(([n]) => n);
    $("modules").textContent = mocks.length ? `Running on mocks: ${mocks.join(", ")}` : "All modules live";
  } catch { /* non-critical */ }

  try {
    renderProfile(await api("/api/profile"));
  } catch (err) {
    $("profile").replaceChildren(el("p", { class: "muted" }, `Couldn't load profile: ${err.message}`));
  }
  try {
    renderFlags(await api("/api/flags"));
  } catch (err) {
    $("flags-summary").textContent = `Couldn't run the medication check: ${err.message}`;
  }

  pollLedger();
  setInterval(pollLedger, 1500);
}

boot();
