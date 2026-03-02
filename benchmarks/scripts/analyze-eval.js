#!/usr/bin/env node
/**
 * analyze-eval.js — Generic value analysis for any promptfoo eval result file.
 *
 * Usage:
 *   node analyze-eval.js <result-file.json> [--eval-name <name>]
 *
 * Prints quality rankings and value (score/$) rankings for all providers
 * in the result file, computing cost from token usage and published pricing.
 *
 * Pricing source: published rates as of March 2026. Verify before decisions.
 */

const path = require("path");
const fs = require("fs");

// Pricing per 1M tokens (input/output) as of March 2026
const PRICING = {
  "GPT-4.1 Nano":          { input: 0.10,  output: 0.40 },
  "GPT-4.1 Mini":          { input: 0.40,  output: 1.60 },
  "GPT-4.1":               { input: 2.00,  output: 8.00 },
  "GPT-5.2":               { input: 2.00,  output: 8.00 },
  "Claude Haiku 4.5":      { input: 0.80,  output: 4.00 },
  "Claude Sonnet 4.5":     { input: 3.00,  output: 15.00 },
  "Claude Sonnet 4.6":     { input: 3.00,  output: 15.00 },
  "Claude Opus 4.6":       { input: 15.00, output: 75.00 },
  "Gemini 2.5 Flash Lite": { input: 0.075, output: 0.30 },
  "Gemini 2.5 Flash":      { input: 0.15,  output: 0.60 },
  "Gemini 2.5 Pro":        { input: 1.25,  output: 10.00 },
  "Gemini 3 Flash":        { input: 0.15,  output: 0.60 },
  "Gemini 3 Pro":          { input: 1.25,  output: 10.00 },
};

function main() {
  const args = process.argv.slice(2);
  if (args.length === 0) {
    console.error("Usage: node analyze-eval.js <result-file.json> [--eval-name <name>]");
    process.exit(1);
  }

  const filePath = path.resolve(args[0]);
  let evalName = path.basename(filePath, ".json");
  const nameIdx = args.indexOf("--eval-name");
  if (nameIdx !== -1 && args[nameIdx + 1]) {
    evalName = args[nameIdx + 1];
  }

  if (!fs.existsSync(filePath)) {
    console.error(`File not found: ${filePath}`);
    process.exit(1);
  }

  const data = JSON.parse(fs.readFileSync(filePath, "utf8"));
  const results = data.results.results;

  // Aggregate per provider
  const providers = {};
  for (const r of results) {
    const label = r.provider.label || r.provider.id;
    if (!providers[label]) {
      providers[label] = {
        python: [], rubric: [], pass: 0, fail: 0,
        inputTokens: 0, outputTokens: 0, calls: 0, latencyMs: 0,
      };
    }

    const p = providers[label];
    for (const g of (r.gradingResult && r.gradingResult.componentResults) || []) {
      if (!g.assertion) continue;
      if (g.assertion.type === "python") p.python.push(g.score || 0);
      else if (g.assertion.type === "llm-rubric") p.rubric.push(g.score || 0);
    }

    if (r.success) p.pass++; else p.fail++;

    const tok = (r.response && r.response.tokenUsage) ? r.response.tokenUsage : {};
    p.inputTokens += tok.prompt || tok.total || 0;
    p.outputTokens += tok.completion || 0;
    p.latencyMs += r.latencyMs || 0;
    p.calls += 1;
  }

  // Compute summary stats
  const rows = Object.entries(providers).map(([name, d]) => {
    const pyAvg = d.python.length ? avg(d.python) : null;
    const rubAvg = d.rubric.length ? avg(d.rubric) : null;

    // Combined: if both scorers exist, average them; otherwise use whichever exists
    let combined;
    if (pyAvg !== null && rubAvg !== null) combined = (pyAvg + rubAvg) / 2;
    else if (pyAvg !== null) combined = pyAvg;
    else if (rubAvg !== null) combined = rubAvg;
    else combined = 0;

    const price = PRICING[name] || null;
    const avgIn = d.calls > 0 ? Math.round(d.inputTokens / d.calls) : 0;
    const avgOut = d.calls > 0 ? Math.round(d.outputTokens / d.calls) : 0;
    const avgLatMs = d.calls > 0 ? Math.round(d.latencyMs / d.calls) : 0;

    let costPerCall = null;
    if (price && d.calls > 0) {
      costPerCall = (d.inputTokens / 1e6 * price.input + d.outputTokens / 1e6 * price.output) / d.calls;
    }

    const value = (costPerCall && costPerCall > 0) ? combined / costPerCall : null;

    return { name, pyAvg, rubAvg, combined, pass: d.pass, fail: d.fail, avgIn, avgOut, avgLatMs, costPerCall, value };
  });

  // Sort by quality (combined)
  rows.sort((a, b) => b.combined - a.combined);

  console.log(`\n=== ${evalName} — Quality Rankings ===\n`);
  console.log("Model                    | Python | Rubric | Combined | Latency  | Cost/call | Value     | P/F");
  console.log("-------------------------|--------|--------|----------|----------|-----------|-----------|----");
  for (const s of rows) {
    const py = s.pyAvg !== null ? s.pyAvg.toFixed(3).padStart(6) : "  n/a ";
    const rub = s.rubAvg !== null ? s.rubAvg.toFixed(3).padStart(6) : "  n/a ";
    const cost = s.costPerCall !== null ? ("$" + s.costPerCall.toFixed(5)).padStart(9) : "  unknown";
    const val = s.value !== null ? s.value.toFixed(0).padStart(9) : "    n/a  ";
    const lat = (s.avgLatMs / 1000).toFixed(1).padStart(6) + "s";
    console.log(
      s.name.padEnd(25) + "| " +
      py + " | " + rub + " | " +
      s.combined.toFixed(3).padStart(8) + " | " +
      lat + "  | " +
      cost + " | " +
      val + " | " +
      s.pass + "/" + (s.pass + s.fail)
    );
  }

  // Sort by value
  const byValue = rows.filter(r => r.value !== null).sort((a, b) => b.value - a.value);
  if (byValue.length > 0) {
    console.log(`\n=== ${evalName} — Value Rankings (score per dollar) ===\n`);
    console.log("Model                    | Combined | Cost/call | Latency  | Value (score/$)");
    console.log("-------------------------|----------|-----------|----------|-----------------");
    for (const s of byValue) {
      const lat = (s.avgLatMs / 1000).toFixed(1).padStart(6) + "s";
      console.log(
        s.name.padEnd(25) + "| " +
        s.combined.toFixed(3).padStart(8) + " | " +
        ("$" + s.costPerCall.toFixed(5)).padStart(9) + " | " +
        lat + "  | " +
        s.value.toFixed(0).padStart(15)
      );
    }
  }

  // Failures
  const failed = results.filter(r => !r.success);
  if (failed.length > 0) {
    console.log("\n--- Failed test details ---");
    for (const r of failed) {
      const label = r.provider.label || r.provider.id;
      const testKey = r.vars ? (r.vars.character_name || r.vars.scene_key || Object.values(r.vars)[0] || "?") : "?";
      console.log(`${label} on ${typeof testKey === 'string' ? testKey.substring(0, 60) : testKey}:`);
      for (const g of (r.gradingResult && r.gradingResult.componentResults) || []) {
        if (g.pass) continue;
        const aType = g.assertion ? g.assertion.type : "?";
        const score = g.score ? g.score.toFixed(4) : "0";
        const reason = (g.reason || "").substring(0, 120);
        console.log(`  ${aType}: pass=${g.pass} score=${score} reason=${reason}`);
      }
    }
  }
}

function avg(arr) {
  return arr.reduce((a, b) => a + b, 0) / arr.length;
}

main();
