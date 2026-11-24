// ts-jest, plus a rewrite of `import.meta.{url,dirname,filename}` to CommonJS equivalents.
// NestJS 12 ships ESM-only and uses import.meta, which is a syntax error once Jest
// runs the transpiled CJS output.
const { TsJestTransformer } = require('ts-jest');

const CJS_EQUIVALENTS = {
    url: "require('node:url').pathToFileURL(__filename).href",
    dirname: '__dirname',
    filename: '__filename',
};
const IMPORT_META = /\bimport\.meta\.(url|dirname|filename)\b/g;
const shim = (source) => source.replace(IMPORT_META, (_, key) => CJS_EQUIVALENTS[key]);

class Transformer extends TsJestTransformer {
    process(source, path, options) {
        return super.process(shim(source), path, options);
    }

    processAsync(source, path, options) {
        return super.processAsync(shim(source), path, options);
    }

    getCacheKey(source, path, options) {
        return super.getCacheKey(shim(source), path, options);
    }
}

module.exports = { createTransformer: (config) => new Transformer(config) };
