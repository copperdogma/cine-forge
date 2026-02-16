#!/usr/bin/env node
// Investigate failures in eval results
// Usage: node scripts/investigate.mjs <results-file> [provider-filter]

import fs from 'fs';

const file = process.argv[2];
const providerFilter = process.argv[3];

if (!file) {
  console.error('Usage: node scripts/investigate.mjs <results-file> [provider-filter]');
  process.exit(1);
}

const data = JSON.parse(fs.readFileSync(file, 'utf8'));

for (const r of data.results.results) {
  const label = r.provider?.label || r.provider?.id || 'unknown';

  if (providerFilter && !label.toLowerCase().includes(providerFilter.toLowerCase())) continue;

  const py = r.gradingResult?.componentResults?.find(c => c.assertion?.type === 'python');
  const llm = r.gradingResult?.componentResults?.find(c => c.assertion?.type === 'llm-rubric');

  // Show failures or filtered provider
  const isFail = !r.success;
  if (!providerFilter && !isFail) continue;

  console.log(`--- ${label} (${r.success ? 'PASS' : 'FAIL'}) ---`);
  console.log(`  Py score: ${py?.score?.toFixed(3) || 'N/A'} (${py?.pass ? 'pass' : 'fail'})`);
  console.log(`  Py reason: ${(py?.reason || '').substring(0, 250)}`);
  console.log(`  LLM score: ${llm?.score?.toFixed(2) || 'N/A'} (${llm?.pass ? 'pass' : 'fail'})`);
  console.log(`  LLM reason: ${(llm?.reason || '').substring(0, 300)}`);
  console.log(`  Output length: ${r.response?.output?.length || 0}`);
  if (py?.score === 0 || (py?.score && py.score < 0.3)) {
    console.log(`  Output tail: ${(r.response?.output || '').substring(Math.max(0, (r.response?.output?.length || 0) - 200))}`);
  }
  console.log('');
}
