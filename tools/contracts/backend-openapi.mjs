// Completes the backend OpenAPI document exported by `main.js --export-openapi=<raw>`.
// Controllers point responses at `#/components/schemas/<Name>`; this script generates those
// schemas from the @docqa/contracts TypeScript models, so the models stay the source of truth.
//
// Usage: node tools/contracts/backend-openapi.mjs <raw.json> <out.json>
import { readFileSync, writeFileSync } from 'node:fs';
import { createGenerator } from 'ts-json-schema-generator';

const CONTRACTS = 'libs/shared/contracts/src/index.ts';
const TSCONFIG = 'libs/shared/contracts/tsconfig.lib.json';
const REF_PREFIX = '#/components/schemas/';

const [rawPath, outPath] = process.argv.slice(2);
if (!rawPath || !outPath) {
    console.error('Usage: backend-openapi.mjs <raw.json> <out.json>');
    process.exit(2);
}

const doc = JSON.parse(readFileSync(rawPath, 'utf8'));

/** Every `$ref` name used anywhere in `node`. */
function collectRefs(node, found = new Set()) {
    if (Array.isArray(node)) {
        node.forEach((item) => collectRefs(item, found));
    } else if (node && typeof node === 'object') {
        for (const [key, value] of Object.entries(node)) {
            if (key === '$ref' && typeof value === 'string' && value.startsWith(REF_PREFIX)) {
                found.add(value.slice(REF_PREFIX.length));
            } else {
                collectRefs(value, found);
            }
        }
    }
    return found;
}

const generator = createGenerator({
    path: CONTRACTS,
    tsconfig: TSCONFIG,
    type: '*',
    expose: 'export',
    topRef: false,
    jsDoc: 'extended',
    skipTypeCheck: true,
});

const schemas = {};
const pending = [...collectRefs(doc)];
while (pending.length > 0) {
    const name = pending.pop();
    if (schemas[name]) continue;
    // With topRef off, the root is the model itself and `definitions` holds what it references.
    const { definitions: nested = {}, $schema: _dialect, ...root } = generator.createSchema(name);
    const definitions = { ...nested, [name]: root };
    const text = JSON.stringify(definitions).replaceAll('"#/definitions/', `"${REF_PREFIX}`);
    for (const [defName, schema] of Object.entries(JSON.parse(text))) {
        schemas[defName] = schema;
        pending.push(...collectRefs(schema));
    }
    if (!schemas[name]) {
        console.error(`Model "${name}" is not exported by @docqa/contracts.`);
        process.exit(1);
    }
}

doc.openapi = '3.1.0';
doc.components = {
    ...doc.components,
    schemas: Object.fromEntries(Object.entries(schemas).sort(([a], [b]) => a.localeCompare(b))),
};
writeFileSync(outPath, `${JSON.stringify(doc, null, 2)}\n`, 'utf8');
