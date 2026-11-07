import fs from 'node:fs';
import YAML from 'yaml';
const contract = YAML.parse(fs.readFileSync(new URL('../../contracts/openapi.yaml', import.meta.url), 'utf8'));
const output = new URL('../src/api/schemas.generated.json', import.meta.url);
const generated = JSON.stringify({components: contract.components});
if (process.argv.includes('--check')) {
  if (fs.readFileSync(output, 'utf8') !== generated) throw new Error('Generated response schemas are stale');
} else fs.writeFileSync(output, generated);
