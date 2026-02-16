#!/usr/bin/env node
// Quick analysis of a single promptfoo result file
// Usage: node scripts/analyze-run.mjs results/<file>.json

import fs from 'fs';

const file = process.argv[2];
if (!file) {
  console.error('Usage: node scripts/analyze-run.mjs <results-file>');
  process.exit(1);
}

const data = JSON.parse(fs.readFileSync(file, 'utf8'));
const stats = data.results.stats;
const total = stats.successes + stats.failures;

console.log(`=== ${file} ===`);
console.log(`Total: ${total} | Pass: ${stats.successes} | Fail: ${stats.failures} | Errors: ${stats.tokenUsage?.numRequests - total || 0}`);
console.log('');

const byProvider = {};
for (const r of data.results.results) {
  const label = r.provider?.label || r.provider?.id || 'unknown';
  if (!(label in byProvider)) byProvider[label] = [];

  const pyScore = r.gradingResult?.componentResults?.find(c => c.assertion?.type === 'python');
  const llmScore = r.gradingResult?.componentResults?.find(c => c.assertion?.type === 'llm-rubric');

  byProvider[label].push({
    pass: r.success,
    pyScore: pyScore?.score?.toFixed(3) || 'N/A',
    pyPass: pyScore?.pass ? 'Y' : 'N',
    llmPass: llmScore?.pass ? 'Y' : 'N',
    llmScore: llmScore?.score?.toFixed(2) || 'N/A',
    pyReason: pyScore?.reason?.substring(0, 120) || '',
  });
}

// Sort by average python score descending
const sorted = Object.entries(byProvider).sort((a, b) => {
  const avgA = a[1].reduce((s, r) => s + parseFloat(r.pyScore || 0), 0) / a[1].length;
  const avgB = b[1].reduce((s, r) => s + parseFloat(r.pyScore || 0), 0) / b[1].length;
  return avgB - avgA;
});

for (const [provider, results] of sorted) {
  if (results.length === 1) {
    const r = results[0];
    console.log(`${provider.padEnd(25)} Pass:${r.pass ? 'Y' : 'N'}  Py:${r.pyScore}(${r.pyPass})  LLM:${r.llmScore}(${r.llmPass})`);
  } else {
    const pyScores = results.map(r => r.pyScore);
    const avgPy = (results.reduce((s, r) => s + parseFloat(r.pyScore || 0), 0) / results.length).toFixed(3);
    const passCount = results.filter(r => r.pass).length;
    console.log(`${provider.padEnd(25)} Pass:${passCount}/${results.length}  AvgPy:${avgPy}  Scores:[${pyScores.join(', ')}]`);
  }
}
