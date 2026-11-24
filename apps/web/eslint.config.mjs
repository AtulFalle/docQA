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
        },
    },
];
