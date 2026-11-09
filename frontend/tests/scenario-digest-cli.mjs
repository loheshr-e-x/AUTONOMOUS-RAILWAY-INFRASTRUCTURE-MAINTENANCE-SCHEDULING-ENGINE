import { canonicalScenarioInputDigest } from "../lib/scenario-export.ts";

let input = "";
for await (const chunk of process.stdin) input += chunk;

const { requests } = JSON.parse(input);
const digests = await Promise.all(requests.map(canonicalScenarioInputDigest));
process.stdout.write(`${JSON.stringify({ digests })}\n`);
