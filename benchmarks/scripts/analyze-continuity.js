const data = require("../results/continuity-extraction-2026-03-01.json");
const results = data.results.results;

// Pricing per 1M tokens (input/output) as of March 2026
const pricing = {
  "GPT-4.1 Nano":         { input: 0.10, output: 0.40 },
  "GPT-4.1 Mini":         { input: 0.40, output: 1.60 },
  "GPT-4.1":              { input: 2.00, output: 8.00 },
  "GPT-5.2":              { input: 2.00, output: 8.00 },
  "Claude Haiku 4.5":     { input: 0.80, output: 4.00 },
  "Claude Sonnet 4.5":    { input: 3.00, output: 15.00 },
  "Claude Sonnet 4.6":    { input: 3.00, output: 15.00 },
  "Claude Opus 4.6":      { input: 15.00, output: 75.00 },
  "Gemini 2.5 Flash Lite":{ input: 0.075, output: 0.30 },
  "Gemini 2.5 Flash":     { input: 0.15, output: 0.60 },
  "Gemini 2.5 Pro":       { input: 1.25, output: 10.00 },
  "Gemini 3 Flash":       { input: 0.15, output: 0.60 },
  "Gemini 3 Pro":         { input: 1.25, output: 10.00 },
};

const providers = {};
for (const r of results) {
  const label = r.provider.label || r.provider.id;
  if (!providers[label]) providers[label] = { python: [], rubric: [], pass: 0, fail: 0, input: 0, output: 0, calls: 0 };

  for (const g of r.gradingResult.componentResults || []) {
    if (g.assertion && g.assertion.type === "python") {
      providers[label].python.push(g.score || 0);
    } else if (g.assertion && g.assertion.type === "llm-rubric") {
      providers[label].rubric.push(g.score || 0);
    }
  }
  if (r.success) providers[label].pass++;
  else providers[label].fail++;

  const tok = r.response && r.response.tokenUsage ? r.response.tokenUsage : {};
  providers[label].input += tok.prompt || tok.total || 0;
  providers[label].output += tok.completion || 0;
  providers[label].calls += 1;
}

const sorted = Object.entries(providers).map(([name, d]) => {
  const pyAvg = d.python.length ? d.python.reduce((a,b) => a+b, 0) / d.python.length : 0;
  const rubAvg = d.rubric.length ? d.rubric.reduce((a,b) => a+b, 0) / d.rubric.length : 0;
  const combined = (pyAvg + rubAvg) / 2;
  const p = pricing[name] || { input: 0, output: 0 };
  const avgIn = d.calls > 0 ? Math.round(d.input / d.calls) : 0;
  const avgOut = d.calls > 0 ? Math.round(d.output / d.calls) : 0;
  const costPerCall = d.calls > 0 ? (d.input / 1000000 * p.input + d.output / 1000000 * p.output) / d.calls : 0;
  const value = costPerCall > 0 ? combined / costPerCall : 0;
  return { name, pyAvg, rubAvg, combined, pass: d.pass, fail: d.fail, avgIn, avgOut, costPerCall, value };
}).sort((a,b) => b.combined - a.combined);

console.log("\n=== Combined Rankings (by quality) ===\n");
console.log("Model                    | Python | Rubric | Combined | Cost/call | Value  | P/F");
console.log("-------------------------|--------|--------|----------|-----------|--------|----");
for (const s of sorted) {
  console.log(
    s.name.padEnd(25) + "| " +
    s.pyAvg.toFixed(3).padStart(6) + " | " +
    s.rubAvg.toFixed(3).padStart(6) + " | " +
    s.combined.toFixed(3).padStart(8) + " | " +
    ("$" + s.costPerCall.toFixed(5)).padStart(9) + " | " +
    s.value.toFixed(0).padStart(6) + " | " +
    s.pass + "/" + (s.pass + s.fail)
  );
}

console.log("\n=== Value Rankings (score per dollar) ===\n");
const byCost = [...sorted].sort((a,b) => b.value - a.value);
console.log("Model                    | Combined | Cost/call | Value (score/$)");
console.log("-------------------------|----------|-----------|----------------");
for (const s of byCost) {
  console.log(
    s.name.padEnd(25) + "| " +
    s.combined.toFixed(3).padStart(8) + " | " +
    ("$" + s.costPerCall.toFixed(5)).padStart(9) + " | " +
    s.value.toFixed(0).padStart(15)
  );
}

// Show the failure
console.log("\n--- Failed test details ---");
for (const r of results) {
  if (!r.success) {
    const label = r.provider.label || r.provider.id;
    const testKey = r.vars ? r.vars.scene_key : "?";
    console.log(label + " on " + testKey + ":");
    for (const g of r.gradingResult.componentResults || []) {
      const aType = g.assertion ? g.assertion.type : "?";
      const score = g.score ? g.score.toFixed(4) : "0";
      const reason = (g.reason || "").substring(0, 120);
      console.log("  " + aType + ": pass=" + g.pass + " score=" + score + " reason=" + reason);
    }
  }
}
