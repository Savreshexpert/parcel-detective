"use strict";
const $ = (s) => document.querySelector(s);
const escapeHTML = (s) =>
  String(s ?? "").replace(
    /[&<>"']/g,
    (c) =>
      ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;",
      })[c],
  );
const labels = {
  scan_history: "Scan history",
  dispatch_records: "Dispatch records",
  handover_notes: "Shift handover",
  finish_investigation: "Prepare finding",
  request_physical_check: "Request physical check",
};
let cases = [],
  selected = null,
  modified = {},
  currentSource = "dispatch_records",
  baseline = null,
  busy = false;

async function api(path, data) {
  const controller = new AbortController();
  const timeout = path === "/api/investigate" ? 300000 : 30000;
  const timer = setTimeout(() => controller.abort(), timeout);
  const options = { signal: controller.signal };
  if (data !== undefined) {
    options.method = "POST";
    options.headers = { "Content-Type": "application/json" };
    options.body = JSON.stringify(data);
  }
  try {
    const response = await fetch(path, options);
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.error || "The request could not be completed.");
    }
    return payload;
  } catch (error) {
    if (error.name === "AbortError") {
      throw new Error(
        "The server took too long to reply. Check its terminal before starting another run.",
      );
    }
    throw error;
  } finally {
    clearTimeout(timer);
  }
}

function notice(message = "") {
  $("#notice").textContent = message;
  $("#notice").hidden = !message;
}

function showView(view) {
  document
    .querySelectorAll(".view")
    .forEach((el) => (el.hidden = el.id !== view));
  document
    .querySelectorAll(".nav-item")
    .forEach((el) => el.classList.toggle("active", el.dataset.view === view));
  $("#page-crumb").textContent = {
    desk: "Investigation desk",
    evaluation: "Evaluation lab",
    guide: "How it works",
  }[view];
}

function showTab(tab) {
  document
    .querySelectorAll(".detail-view")
    .forEach((el) => (el.hidden = el.id !== tab));
  document.querySelectorAll(".detail-tab").forEach((el) => {
    const active = el.dataset.tab === tab;
    el.classList.toggle("active", active);
    el.setAttribute("aria-selected", active);
  });
}

function setBusy(value, message = "Collecting evidence and checking records…") {
  busy = value;
  [
    "#run",
    "#rerun",
    "#run-evaluation",
    "#reset-clues",
    "#remove-record",
    "#source-select",
  ].forEach((s) => ($(s).disabled = value));
  $("#run").textContent = value ? "Please wait…" : "Investigate parcel ↗";
  $("#action-note").textContent = value
    ? message
    : "Ready to follow the evidence";
  $("#case-list").inert = value;
}

function renderQueue() {
  const q = $("#search").value.toLowerCase();
  const filtered = cases.filter((c) =>
    `${c.parcel_id} ${c.id} ${c.title}`.toLowerCase().includes(q),
  );
  $("#case-list").innerHTML =
    filtered
      .map(
        (c) =>
          `<button class="case-button ${selected?.id === c.id ? "selected" : ""}"
                   data-case="${escapeHTML(c.id)}" aria-pressed="${selected?.id === c.id}">
            <strong>${escapeHTML(c.parcel_id)}</strong>
            <span class="tiny-case">${escapeHTML(c.id)}</span>
            <p>${escapeHTML(c.title)}</p>
            <span class="queue-status">Needs investigation</span>
          </button>`,
      )
      .join("") || '<p class="no-cases">No matching cases.</p>';
}
async function selectCase(id) {
  if (busy) return;
  setBusy(true, "Loading case records…");
  try {
    const c = await api(`/api/cases/${encodeURIComponent(id)}`);
    selected = c;
    modified = {};
    baseline = null;
    $("#case-id").textContent = `CASE ${c.id}`;
    $("#parcel-title").innerHTML =
      `Parcel ${escapeHTML(c.parcel_id)} <span class="status-tag">Missing alert</span>`;
    $("#case-report").textContent = c.report;
    $("#clue-count").textContent =
      `${Object.values(c.records).flat().length} available records`;
    $("#result").hidden = true;
    $("#response-stat").textContent = "—";
    $("#timeline-count").textContent = "0";
    $("#timeline").innerHTML =
      '<div class="empty-state"><div class="empty-icon">⌕</div><h3>Start with a question.</h3><p>Run the investigation to collect scanner events, dispatch records and handover notes.</p><div class="source-pills"><span>Scanner events</span><span>Bag manifests</span><span>Shift notes</span></div></div>';
    $("#trace").innerHTML =
      '<div class="empty-state"><h3>The decisions will appear here.</h3><p>Each step records who selected the tool and which records it returned.</p></div>';
    $("#edit-error").textContent = "";
    loadEditor();
    showTab("timeline");
    document.querySelectorAll("[data-case]").forEach((button) => {
      const active = button.dataset.case === id;
      button.classList.toggle("selected", active);
      button.setAttribute("aria-pressed", active);
    });
    notice();
  } catch (e) {
    notice(e.message);
  } finally {
    setBusy(false);
  }
}

function loadEditor() {
  if (selected)
    $("#clue-editor").value = JSON.stringify(
      modified[currentSource] ?? selected.records[currentSource],
      null,
      2,
    );
}

function saveEditor() {
  const rows = JSON.parse($("#clue-editor").value);
  if (!Array.isArray(rows))
    throw new Error(
      "Use a JSON array: [record, record]. An empty array [] removes this source's records.",
    );
  if (JSON.stringify(rows) !== JSON.stringify(selected.records[currentSource]))
    modified[currentSource] = rows;
  else delete modified[currentSource];
}

function citations(text) {
  return escapeHTML(text).replace(
    /\[([A-Za-z0-9_-]+)\]/g,
    (_, id) => `<button class="citation" data-record="${id}">${id}</button>`,
  );
}

function renderRun(r) {
  if (!r.clues_changed) baseline = r;
  const f = r.finding;
  $("#result").hidden = false;
  $("#result").classList.toggle("needs-check", f.physical_check_required);
  const delta =
    r.clues_changed && baseline
      ? `<div class="explanation-label">CLUE COMPARISON · ${escapeHTML(baseline.finding.label)} → ${escapeHTML(f.label)}</div>`
      : "";
  const physicalCheck = r.physical_check
    ? `<p>${escapeHTML(r.physical_check.instructions)}</p>
       <div class="explanation-label">CHECK REQUEST PREPARED · NOT SENT TO A WORKER</div>`
    : "";
  $("#result").innerHTML = `
    <div class="result-heading">
      <h3>${escapeHTML(f.label)}</h3>
      <span class="provisional">PROVISIONAL FINDING</span>
    </div>
    <p>${citations(r.explanation.text)}</p>
    <div class="location-line">
      <span>NEXT PLACE TO CHECK</span>
      <strong>${escapeHTML(f.location)}</strong>
    </div>
    ${physicalCheck}
    <div class="explanation-label">
      ${escapeHTML(r.explanation.provider)} · Record IDs checked · Physical location unconfirmed
    </div>
    ${delta}
    <button id="export-run" class="button text-button">Download investigation JSON ↓</button>`;
  $("#response-stat").textContent =
    r.metrics.response_time_ms < 1000
      ? `${r.metrics.response_time_ms.toFixed(1)} ms`
      : `${(r.metrics.response_time_ms / 1000).toFixed(1)} s`;
  $("#timeline-count").textContent = r.timeline.length;
  $("#action-note").textContent = r.clues_changed
    ? "Investigation used your edited clues"
    : "Investigation complete · review the evidence";
  const timeline = r.timeline
    .map((row) => {
      const time = new Date(row.timestamp).toLocaleTimeString("en-IN", {
        hour: "2-digit",
        minute: "2-digit",
        hour12: false,
        timeZone: "Asia/Kolkata",
      });
      const title = row.event
        ? `${row.event.toLowerCase().replaceAll("_", " ")} event`
        : row.status
          ? `${row.status} · ${row.bag_id || "bag not recorded"}`
          : "Shift handover note";
      const details =
        row.note ||
        [
          row.location,
          row.expected_bag_id ? `Expected bag: ${row.expected_bag_id}` : null,
          row.bag_id ? `Recorded bag: ${row.bag_id}` : null,
        ]
          .filter(Boolean)
          .join(" · ");
      return `
        <article class="event" id="record-${escapeHTML(row.record_id)}">
          <div class="event-time">${time}</div>
          <div class="event-rail">
            <span class="event-dot"></span><span class="event-line"></span>
          </div>
          <div class="event-body">
            <div class="event-top">
              <span class="event-title">${escapeHTML(title)}</span>
              <span class="record-id">${escapeHTML(row.record_id)}</span>
            </div>
            <p>${escapeHTML(details)}</p>
            <span class="event-source">
              ${escapeHTML(labels[row.source])}${row.verified === false ? " · unverified" : ""}
            </span>
          </div>
        </article>`;
    })
    .join("");
  $("#timeline").innerHTML =
    `<div class="timeline-head"><strong>Collected evidence</strong><span>21 OCT · IST · OLDEST FIRST</span></div>${timeline || '<div class="empty-state"><h3>No records returned.</h3><p>All three sources were checked. A physical check is required.</p></div>'}`;
  $("#trace").innerHTML = r.trace
    .map(
      (t) =>
        `<article class="trace-step">
          <div class="trace-top">
            <span class="step-num">${t.step}</span>
            <strong>${escapeHTML(labels[t.tool])}</strong>
            <small>${t.confidence === null ? "No model score" : `${Math.round(t.confidence * 100)}% choice confidence`}</small>
          </div>
          <p>Selected by ${escapeHTML(t.selector)} · ${t.latency_ms} ms
            <br>Available: ${t.available_tools.map((x) => escapeHTML(labels[x])).join(" / ")}
            <br>Returned: ${t.record_ids.map(escapeHTML).join(", ") || "No records / terminal action"}
            ${t.model ? `<br>Model: ${escapeHTML(t.model)}` : ""}
          </p>
        </article>`,
    )
    .join("");
  $("#export-run").onclick = () =>
    download(`${r.parcel_id}-investigation.json`, r);
}
async function run() {
  if (busy || !selected) return;
  try {
    saveEditor();
    $("#edit-error").textContent = "";
  } catch (e) {
    $("#edit-error").textContent = `Invalid clue JSON: ${e.message}`;
    showTab("clues");
    return;
  }
  notice();
  setBusy(true);
  try {
    const result = await api("/api/investigate", {
      case_id: selected.id,
      overrides: Object.keys(modified).length ? modified : undefined,
    });
    setBusy(false);
    renderRun(result);
    showTab("timeline");
  } catch (e) {
    setBusy(false);
    notice(e.message);
  }
}

function download(name, data) {
  const blob = new Blob([JSON.stringify(data, null, 2)], {
    type: "application/json",
  });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = name;
  a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 1000);
}

function renderEvaluation(result) {
  const value = (number, suffix = "") =>
    number === null ? "—" : `${Number(number).toFixed(2)}${suffix}`;
  const rows = result.rows
    .map(
      (row) => `
    <tr>
      <td>${escapeHTML(row.case_id)}</td>
      <td>${escapeHTML(row.expected.replaceAll("_", " "))}</td>
      <td>${escapeHTML(row.actual.replaceAll("_", " "))}</td>
      <td>${value(row.response_time_ms, " ms")}</td>
      <td>${row.evidence_tool_calls ?? "—"}</td>
      <td class="${row.correct ? "pass" : "fail"}">${row.correct ? "PASS" : "FAIL"}</td>
    </tr>
    ${row.error ? `<tr><td colspan="6">${escapeHTML(row.error)}</td></tr>` : ""}
  `,
    )
    .join("");

  $("#evaluation-output").classList.remove("evaluation-empty");
  $("#evaluation-output").innerHTML = `
    <div class="eval-label">
      <strong>${result.mode === "demo" ? "DEMO RULES" : "LIVE AWS PROVIDERS"}
        · ${result.runs} runs · ${result.errors} errors</strong>
      <button class="button secondary" id="export-eval">Download results ↓</button>
    </div>
    <div class="eval-stats">
      <div class="eval-stat">
        <small>Outcome + location accuracy</small>
        <strong>${(result.accuracy * 100).toFixed(0)}%</strong>
      </div>
      <div class="eval-stat">
        <small>Median response</small>
        <strong>${value(result.median_response_ms, " ms")}</strong>
      </div>
      <div class="eval-stat">
        <small>95th percentile</small>
        <strong>${value(result.p95_response_ms, " ms")}</strong>
      </div>
      <div class="eval-stat">
        <small>Mean evidence tools</small>
        <strong>${value(result.mean_evidence_tool_calls)}</strong>
      </div>
    </div>
    <div class="eval-table-wrap">
      <table>
        <thead><tr><th>CASE</th><th>EXPECTED</th><th>RESULT</th><th>RESPONSE</th><th>TOOLS</th><th>CHECK</th></tr></thead>
        <tbody>${rows}</tbody>
      </table>
    </div>`;
  $("#export-eval").onclick = () =>
    download(`parcel-detective-${result.mode}-evaluation.json`, result);
}

async function runEvaluation() {
  if (busy) return;
  setBusy(true, "Evaluating the 20 fictional cases…");
  notice();
  $("#run-evaluation").textContent = "Running 20 cases…";
  try {
    let job = await api("/api/evaluate", {});
    let delay = 300;
    while (job.status === "running") {
      job = await api("/api/evaluation");
      if (job.status === "running") {
        await new Promise((resolve) => setTimeout(resolve, delay));
        delay = Math.min(delay * 2, 3000);
      }
    }
    if (job.status !== "complete") {
      throw new Error(
        job.error || "No active evaluation was found. Please start a new run.",
      );
    }
    renderEvaluation(job.result);
  } catch (e) {
    notice(e.message);
  } finally {
    setBusy(false);
    $("#run-evaluation").textContent = "Run 20 cases ↗";
  }
}
document
  .querySelectorAll("[data-view]")
  .forEach((b) => (b.onclick = () => showView(b.dataset.view)));
document
  .querySelectorAll("[data-tab]")
  .forEach((b) => (b.onclick = () => showTab(b.dataset.tab)));
$("#case-list").onclick = (e) => {
  const button = e.target.closest("[data-case]");
  if (button) selectCase(button.dataset.case);
};
$("#search").oninput = renderQueue;
$("#run").onclick = run;
$("#rerun").onclick = run;
$("#run-evaluation").onclick = runEvaluation;
$("#source-select").onchange = (e) => {
  try {
    saveEditor();
    currentSource = e.target.value;
    loadEditor();
    $("#edit-error").textContent = "";
  } catch (error) {
    e.target.value = currentSource;
    $("#edit-error").textContent = error.message;
  }
};
$("#remove-record").onclick = () => {
  try {
    const records = JSON.parse($("#clue-editor").value);
    if (!Array.isArray(records)) throw new Error("Use a JSON array.");
    records.pop();
    $("#clue-editor").value = JSON.stringify(records, null, 2);
    saveEditor();
  } catch (e) {
    $("#edit-error").textContent = e.message;
  }
};
$("#reset-clues").onclick = () => {
  modified = {};
  loadEditor();
  $("#edit-error").textContent = "";
  notice("Original clues restored. Run again to update the finding.");
};
$("#result").onclick = (e) => {
  const button = e.target.closest("[data-record]");
  if (button) {
    showTab("timeline");
    document.getElementById(`record-${button.dataset.record}`)?.scrollIntoView({
      behavior: "smooth",
      block: "center",
    });
  }
};
async function init() {
  try {
    const data = await api("/api/cases");
    cases = data.cases;
    const mode = data.mode;
    $("#mode").textContent = mode === "aws" ? "AWS mode" : "Local demo";
    $("#mode-stat").textContent = mode === "aws" ? "Live AWS" : "Demo";
    $("#mode-help").textContent =
      mode === "aws"
        ? "Decider + Bedrock · verify with a run"
        : "Rules and templates · no AI calls";
    renderQueue();
    await selectCase(cases[0].id);
  } catch (e) {
    notice(`Cannot reach the server. ${e.message}`);
  }
}
init();
