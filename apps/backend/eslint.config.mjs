import baseConfig from '../../eslint.config.mjs';

export default [
    ...baseConfig,
    {
        // NestJS DI reads constructor param types from decorator metadata, so those
        // imports must stay value imports; tell typescript-eslint so it doesn't flag them.
        files: ['**/*.ts'],
        languageOptions: {
            parserOptions: { emitDecoratorMetadata: true, experimentalDecorators: true },
        },
    },
];
