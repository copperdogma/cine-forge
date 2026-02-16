import { readFileSync } from 'fs';

const data = JSON.parse(readFileSync('results/character-extraction-run1.json', 'utf8'));
const results = data.results.results;

const byChar = {};
for (const r of results) {
  const provider = r.provider?.label || r.provider?.id || 'unknown';
  const charName = r.vars?.character_name || 'unknown';
  if (!byChar[charName]) byChar[charName] = [];

  const gradingResults = r.gradingResult?.componentResults || [];
  const pythonResult = gradingResults.find(g => g.assertion?.type === 'python') || {};
  const llmResult = gradingResults.find(g => g.assertion?.type === 'llm-rubric') || {};

  byChar[charName].push({
    provider,
    pass: r.success,
    pythonScore: pythonResult.score?.toFixed(4) || 'N/A',
    llmScore: llmResult.score?.toFixed(2) || 'N/A',
    llmPass: llmResult.pass,
    reason: (pythonResult.reason || '').substring(0, 160),
    latency: r.latencyMs,
  });
}

for (const [char, entries] of Object.entries(byChar)) {
  console.log(`\n=== ${char} ===`);
  entries.sort((a, b) => parseFloat(b.pythonScore) - parseFloat(a.pythonScore));
  for (const e of entries) {
    const pass = e.pass ? 'PASS' : 'FAIL';
    console.log(
      `${e.provider.padEnd(22)} ${pass.padEnd(6)} py=${e.pythonScore.padEnd(8)} llm=${e.llmScore.padEnd(6)} ${e.latency}ms`
    );
    console.log(`  ${e.reason}`);
  }
}
