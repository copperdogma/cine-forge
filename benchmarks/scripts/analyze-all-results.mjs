import fs from 'fs';

function analyzeResults(file, entityVar) {
  const data = JSON.parse(fs.readFileSync(file));
  const results = data.results.results;

  const models = {};
  for (const r of results) {
    const model = r.provider?.label || r.provider?.id || 'unknown';
    const test = r.vars?.[entityVar] || 'unknown';
    if (!(model in models)) models[model] = {};

    // Check if there's a provider-level error (API failure)
    if (r.error && !r.response?.output) {
      models[model][test] = { score: null, llm: null, status: 'API_ERROR' };
      continue;
    }

    const gr = r.gradingResult;
    if (!gr) {
      models[model][test] = { score: null, llm: null, status: 'NO_GRADE' };
      continue;
    }

    const pyResult = gr.componentResults?.find(c => c.assertion?.type === 'python');
    const llmResult = gr.componentResults?.find(c => c.assertion?.type === 'llm-rubric');

    models[model][test] = {
      score: pyResult?.score ?? null,
      llm: llmResult?.pass ?? null,
      pass: gr.pass,
      status: gr.pass ? 'PASS' : 'FAIL'
    };
  }

  return models;
}

function printTable(title, models, tests) {
  console.log(`\n=== ${title} ===`);
  const colWidth = Math.max(14, ...tests.map(t => t.length + 2));
  const header = 'Model'.padEnd(25) + tests.map(t => t.padEnd(colWidth)).join('') + 'AVG';
  console.log(header);
  console.log('-'.repeat(header.length + 6));

  const sortedModels = Object.entries(models).sort((a, b) => {
    const avgA = Object.values(a[1]).reduce((s, v) => s + (v.score || 0), 0) / tests.length;
    const avgB = Object.values(b[1]).reduce((s, v) => s + (v.score || 0), 0) / tests.length;
    return avgB - avgA;
  });

  for (const [model, data] of sortedModels) {
    let totalScore = 0;
    let count = 0;
    const cols = tests.map(t => {
      const d = data[t];
      if (!d || d.status === 'API_ERROR') return 'API_ERR'.padEnd(colWidth);
      const scoreStr = d.score !== null ? d.score.toFixed(3) : '-.---';
      const llmStr = d.llm === true ? 'Y' : d.llm === false ? 'N' : '?';
      const passStr = d.pass ? '+' : '-';
      if (d.score !== null) { totalScore += d.score; count++; }
      return `${passStr}${scoreStr}/${llmStr}`.padEnd(colWidth);
    });
    const avg = count > 0 ? (totalScore / count).toFixed(3) : 'N/A';
    console.log(model.padEnd(25) + cols.join('') + avg);
  }
}

// Check which result files exist
const resultFiles = {
  character: 'results/character-extraction-run2.json',
  location: 'results/location-extraction-run2.json',
  prop: 'results/prop-extraction-run2.json',
};

// Fallback to run1 if run2 doesn't exist
for (const [key, path] of Object.entries(resultFiles)) {
  if (!fs.existsSync(path)) {
    resultFiles[key] = path.replace('run2', 'run1');
  }
}

if (fs.existsSync(resultFiles.character)) {
  const charModels = analyzeResults(resultFiles.character, 'character_name');
  printTable('CHARACTER EXTRACTION', charModels, ['THE MARINER', 'ROSE', 'DAD']);
}

if (fs.existsSync(resultFiles.location)) {
  const locModels = analyzeResults(resultFiles.location, 'location_name');
  printTable('LOCATION EXTRACTION', locModels, ['RUDDY & GREENE BUILDING', '15TH FLOOR', 'COASTLINE']);
}

if (fs.existsSync(resultFiles.prop)) {
  const propModels = analyzeResults(resultFiles.prop, 'prop_name');
  printTable('PROP EXTRACTION', propModels, ['OAR', 'PURSE', 'FLARE GUN']);
}
