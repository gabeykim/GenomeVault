// GenomeVault phone page (Agent C, BRIEF queue 5; F2, S2, S6). Plain JS, no external assets (I8).
// The photo goes only to the laptop on the local network; A's capture.from_image reads it there.
// No voice input on purpose: browser speech recognition sends audio to a cloud service.
"use strict";

const $ = (id) => document.getElementById(id);

function el(tag, attrs = {}, ...children) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v === null || v === undefined || v === false) continue;
    if (k === "class") node.className = v; else node.setAttribute(k, v === true ? "" : v);
  }
  for (const c of children.flat()) {
    if (c === null || c === undefined || c === false) continue;
    node.append(c instanceof Node ? c : document.createTextNode(String(c)));
  }
  return node;
}

class Unpaired extends Error {}

async function api(path, { body, json, headers = {} } = {}) {
  const opts = { headers: { ...headers } };
  if (json !== undefined) {
    opts.method = "POST"; opts.body = JSON.stringify(json); opts.headers["Content-Type"] = "application/json";
  } else if (body !== undefined) {
    opts.method = "POST"; opts.body = body;
  }
  const res = await fetch(path, opts);
  if (res.status === 401) throw new Unpaired();
  if (!res.ok) {
    let detail = `${res.status}`;
    try { detail = (await res.json()).detail || detail; } catch { /* not JSON */ }
    throw new Error(detail);
  }
  return res.json();
}

const cap = (s) => s.charAt(0).toUpperCase() + s.slice(1);
const LAB_NAMES = { egfr: "eGFR", alt: "ALT", ck: "CK", ldl: "LDL" };

function flagTitle(key) {
  const drugs = [], context = [];
  for (const part of key.split("|")) {
    if (part.includes(":")) { const [g, p] = part.split(":"); context.push(`${g} ${p.replace(/_/g, " ")}`); }
    else if (/[<>]/.test(part)) {
      if (!part.startsWith("dose")) context.push(part.replace(/^[a-z0-9]+/, (t) => LAB_NAMES[t] || t).replace(/([<>]=?)/, " $1 "));
    } else drugs.push(cap(part));
  }
  return [...drugs, ...context].join(" × ");
}

function formatBytes(n) { return n < 1024 ? `${n} B` : `${(n / 1024).toFixed(1)} KB`; }

// ---------- screens ----------

function show(screen) {
  $("pair-screen").hidden = screen !== "pair";
  $("main-screen").hidden = screen !== "main";
}

async function start() {
  try {
    await api("/api/status");
    show("main");
    loadReminders();
    refreshSent();
    setInterval(refreshSent, 5000);
  } catch (err) {
    if (err instanceof Unpaired) { show("pair"); $("pair-code").focus(); }
    else { show("main"); $("result").replaceChildren(el("p", { class: "note" }, `Can't reach the laptop: ${err.message}`)); }
  }
}

async function onPair(ev) {
  ev.preventDefault();
  const code = $("pair-code").value.trim();
  if (!code) return;
  const msg = $("pair-msg");
  try {
    await api("/api/phone/pair", { json: { code } });
    msg.textContent = "";
    start();
  } catch (err) {
    msg.className = "msg bad";
    msg.textContent = err.message === "wrong code" ? "That code doesn't match the laptop. Try again." : err.message;
  }
}

// ---------- capture ----------

function renderResult(data, preview) {
  const out = $("result");
  if (!data.drugs.length) {
    out.replaceChildren(el("p", { class: "note" },
      el("strong", {}, "Couldn't read this label on the laptop. "), "Type the medicine name below instead."));
    $("type-input").focus();
    return;
  }
  const names = data.drugs.map((d) => cap(d.ingredient) + (d.dose_mg ? ` ${d.dose_mg} mg` : "")).join(", ");
  const nodes = [
    el("div", { class: "read" },
      preview ? el("img", { src: preview, alt: "" }) : el("span", {}),
      el("div", {}, el("span", { class: "small mute" }, "Read on the laptop"), el("strong", {}, names))),
  ];
  if (data.flags.length) {
    nodes.push(el("ul", { class: "flags" }, data.flags.map((f) =>
      el("li", { class: f.severity }, el("span", { class: "id" }, f.id), el("span", {}, flagTitle(f.key)),
        el("span", { class: "sev" }, cap(f.severity))))));
    nodes.push(el("p", { class: "note" }, "Raise these with your pharmacist before taking it."));
  } else {
    nodes.push(el("p", { class: "note" }, el("strong", {}, "No flags in the local tables. "),
      "A missing entry does not mean there is no interaction. Ask your pharmacist."));
  }
  for (const n of data.notes || []) {
    nodes.push(el("div", { class: "info" }, el("span", { class: "i", "aria-hidden": "true" }, "i"),
      el("span", {}, el("span", { class: "small mute" }, "For information · "), n.text)));
  }
  nodes.push(el("p", { class: "laptop" }, "Also shown on your laptop"));
  out.replaceChildren(...nodes);
}

async function sendImage(blob, source, preview) {
  $("result").replaceChildren(el("p", { class: "note mute" }, "Reading on the laptop…"));
  try {
    const data = await api("/api/capture", {
      body: blob, headers: { "Content-Type": blob.type || "application/octet-stream", "X-GV-Source": source },
    });
    renderResult(data, preview);
  } catch (err) {
    if (err instanceof Unpaired) { show("pair"); return; }
    $("result").replaceChildren(el("p", { class: "note" }, `Couldn't send the photo: ${err.message}`));
  } finally {
    refreshSent();
  }
}

function onPhoto(ev) {
  const file = ev.target.files?.[0];
  if (!file) return;
  sendImage(file, "photo", URL.createObjectURL(file));   // preview stays on the phone
  ev.target.value = "";
}

async function onSample(ev) {
  const btn = ev.target.closest(".sample");
  if (!btn) return;
  btn.classList.add("busy");
  try {
    const blob = await (await fetch(btn.dataset.src)).blob();
    await sendImage(blob, "sample", btn.dataset.src);
  } finally {
    btn.classList.remove("busy");
  }
}

async function onType(ev) {
  ev.preventDefault();
  const input = $("type-input");
  const text = input.value.trim();
  if (!text) return;
  try {
    const data = await api("/api/check", { json: { text, via: "phone" } });
    renderResult(data, null);
    input.value = "";
  } catch (err) {
    if (err instanceof Unpaired) { show("pair"); return; }
    $("result").replaceChildren(el("p", { class: "note" }, `Check failed: ${err.message}`));
  } finally {
    refreshSent();
  }
}

// ---------- reminders, bytes sent ----------

async function loadReminders() {
  try {
    const { reminders } = await api("/api/actions/reminders");
    const day = (iso) => new Date(`${iso}T00:00:00`).toLocaleDateString(undefined, { weekday: "short", day: "numeric", month: "short" });
    $("reminders").replaceChildren(...(reminders.length ? reminders.map((r) =>
      el("li", {}, el("span", { class: "due" }, day(r.due)), el("span", {}, r.title, el("span", { class: "detail" }, r.detail))))
      : [el("li", { class: "mute" }, "No reminders right now.")]));
  } catch {
    $("reminders").replaceChildren(el("li", { class: "mute" }, "Couldn't load reminders."));
  }
}

async function refreshSent() {
  try { $("sent").textContent = formatBytes((await api("/api/ledger")).totals.bytes_out); } catch { /* keep last */ }
}

$("pair-form").addEventListener("submit", onPair);
$("photo").addEventListener("change", onPhoto);
document.querySelector(".samples").addEventListener("click", onSample);
$("type-form").addEventListener("submit", onType);
start();
