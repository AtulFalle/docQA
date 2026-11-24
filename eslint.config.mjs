import nx from '@nx/eslint-plugin';
import prettier from 'eslint-config-prettier';

/**
 * Root ESLint config for all TypeScript projects (apps/web, apps/backend, libs/shared/*).
 * Rationale per rule: docs/engineering/typescript.md. Changing a rule = PR with justification.
 */
export default [
    ...nx.configs['flat/base'],
    ...nx.configs['flat/typescript'],
    ...nx.configs['flat/javascript'],
    {
        ignores: [
            '**/dist',
            '**/out-tsc',
            '**/coverage',
            '**/generated',
            '**/.angular',
            '**/vite.config.*.timestamp*',
        ],
    },
    {
        files: ['**/*.ts', '**/*.tsx', '**/*.js', '**/*.jsx'],
        rules: {
            // Architecture: who may import whom (Nx project tags).
            '@nx/enforce-module-boundaries': [
                'error',
                {
                    enforceBuildableLibDependency: true,
                    allow: ['^.*/eslint(\\.base)?\\.config\\.[cm]?[jt]s$'],
                    depConstraints: [
                        {
                            sourceTag: 'scope:web',
                            onlyDependOnLibsWithTags: ['scope:web', 'scope:shared'],
                        },
                        {
                            sourceTag: 'scope:backend',
                            onlyDependOnLibsWithTags: ['scope:backend', 'scope:shared'],
                        },
                        { sourceTag: 'scope:shared', onlyDependOnLibsWithTags: ['scope:shared'] },
                        {
                            sourceTag: 'type:contracts',
                            onlyDependOnLibsWithTags: ['type:contracts'],
                        },
                    ],
                },
            ],
        },
    },
    {
        files: ['**/*.ts', '**/*.cts', '**/*.mts'],
        rules: {
            '@typescript-eslint/no-explicit-any': 'error',
            '@typescript-eslint/no-non-null-assertion': 'error',
            '@typescript-eslint/consistent-type-imports': [
                'error',
                { fixStyle: 'inline-type-imports' },
            ],
            '@typescript-eslint/no-unused-vars': [
                'error',
                { argsIgnorePattern: '^_', varsIgnorePattern: '^_' },
            ],
            eqeqeq: ['error', 'always'],
            'no-console': 'error',
            'no-restricted-imports': [
                'error',
                {
                    paths: [
                        {
                            name: 'axios',
                            message: 'Use fetch (backend) or Angular HttpClient (web).',
                        },
                        {
                            name: 'lodash',
                            message: 'Use native JS; add a targeted util if really needed.',
                        },
                    ],
                },
            ],
            // Every function states its return type (expressions passed where a type is
            // already known, e.g. callbacks and typed arrow consts, are exempt).
            '@typescript-eslint/explicit-function-return-type': [
                'error',
                {
                    allowExpressions: true,
                    allowTypedFunctionExpressions: true,
                    allowHigherOrderFunctions: true,
                    allowDirectConstAssertionInArrowFunctions: true,
                },
            ],
            '@typescript-eslint/explicit-module-boundary-types': 'error',
            // Size: small files and small functions (docs/engineering/typescript.md#complexity-and-size).
            'max-lines': ['error', { max: 400, skipBlankLines: true, skipComments: true }],
            'max-lines-per-function': [
                'error',
                { max: 50, skipBlankLines: true, skipComments: true, IIFEs: true },
            ],
            complexity: ['error', 10],
            'max-depth': ['error', 4],
            'max-params': ['error', 6],
        },
    },
    {
        files: ['**/*.spec.ts', '**/*.test.ts', '**/*-e2e/**/*.ts'],
        rules: {
            '@typescript-eslint/no-non-null-assertion': 'off',
            '@typescript-eslint/explicit-function-return-type': 'off',
            'max-lines-per-function': 'off',
            'max-params': 'off',
        },
    },
    // Must stay last: turns off stylistic rules that Prettier owns.
    prettier,
];
