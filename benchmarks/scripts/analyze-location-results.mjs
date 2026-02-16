import fs from 'fs';

const data = JSON.parse(fs.readFileSync('results/location-extraction-run1.json'));
const results = data.results.results;

const models = {};
for (const r of results) {
  const model = r.provider?.label || r.provider?.id || 'unknown';
  const test = r.vars?.location_name || 'unknown';
  if (!(model in models)) models[model] = {};

  if (r.error) {
    models[model][test] = 'ERROR';
  } else {
    const pythonAssert = r.gradingResult?.componentResults?.find(c => c.assertion?.type === 'python');
    const llmAssert = r.gradingResult?.componentResults?.find(c => c.assertion?.type === 'llm-rubric');
    const pyScore = pythonAssert?.score || 0;
    const llmPass = llmAssert?.pass ? 'Y' : 'N';
    models[model][test] = pyScore.toFixed(3) + '/' + llmPass;
  }
}

console.log('\n=== LOCATION EXTRACTION RESULTS ===');
console.log('Model'.padEnd(25), 'BUILDING'.padEnd(12), '15TH FLOOR'.padEnd(12), 'COASTLINE'.padEnd(12));
console.log('-'.repeat(61));
for (const [model, tests] of Object.entries(models)) {
  console.log(
    model.padEnd(25),
    (tests['RUDDY & GREENE BUILDING'] || '-').padEnd(12),
    (tests['15TH FLOOR'] || '-').padEnd(12),
    (tests['COASTLINE'] || '-').padEnd(12)
  );
}
