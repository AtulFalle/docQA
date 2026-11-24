import nx from '@nx/eslint-plugin';
import angular from 'angular-eslint';
import baseConfig from '../../eslint.config.mjs';

export default [
    ...nx.configs['flat/angular'],
    ...nx.configs['flat/angular-template'],
    ...baseConfig,
    {
        files: ['**/*.ts'],
        rules: {
            '@angular-eslint/directive-selector': [
                'error',
                {
                    type: 'attribute',
                    prefix: 'dq',
                    style: 'camelCase',
                },
            ],
            '@angular-eslint/component-selector': [
                'error',
                {
                    type: 'element',
                    prefix: 'dq',
                    style: 'kebab-case',
                },
            ],
            '@angular-eslint/prefer-on-push-component-change-detection': 'error',
            '@angular-eslint/prefer-standalone': 'error',
            '@angular-eslint/no-output-on-prefix': 'error',
            // Modern Angular: signal inputs/outputs/queries and inject() instead of decorators/ctor DI.
            '@angular-eslint/prefer-signals': 'error',
            '@angular-eslint/prefer-signal-model': 'error',
            '@angular-eslint/prefer-inject': 'error',
            '@angular-eslint/prefer-output-readonly': 'error',
            '@angular-eslint/no-input-rename': 'error',
            '@angular-eslint/no-output-rename': 'error',
            '@angular-eslint/use-lifecycle-interface': 'error',
            '@angular-eslint/no-empty-lifecycle-method': 'error',
        },
    },
    ...angular.configs.templateAccessibility.map((config) => ({
        ...config,
        files: ['**/*.html'],
    })),
    {
        files: ['**/*.html'],
        rules: {
            '@angular-eslint/template/prefer-control-flow': 'error',
            '@angular-eslint/template/prefer-self-closing-tags': 'error',
            '@angular-eslint/template/prefer-ngsrc': 'error',
            '@angular-eslint/template/no-any': 'error',
            '@angular-eslint/template/conditional-complexity': ['error', { maxComplexity: 4 }],
            'max-lines': ['error', { max: 400, skipBlankLines: true }],
        },
    },
];
