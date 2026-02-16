import { readFileSync } from "fs";
const data = JSON.parse(readFileSync("results/character-extraction-run1.json", "utf8"));
const r = data.results.results[0];
for (const cr of r.gradingResult?.componentResults || []) {
  if (cr.assertion?.type === "llm-rubric") {
    console.log("Rubric provider:", cr.assertion?.provider);
    console.log("Token usage:", JSON.stringify(cr.tokensUsed || cr.tokenUsage, null, 2));
  }
}
// Check top-level config for defaultTest grader
console.log("\nConfig defaultTest:", JSON.stringify(data.config?.defaultTest, null, 2));
console.log("Config grader provider:", data.config?.provider);
