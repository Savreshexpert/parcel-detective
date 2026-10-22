// Logic checks with small DOM stubs. This is not a browser layout test.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

function dashboard() {
  const elements = new Map();
  const waits = [];
  function element(selector) {
    if (!elements.has(selector)) {
      const classes = new Set();
      elements.set(selector, {
        value: "",
        textContent: "",
        innerHTML: "",
        hidden: false,
        classList: {
          remove: (name) => classes.delete(name),
          toggle: (name, active) =>
            active ? classes.add(name) : classes.delete(name),
        },
        setAttribute() {},
      });
    }
    return elements.get(selector);
  }
  const context = vm.createContext({
    document: { querySelector: element, querySelectorAll: () => [] },
    setTimeout: (callback, delay) => {
      waits.push(delay);
      callback();
    },
    clearTimeout() {},
    AbortController,
  });
  const source = fs.readFileSync(path.join(__dirname, "../web/app.js"), "utf8");
  vm.runInContext(source.replace(/\ninit\(\);\s*$/, "\n"), context);
  return { context, element, waits };
}

const complete = {
  status: "complete",
  result: {
    mode: "demo",
    runs: 20,
    errors: 0,
    accuracy: 1,
    median_response_ms: 0.1,
    p95_response_ms: 0.2,
    mean_evidence_tool_calls: 3,
    rows: [],
  },
};

test("busy state keeps the existing case cards", () => {
  const { context, element } = dashboard();
  const queue = element("#case-list");
  queue.innerHTML = "existing cards";
  context.setBusy(true);
  assert.equal(queue.innerHTML, "existing cards");
  assert.equal(queue.inert, true);
  context.setBusy(false);
  assert.equal(queue.inert, false);
});

test("completed evaluation appears without a fixed polling delay", async () => {
  const { context, waits, element } = dashboard();
  const responses = [{ status: "running" }, complete];
  context.api = async () => responses.shift();
  await context.runEvaluation();
  assert.deepEqual(waits, []);
  assert.match(element("#evaluation-output").innerHTML, /100%/);
  assert.equal(element("#run-evaluation").disabled, false);
});

test("running evaluations back off and an idle job stops polling", async () => {
  const { context, waits, element } = dashboard();
  const responses = ["running", "running", "running", "idle"];
  context.api = async () => ({ status: responses.shift() });
  await context.runEvaluation();
  assert.deepEqual(waits, [300, 600]);
  assert.match(element("#notice").textContent, /No active evaluation/);
  assert.equal(element("#run-evaluation").disabled, false);
});

test("case loading prevents overlapping selection and investigation", async () => {
  const { context, element } = dashboard();
  const calls = [];
  let resolveCase;
  context.api = (url) => {
    calls.push(url);
    return new Promise((resolve) => {
      resolveCase = resolve;
    });
  };
  const loading = context.selectCase("C01");
  await context.selectCase("C02");
  await context.run();
  assert.deepEqual(calls, ["/api/cases/C01"]);
  resolveCase({
    id: "C01",
    parcel_id: "P104",
    report: "Missing",
    records: { scan_history: [], dispatch_records: [], handover_notes: [] },
  });
  await loading;
  assert.equal(element("#case-id").textContent, "CASE C01");
  assert.equal(element("#run").disabled, false);
});
