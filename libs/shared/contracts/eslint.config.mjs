import baseConfig from '../../../eslint.config.mjs';

const PURE_MODELS = 'Shared models are data only: types, interfaces and `as const` value lists.';

export default [
    ...baseConfig,
    {
        files: ['**/*.ts'],
        ignores: ['**/*.spec.ts'],
        rules: {
            // Keep the lib free of runtime code so web and backend can import it without
            // pulling in server code, frameworks or side effects.
            'no-restricted-syntax': [
                'error',
                { selector: 'FunctionDeclaration', message: PURE_MODELS },
                { selector: 'ArrowFunctionExpression', message: PURE_MODELS },
                { selector: 'FunctionExpression', message: PURE_MODELS },
                { selector: 'ClassDeclaration', message: PURE_MODELS },
                { selector: 'TSEnumDeclaration', message: 'Use an `as const` array + union type.' },
            ],
            'no-restricted-imports': [
                'error',
                {
                    patterns: [
                        {
                            regex: '^(?!\\.)',
                            message: 'Models import only other model files (relative paths).',
                        },
                    ],
                },
            ],
        },
    },
];
