// GenomeVault two-pane UI (Agent C, M10). Plain JS, no external assets, so demo mode works offline (I8).
// Wording rule (I7): the UI never tells the user a drug is fine to take; it prepares them for a pharmacist.
"use strict";

const $ = (id) => document.getElementById(id);
const REDUCED = matchMedia("(prefers-reduced-motion: reduce)").matches;

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

// Small deterministic PRNG + hash so the patterns look designed, not random each load.
function hash(str) {
  let h = 2166136261;
  for (let i = 0; i < str.length; i++) { h ^= str.charCodeAt(i); h = Math.imul(h, 16777619); }
  return h >>> 0;
}
function rng(seed) {
  let s = seed >>> 0;
  return () => { s = (Math.imul(s, 1664525) + 1013904223) >>> 0; return s / 4294967296; };
}

// ---------- formatting ----------

const humanize = (s) => s.replace(/_/g, " ");
const cap = (s) => s.charAt(0).toUpperCase() + s.slice(1);
const pad2 = (n) => String(n).padStart(2, "0");

const CONDITIONS = {
  CAD_post_stent: "Coronary artery disease, post-stent",
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
  no_data: "No data, ask your pharmacist",
};
const LEDGER_KINDS = {
  local_only: "Answered on device",
  kb_hit: "Knowledge base hit",
  bucket: "Decoy group of 8 sent",
  cover: "Cover traffic",
  blocked: "Blocked by leakage check",
};
const SEV_LEVEL = { high: 3, medium: 2, low: 1 };
const LAB_NAMES = { egfr: "eGFR", alt: "ALT", ast: "AST", ck: "CK", ldl: "LDL", inr: "INR" };
const NOT_ASSESSED = /^(not_assessed|indeterminate|unknown|no_call)$/i;

function formatBytes(n) {
  if (n < 1024) return `${n} B`;
  return `${(n / 1024).toFixed(n < 10240 ? 1 : 0)} KB`;
}
function formatDate(iso) {
  const d = new Date(iso + (iso.length === 10 ? "T00:00:00" : ""));
  return d.toLocaleDateString(undefined, { month: "short", year: "numeric" });
}

// "CYP2C19:poor_metabolizer|clopidogrel" → "Clopidogrel × CYP2C19 poor metabolizer"
function flagTitle(key) {
  const drugs = [], context = [], conditions = [];
  for (const part of key.split("|")) {
    if (part.startsWith("allergy:")) {
      context.push(`${humanize(part.slice(8))} allergy`);
    } else if (part.includes(":")) {
      const [gene, pheno] = part.split(":");
      context.push(`${gene} ${humanize(pheno)}`);
    } else if (/[<>]/.test(part)) {
      // Keys use lowercase lab tokens (A's format: "egfr<60"); show them as labs are usually written.
      const cond = part.replace(/^[a-z0-9]+/, (t) => LAB_NAMES[t] || t).replace(/\s*([<>]=?)\s*/, " $1 ");
      (part.startsWith("dose") ? conditions : context).push(cond);
    } else {
      drugs.push(cap(humanize(part)));
    }
  }
  const title = [...drugs, ...context].join(" × ");
  return conditions.length ? `${title} (${conditions.join(", ")})` : title;
}

// ---------- motion helpers ----------

// Rolling number: old value slides up and out, new one slides in.
function setTicker(node, text) {
  if (node.dataset.v === text) return;
  node.dataset.v = text;
  const prev = node.querySelector(".tick:not(.out)");
  if (prev && prev.textContent === text) return;
  const next = el("span", { class: REDUCED ? "tick" : "tick in" }, text);
  node.append(next);
  if (!prev) return;
  if (REDUCED) { prev.remove(); return; }
  prev.classList.add("out");
  prev.addEventListener("animationend", () => prev.remove(), { once: true });
}


function sevBar(sev) {
  const n = SEV_LEVEL[sev] || 1;
  return el("span", { class: "sev-bar", "aria-hidden": "true" },
    [0, 1, 2].map((i) => el("i", { class: i < n ? "on" : "" })));
}

// Text that rises out of a mask.
const reveal = (text) => el("span", { class: "reveal" }, el("span", {}, text));

// Packets crossing the barcode strand: eight identical blocks, one per question in the bucket.
function sendPackets(count = 8) {
  if (REDUCED) return;
  const strand = $("strand");
  for (let i = 0; i < count; i++) {
    const p = el("span", { class: "packet", style: `--d:${i * 70}ms` });
    p.addEventListener("animationend", () => p.remove(), { once: true });
    strand.append(p);
  }
}

// ---------- intro + page chrome ----------

function buildWordmark() {
  for (const wm of document.querySelectorAll(".wm")) {
    [...wm.dataset.word].forEach((ch, i) => wm.append(el("span", { class: "ch", style: `--i:${i + (wm.dataset.word === "VAULT" ? 6 : 0)}` }, ch)));
  }
}

function buildStrand() {
  const track = $("strand-track");
  const r = rng(hash("CYP2C19*2/*2 SLCO1B1*1/*5"));
  const target = Math.max(screen.width || 0, 1920);
  const half = [];
  let width = 0;
  while (width < target) {
    const w = 1 + Math.floor(r() * 4), gap = 2 + Math.floor(r() * 6);
    half.push([w, gap]);
    width += w + gap;
  }
  for (const set of [half, half]) {
    for (const [w, gap] of set) track.append(el("i", { style: `width:${w}px;margin-right:${gap}px` }));
  }
}

function playIntro(onOpen) {
  const intro = $("intro");
  if (REDUCED || !intro) { intro?.remove(); onOpen(); return; }
  const cols = $("intro-cols");
  const n = Math.max(6, Math.round(innerWidth / 110));
  const r = rng(hash("genomevault"));
  for (let i = 0; i < n; i++) {
    const col = el("div", { class: "intro-col", style: `--d:${i * 50}ms`, dataset: { dir: i % 2 ? "down" : "up" } });
    let left = 100;
    while (left > 0) {
      const h = Math.min(left, 6 + Math.floor(r() * 26));
      const roll = r();
      const kind = roll < 0.42 ? "b" : roll < 0.6 ? "e" : roll < 0.68 ? "m" : "w";    // raised midnight, blue, cantaloupe, midnight
      col.append(el("i", { class: kind, style: `height:${h}%` }));
      left -= h;
    }
    cols.append(col);
  }
  let opened = false, gone = false;
  const open = () => {
    if (opened) return;
    opened = true;
    intro.classList.add("open");
    setTimeout(onOpen, 280);
    setTimeout(finish, 1100 + n * 50);
  };
  const finish = () => { if (!gone) { gone = true; intro.remove(); } };
  intro.addEventListener("click", () => { open(); finish(); });
  setTimeout(open, 650);
}

function revealSections() {
  const secs = [...document.querySelectorAll(".sec")];
  if (!("IntersectionObserver" in window)) { secs.forEach((s) => s.classList.add("in")); return; }
  const io = new IntersectionObserver((entries) => {
    let k = 0;
    for (const e of entries) {
      if (!e.isIntersecting) continue;
      e.target.style.setProperty("--s", k);
      e.target.querySelector(".rule").style.transitionDelay = `${k++ * 120}ms`;
      e.target.classList.add("in");
      io.unobserve(e.target);
    }
  }, { rootMargin: "0px 0px -8% 0px" });
  secs.forEach((s) => io.observe(s));
  // Never leave content hidden if the observer misbehaves during a live demo.
  setTimeout(() => secs.forEach((s) => s.classList.add("in")), 4000);
}

function watchScroll() {
  const bar = $("bar");
  const onScroll = () => bar.classList.toggle("stuck", scrollY > 8);
  addEventListener("scroll", onScroll, { passive: true });
  onScroll();
}

// ---------- profile ----------

function plist(items) { return el("ul", { class: "plist" }, items); }

function renderProfile(p) {
  const genes = plist(Object.entries(p.genotypes).map(([gene, gt]) => {
    const pheno = p.phenotypes[gene] || "";
    // Status colors (red / green) always sit next to the words, never instead of them.
    // "Not assessed" (D-021: e.g. CYP2D6 can't be called from SNP data) is neutral: no result, not a bad one.
    if (NOT_ASSESSED.test(pheno) || NOT_ASSESSED.test(gt)) {
      return el("li", { title: "This kind of test can't read this gene reliably, so no result is shown." },
        el("span", { class: "k" }, gene),
        el("span", { class: "v hot na" }, "not assessed"));
    }
    const notable = pheno && !/^(normal|reference)/.test(pheno);
    return el("li", {}, el("span", { class: "k" }, gene, el("code", {}, gt)),
      el("span", { class: notable ? "v hot bad" : "v hot good" }, humanize(pheno)));
  }));

  const meds = plist(p.meds.map((m) =>
    el("li", {}, el("span", { class: "k" }, cap(humanize(m.ingredient))),
      el("span", { class: "v" }, m.dose_mg != null ? `${m.dose_mg} mg` : ""))));

  const byTest = new Map();
  for (const lab of p.labs) {
    if (!byTest.has(lab.test)) byTest.set(lab.test, []);
    byTest.get(lab.test).push(lab);
  }
  const labs = plist([...byTest.entries()].map(([test, rows]) => {
    rows.sort((a, b) => b.date.localeCompare(a.date));
    const [latest, prev] = rows;
    return el("li", { title: `${latest.unit} · ${formatDate(latest.date)}`, "data-lab": test },
      el("span", { class: "k" }, test, latest.stale ? el("span", { class: "stale" }, "stale") : null),
      el("span", { class: "v" }, prev ? el("span", { class: "trend" }, `${prev.value} → `) : null,
        `${latest.value} `, el("span", { class: "small" }, latest.unit)));
  }));

  const history = plist([
    ...p.conditions.map((c) => el("li", {}, el("span", { class: "k" }, CONDITIONS[c] || humanize(c)))),
    ...(p.allergies.length
      ? p.allergies.map((a) => el("li", {}, el("span", { class: "k" }, cap(a)), el("span", { class: "v hot bad" }, "allergy")))
      : [el("li", {}, el("span", { class: "k mute" }, "No allergies recorded"))]),
  ]);

  $("profile").replaceChildren(
    el("section", {}, el("h3", {}, "Genes"), genes),
    el("section", {}, el("h3", {}, "Medications"), meds),
    el("section", {}, el("h3", {}, "Labs"), labs),
    el("section", {}, el("h3", {}, "Conditions & allergies"), history),
  );
}

// ---------- flags ----------

function flagRow(f, i) {
  const detailId = `d-${f.id}-${i}-${Math.random().toString(36).slice(2, 7)}`;
  const btn = el("button", { class: "row-btn", type: "button", "aria-expanded": "false", "aria-controls": detailId,
    title: `${ENGINES[f.engine] || f.engine} · ${f.key}` },
    el("span", { class: "r-id" }, f.id),
    el("span", { class: "r-title" }, flagTitle(f.key)),
    el("span", { class: "r-sev" }, cap(f.severity), sevBar(f.severity)));
  const detail = el("div", { class: "row-detail", id: detailId },
    el("div", {}, el("div", { class: "detail-inner" }, el("div", {},
      f.evidence.length ? el("ul", { class: "evidence" }, f.evidence.map((e) => el("li", {}, e))) : null))));
  const li = el("li", { class: `row sev-${f.severity}`, style: `--i:${i}` }, btn, detail);
  btn.addEventListener("click", () => {
    const open = li.classList.toggle("open");
    btn.setAttribute("aria-expanded", String(open));
  });
  return li;
}

// Labs a flag's evidence points to (e.g. potassium, eGFR behind X4) get the red marker in My data.
// Only flags decide this: the data has no reference ranges, so no lab is ever marked "good".
function markFlaggedLabs(flags) {
  const evidence = flags.flatMap((f) => f.evidence).join(" ");
  for (const li of document.querySelectorAll("#profile li[data-lab]")) {
    const test = li.dataset.lab.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    if (new RegExp(`\\b${test}\\b`, "i").test(evidence)) li.querySelector(".v").classList.add("hot", "bad");
  }
}

function renderFlags(data) {
  const n = data.flags.length;
  const high = data.flags.filter((f) => f.severity === "high").length;
  $("flags-summary").replaceChildren(...(n
    ? [el("strong", { class: high ? "count bad" : "count warn" }, `${n} thing${n === 1 ? "" : "s"}`),
       " to raise with your pharmacist. Checked on this device, nothing sent."]
    : [el("strong", { class: "count good" }, "No flags"),
       " from the local tables. A missing entry is not the same as no interaction; ask your pharmacist."]));
  $("flags").replaceChildren(...data.flags.map(flagRow));
  $("notes").replaceChildren(...noteItems(data.notes || []));
  markFlaggedLabs(data.flags);
}

// Expected combinations (D-021), e.g. aspirin + clopidogrel after a stent: information, never a warning.
// Neutral styling on purpose: no red, no severity, labeled "For information".
function noteItems(notes) {
  return notes.map((n) => el("li", { class: "info-note", title: n.source ? `Source: ${n.source}` : null },
    el("span", { class: "info-mark", "aria-hidden": "true" }, "i"),
    el("span", {},
      el("span", { class: "info-label" }, `For information · ${flagTitle(n.key)}`),
      el("span", { class: "info-text" }, n.text))));
}

function noteList(notes) {
  return el("ul", { class: "notes" }, noteItems(notes));
}

// A's no_data marker (rules.no_data_keys): the exact pairs the local tables don't cover, e.g.
// "pantoprazole with clopidogrel" (I4: no inference from omeprazole). Names the pairs, never "no interaction".
function noDataPairs(data) {
  const typed = new Set(data.drugs.map((d) => d.ingredient));
  const others = [...new Set((data.no_data || []).flatMap((k) => k.split("|").filter((p) => !typed.has(p))))];
  if (!others.length) return "";
  const drug = humanize(data.drugs[0].ingredient);
  return `${drug} with ${others.map(humanize).join(", ")}`;
}

async function onCheck(ev) {
  ev.preventDefault();
  const input = $("check-input"), button = ev.target.querySelector("button");
  const text = input.value.trim();
  if (!text) return;
  button.disabled = true;
  const out = $("check-result");
  try {
    const data = await api("/api/check", { text });
    if (!data.drugs.length) {
      out.replaceChildren(el("p", { class: "note" }, `Couldn't recognize "${text}" as a medication. Try the generic name.`));
    } else if (!data.flags.length) {
      const names = data.drugs.map((d) => humanize(d.ingredient)).join(", ");
      const pairs = noDataPairs(data);
      out.replaceChildren(el("p", { class: "note" },
        el("strong", {}, pairs ? `No local entry for ${pairs}. ` : `No local data for ${names}. `),
        "A missing entry does not mean there is no interaction. Ask your pharmacist before taking it."));
    } else {
      out.replaceChildren(el("ol", { class: "index check-result" }, data.flags.map(flagRow)));
      out.querySelector(".index").style.opacity = 1;
      out.querySelector(".index").style.transform = "none";
    }
    if (data.notes?.length) out.append(noteList(data.notes));
    input.value = "";
  } catch (err) {
    out.replaceChildren(el("p", { class: "note" }, `Check failed: ${err.message}`));
  } finally {
    button.disabled = false;
    pollLedger();
  }
}

// ---------- chat ----------

function message(who, body, extra = []) {
  return el("div", { class: `msg ${who === "You" ? "user" : "agent"}` },
    el("span", { class: "who" }, who),
    el("div", { class: "msg-body" }, body, ...extra));
}

// merge.personalize returns paragraphs separated by blank lines; known lead-ins get emphasis.
const LEADS = /^(In general|For you|AI-summarized, verify|Curated \([^)]*\)|Separately):\s*/;

function answerParagraph(text, i) {
  const m = text.match(LEADS);
  const inner = m
    ? el("span", { style: `animation-delay:${i * 110}ms` }, el("strong", {}, `${m[1]}:`), " ", text.slice(m[0].length))
    : el("span", { style: `animation-delay:${i * 110}ms` }, text);
  return el("span", { class: `reveal para${i === 0 ? "" : " later"}` }, inner);
}

// One keyed fact: its pair as a title, its trust label (I6), the first paragraph, and the rest behind "More".
function factBlock(sec, i) {
  const [first, ...rest] = sec.paragraphs;
  const more = rest.length ? el("div", { class: "fact-more", hidden: true }, rest.map((t) => el("p", {}, t))) : null;
  const toggle = rest.length ? el("button", { type: "button", class: "more-btn" }, "More") : null;
  toggle?.addEventListener("click", () => {
    more.hidden = !more.hidden;
    toggle.textContent = more.hidden ? "More" : "Less";
  });
  return el("div", { class: `fact${sec.primary ? " primary" : ""}`, style: `animation-delay:${i * 110}ms` },
    el("div", { class: "fact-head" },
      el("strong", {}, flagTitle(sec.key)),
      el("span", { class: `fact-tier ${sec.tier}` }, sec.tier === "cloud" ? "AI-summarized, verify" : sec.label)),
    el("p", {}, first), more, toggle);
}

// Other facts fold away so the answer leads with what was asked (C-021).
function alsoBlock(secs) {
  const list = el("div", { class: "also-list", hidden: true }, secs.map((s, i) => factBlock({ ...s, primary: false }, i)));
  const btn = el("button", { type: "button", class: "also-btn" },
    `Also relevant: ${secs.map((s) => flagTitle(s.key)).join(" · ")}`);
  btn.addEventListener("click", () => { list.hidden = !list.hidden; btn.classList.toggle("open", !list.hidden); });
  return el("div", { class: "also" }, btn, list);
}

function answerMessage(a) {
  const meta = el("div", { class: "msg-meta" },
    el("span", { class: a.state === "no_data" ? "chip warn" : "chip solid" }, STATES[a.state] || a.state),
    a.sent_to_cloud
      ? el("span", { class: "chip" }, "Asked privately · decoy group of 8")
      : el("span", { class: "chip good" }, "Answered on device"));
  if (!a.sections) {   // mock merge: plain paragraphs, trust tiers are written into the text
    return message("Vault", a.text.split(/\n{2,}/).map(answerParagraph), [meta]);
  }
  const lead = a.sections.filter((s) => s.kind === "lead");
  const facts = a.sections.filter((s) => s.kind === "fact");
  const primary = facts.find((s) => s.primary) || (lead.length ? null : facts[0]);
  const others = facts.filter((s) => s !== primary);
  const personal = a.sections.filter((s) => s.kind === "personal");
  const closing = a.sections.filter((s) => s.kind === "closing");
  const nodes = [
    ...lead.flatMap((s) => s.paragraphs.map((t, i) => answerParagraph(t, i))),
    primary ? factBlock(primary, 0) : null,
    ...personal.flatMap((s) => s.paragraphs.map((t) => answerParagraph(t, 1))),
    others.length ? alsoBlock(others) : null,
    ...closing.flatMap((s) => s.paragraphs.map((t) => answerParagraph(t, 2))),
  ];
  return message("Vault", nodes, [meta]);
}

async function ask(question) {
  const chat = $("chat");
  // Demo chips stay put: asking the same one again shows the knowledge-base hit (S6).
  document.querySelectorAll(`#chips .suggestion`).forEach((b) => {
    if (b.dataset.q === question) b.classList.add("asked");
  });
  chat.append(message("You", reveal(question)));
  const pending = message("Vault", "Checking locally first");
  pending.classList.add("pending");
  chat.append(pending);
  const button = $("ask-form").querySelector("button");
  button.disabled = true;
  try {
    pending.replaceWith(answerMessage(await api("/api/ask", { question })));
  } catch (err) {
    pending.replaceWith(message("Vault", `Couldn't answer: ${err.message}`));
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

// ---------- actions (F7): prepared on device, the user sends them ----------

function lineButton(label, attrs = {}) {
  const tag = attrs.href ? "a" : "button";
  return el(tag, { class: "line-btn", type: tag === "button" ? "button" : null, ...attrs }, el("span", {}, label));
}

async function copyText(text, button) {
  const label = button.querySelector("span");
  try {
    await navigator.clipboard.writeText(text);
    label.textContent = "Copied";
  } catch {
    label.textContent = "Select the text to copy";
  }
  setTimeout(() => { label.textContent = "Copy text"; }, 1800);
}

function formatDue(iso) {
  return new Date(`${iso}T00:00:00`).toLocaleDateString(undefined, { weekday: "short", day: "numeric", month: "short" });
}

const ACTIONS = [
  {
    id: "A1", key: "action:pharmacist", title: "Draft a message to your pharmacist", kind: "Message",
    async build() {
      const { text } = await api("/api/actions/pharmacist");
      const copy = lineButton("Copy text");
      copy.addEventListener("click", () => copyText(text, copy));
      return [
        el("pre", { class: "draft" }, text),
        el("div", { class: "action-bar" }, copy,
          el("span", { class: "mute small" }, "Not sent. Paste it into your pharmacy's portal or an email yourself.")),
      ];
    },
  },
  {
    id: "A2", key: "action:summary", title: "One-page visit summary", kind: "Print",
    async build() {
      const s = await api("/api/actions/summary");
      return [
        el("dl", { class: "sum-grid" }, s.sections.flatMap((sec) => [
          el("dt", {}, sec.heading),
          el("dd", {}, sec.items.length > 3 ? `${sec.items.slice(0, 3).join(" · ")} · +${sec.items.length - 3} more` : sec.items.join(" · ")),
        ])),
        el("div", { class: "action-bar" },
          lineButton("Open printable page", { href: "/summary", target: "_blank", rel: "noopener" }),
          el("span", { class: "mute small" }, `Prepared ${s.prepared}. Print it or show it on your phone at the visit.`)),
      ];
    },
  },
  {
    id: "A3", key: "action:reminders", title: "Reminders", kind: "Calendar",
    async build() {
      const { reminders } = await api("/api/actions/reminders");
      return [
        reminders.length
          ? el("ol", { class: "rem-list" }, reminders.map((r) => el("li", {},
            el("span", { class: "rem-due" }, formatDue(r.due)),
            el("span", {}, el("span", { class: "rem-title" }, r.title), el("span", { class: "mute" }, r.detail)))))
          : el("p", { class: "mute" }, "No reminders right now."),
        el("div", { class: "action-bar" },
          lineButton("Download calendar file", { href: "/api/actions/reminders.ics", download: "genomevault-reminders.ics" }),
          el("span", { class: "mute small" }, "Calendar entries only say “GenomeVault: …”. Health details stay on this device.")),
      ];
    },
  },
  {
    id: "A4", key: "action:phone", title: "Use your phone", kind: "Phone",
    async build() {
      const p = await api("/api/phone");
      const where = p.url
        ? el("p", {}, "On your phone, open ", el("strong", {}, p.url), ".")
        : el("p", {}, "Start the app for the phone with ", el("code", {}, "bash phone/serve_https.sh"),
            ", then open the address it prints on your phone (same Wi-Fi).");
      return [
        where,
        el("div", { class: "pair-code", "aria-label": "Pairing code" }, p.code),
        el("p", { class: "mute small" },
          "Type this code on the phone once. The phone can then scan labels and see reminders. "
          + "Photos are read on this laptop and not kept; nothing leaves your network."),
      ];
    },
  },
];

function actionRow(a, i) {
  const detailId = `d-${a.id}`;
  const body = el("div", {});
  const btn = el("button", { class: "row-btn", type: "button", "aria-expanded": "false", "aria-controls": detailId },
    el("span", { class: "r-id" }, pad2(i + 1)),
    el("span", { class: "r-title" }, a.title),
    el("span", { class: "r-sev" }, "Open"));
  const li = el("li", { class: "row action", style: `--i:${i}` }, btn,
    el("div", { class: "row-detail", id: detailId }, el("div", {}, el("div", { class: "detail-inner" }, body))));
  btn.addEventListener("click", async () => {
    const open = li.classList.toggle("open");
    btn.setAttribute("aria-expanded", String(open));
    btn.querySelector(".r-sev").textContent = open ? "Close" : "Open";
    if (!open) return;
    body.replaceChildren(el("p", { class: "mute" }, "Preparing on this device…"));
    try {
      body.replaceChildren(...await a.build());
    } catch (err) {
      body.replaceChildren(el("p", { class: "mute" }, `Couldn't prepare this: ${err.message}`));
    }
  });
  return li;
}

function renderActions() {
  $("actions").replaceChildren(...ACTIONS.map(actionRow));
}

// ---------- captures from the phone (S2) ----------

let lastCapture = 0;

function captureItem(c) {
  const names = c.drugs.map((d) => cap(humanize(d.ingredient)) + (d.dose_mg ? ` ${d.dose_mg} mg` : "")).join(", ");
  const worst = c.flags.some((f) => f.severity === "high") ? "high" : c.flags.length ? "medium" : "none";
  const ids = [...new Set(c.flags.map((f) => f.id))];
  const how = { photo: "Photo", sample: "Sample label", typed: "Typed" }[c.source] || "Phone";
  return el("li", { class: `capture sev-${worst}` },
    el("span", { class: "cap-how" }, how),
    el("span", { class: "cap-drug" }, names),
    el("span", { class: "cap-flags" }, ids.length ? `${c.flags.length} flag${c.flags.length === 1 ? "" : "s"} · ${ids.join(", ")}` : "No flags"));
}

async function pollCaptures() {
  try {
    const { captures } = await api(`/api/captures?since=${lastCapture}`);
    if (!captures.length) return;
    $("from-phone").hidden = false;
    for (const c of captures) {
      $("captures").prepend(captureItem(c));
      lastCapture = Math.max(lastCapture, c.seq);
    }
  } catch { /* next tick */ }
}

// ---------- ledger ----------

let lastSeq = 0;
let polling = false;
let firstPoll = true;

// The 8 questions that left in one bucket. Only this device can mark which one is the user's.
async function showOutbound(e, li, toggle) {
  const open = li.classList.toggle("open");
  toggle.setAttribute("aria-expanded", String(open));
  toggle.querySelector(".cells-label").textContent = open ? "Hide" : "See the 8 questions";
  let box = li.querySelector(".outq");
  if (!open) { box?.remove(); return; }
  box = el("div", { class: "outq" }, el("p", { class: "mute" }, "Loading…"));
  li.append(box);
  try {
    const d = await api(`/api/ledger/${e.seq}/outbound`);
    if (!d.texts.length) {
      box.replaceChildren(el("p", { class: "mute" },
        d.available ? "No text was recorded for this entry." : "The exact texts appear once B's ledger is merged."));
      return;
    }
    const mine = new Set(d.mine);
    box.replaceChildren(
      el("ol", {}, d.texts.map((t, i) => el("li", { class: mine.has(i) ? "mine" : "" },
        el("span", { class: "oq-n" }, pad2(i + 1)),
        el("span", { class: "oq-t" }, t),
        mine.has(i) ? el("span", { class: "oq-tag" }, "yours") : null))),
      el("p", { class: "mute" }, mine.size
        ? `The cloud got all ${d.texts.length} in the same shape. Only this device knows which ${mine.size === 1 ? "one is" : "ones are"} yours.`
        : `The cloud got all ${d.texts.length} in the same shape.`));
  } catch (err) {
    box.replaceChildren(el("p", { class: "mute" }, `Couldn't load: ${err.message}`));
  }
}

function ledgerEntry(e) {
  const time = new Date(e.ts).toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit", second: "2-digit" });
  const leaves = e.kind === "bucket" || e.kind === "cover";
  const toggle = leaves ? el("button", { class: "cells", type: "button", "aria-expanded": "false" },
    el("span", { class: "cells-row", "aria-hidden": "true" },
      Array.from({ length: 8 }, (_, i) => el("i", { style: `--i:${i}` }))),
    el("span", { class: "cells-label" }, "See the 8 questions")) : null;
  const li = el("li", { class: `entry k-${e.kind}`,
    title: [time, e.bucket_id, `personal fields ${e.personal_fields_sent}`].filter(Boolean).join(" · ") },
    el("span", { class: "seq" }, pad2(e.seq)),
    el("span", { class: "desc" }, e.pack ? "Knowledge pack · same for every user" : (LEDGER_KINDS[e.kind] || e.kind), toggle),
    el("span", { class: "bytes" }, formatBytes(e.bytes_out)));
  toggle?.addEventListener("click", () => showOutbound(e, li, toggle));
  return li;
}

async function pollLedger() {
  if (polling) return;
  polling = true;
  try {
    const data = await api(`/api/ledger?since=${lastSeq}`);
    const list = $("ledger");
    if (data.entries.length) {
      list.querySelector(".ledger-empty")?.remove();
      let outbound = 0;
      for (const e of data.entries) {
        list.prepend(ledgerEntry(e));
        lastSeq = Math.max(lastSeq, e.seq);
        if (e.kind === "bucket" || e.kind === "cover") outbound++;
      }
      if (outbound && !firstPoll) sendPackets(8);
    }
    firstPoll = false;
    const t = data.totals;
    setTicker($("ledger-bytes"), formatBytes(t.bytes_out));
    setTicker($("total-bytes"), formatBytes(t.bytes_out));
    setTicker($("ledger-personal"), String(t.personal_fields_sent));
    $("ledger-personal").classList.toggle("good", t.personal_fields_sent === 0);
    $("ledger-personal").classList.toggle("bad", t.personal_fields_sent > 0);
    applyCloud(data.cloud);
    $("live-cover").hidden = !data.cover;
    const learned = $("learned");
    if (data.learned) {
      learned.hidden = false;
      setTicker($("learned-n"), String(data.learned.fresh));
    }
  } catch {
    // server restarting; try again next tick
  } finally {
    polling = false;
  }
}

// ---------- knowledge pack sync (D-027, S6) ----------

let syncPoll = null;

function applySync(s) {
  if (!s?.available) return;
  $("sync").hidden = false;
  const btn = $("sync-btn"), msg = $("sync-msg");
  btn.disabled = s.running || cloudState?.online === false;
  btn.querySelector("span").textContent = s.running ? "Syncing…" : s.result ? "Sync again" : "Sync knowledge pack";
  if (s.running) msg.textContent = "Downloading the same groups every user gets, in shuffled order.";
  else if (s.result?.error) msg.textContent = `Sync stopped (${s.result.error}). Try again when online.`;
  else if (s.result?.offline) msg.textContent = "Went offline during the sync; what arrived is kept.";
  else if (s.result) {
    const r = s.result;
    msg.textContent = `Synced: ${r.sent} groups sent, ${r.skipped} already here, ${r.facts} facts stored. Same for every user.`;
  } else if (cloudState?.online === false) msg.textContent = "Connect to sync. Stored answers keep working offline.";
}

async function refreshSync() {
  try {
    const s = await api("/api/sync");
    applySync(s);
    if (!s.running && syncPoll) { clearInterval(syncPoll); syncPoll = null; pollLedger(); }
  } catch { /* next tick */ }
}

async function startSync() {
  try {
    applySync(await api("/api/sync", {}));
  } catch (err) {
    $("sync-msg").textContent = err.message.includes("409") ? "Can't sync right now (offline or already syncing)." : err.message;
  }
  if (!syncPoll) syncPoll = setInterval(refreshSync, 700);
}

// ---------- online / offline (F8, S6) ----------

const ASK_LEDE = {
  online: "Only general questions leave this device, hidden in a group of 8.",
  offline: "You're offline. Local checks and answers stored on this device still work; nothing can leave.",
};
let cloudState = null;

function applyCloud(c) {
  if (!c) return;
  cloudState = c;
  const net = $("net");
  const offline = !c.online;
  net.hidden = false;
  net.disabled = !c.toggle;
  net.title = c.toggle ? (offline ? "Turn the cloud back on" : "Simulate Wi-Fi off: nothing can leave")
    : "Offline switch arrives with B's cloud module";
  net.setAttribute("aria-checked", String(offline));
  net.classList.toggle("off", offline);
  $("net-state").textContent = offline ? "Offline" : "Online";
  document.body.classList.toggle("offline", offline);
  $("ask-lede").textContent = offline ? ASK_LEDE.offline : ASK_LEDE.online;
  const syncBtn = $("sync-btn");
  if (syncBtn && !$("sync").hidden && syncBtn.querySelector("span").textContent !== "Syncing…") syncBtn.disabled = offline;
}

async function toggleOffline() {
  if (!cloudState?.toggle) return;
  const net = $("net");
  net.disabled = true;
  try {
    applyCloud(await api("/api/offline", { offline: cloudState.online }));
  } catch { /* keep the last state */ } finally {
    net.disabled = !cloudState?.toggle;
    pollLedger();
  }
}

// ---------- tabs: one thing on screen at a time ----------

const TABS = ["meds", "ask", "actions", "data"];

function selectTab(name, { focus = false, push = true } = {}) {
  if (!TABS.includes(name)) name = "meds";
  for (const t of TABS) {
    const on = t === name;
    const tab = $(`tab-${t}`), panel = $(`panel-${t}`);
    tab.setAttribute("aria-selected", String(on));
    tab.tabIndex = on ? 0 : -1;
    panel.hidden = !on;
    panel.classList.toggle("active", on);
    if (on && focus) tab.focus();
  }
  if (push) {
    try { history.replaceState(null, "", name === "meds" ? location.pathname + location.search : `#${name}`); } catch { /* file or sandbox */ }
  }
}

function initTabs() {
  const nav = document.querySelector(".tabs");
  nav.addEventListener("click", (ev) => {
    const t = ev.target.closest(".tab");
    if (t) selectTab(t.dataset.tab);
  });
  nav.addEventListener("keydown", (ev) => {
    if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(ev.key)) return;
    const cur = TABS.indexOf(document.querySelector('.tab[aria-selected="true"]').dataset.tab);
    const next = ev.key === "Home" ? 0 : ev.key === "End" ? TABS.length - 1
      : (cur + (ev.key === "ArrowRight" ? 1 : -1) + TABS.length) % TABS.length;
    ev.preventDefault();
    selectTab(TABS[next], { focus: true });
  });
  addEventListener("hashchange", () => selectTab(location.hash.slice(1), { push: false }));
  selectTab(location.hash.slice(1), { push: false });
}

// ---------- boot ----------

async function loadData() {
  try {
    const status = await api("/api/status");
    $("demo-badge").hidden = !status.demo;
    applyCloud(status.cloud);
    // Which modules are still mocks: for the team, shown only with ?debug.
    if (new URLSearchParams(location.search).has("debug")) {
      const mocks = Object.entries(status.modules).filter(([, m]) => m === "mock").map(([n]) => n);
      $("modules").textContent = mocks.length ? `Running on mocks: ${mocks.join(", ")}` : "All modules live";
      $("modules").hidden = false;
    }
  } catch { /* non-critical */ }

  try {
    renderProfile(await api("/api/profile"));
  } catch (err) {
    $("profile").replaceChildren(el("p", { class: "mute" }, `Couldn't load profile: ${err.message}`));
  }
  try {
    renderFlags(await api("/api/flags"));
  } catch (err) {
    $("flags-summary").textContent = `Couldn't run the medication check: ${err.message}`;
  }
}

function boot() {
  buildWordmark();
  buildStrand();
  watchScroll();
  initTabs();
  $("net").addEventListener("click", toggleOffline);
  $("sync-btn").addEventListener("click", startSync);
  renderActions();
  $("check-form").addEventListener("submit", onCheck);
  $("ask-form").addEventListener("submit", onAsk);
  $("chips").addEventListener("click", (ev) => {
    const q = ev.target.closest(".suggestion")?.dataset.q;
    if (q) ask(q);
  });

  const data = loadData();
  playIntro(async () => {
    document.body.classList.add("ready");
    revealSections();
    await data;
    pollLedger();
    setInterval(pollLedger, 1500);
    pollCaptures();
    setInterval(pollCaptures, 2000);
    refreshSync();
  });
}

boot();
