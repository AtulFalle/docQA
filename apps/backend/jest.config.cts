module.exports = {
    displayName: 'backend',
    preset: '../../jest.preset.js',
    testEnvironment: 'node',
    transform: {
        '^.+\\.[cm]?[tj]s$': [
            '<rootDir>/jest.transformer.cjs',
            { tsconfig: '<rootDir>/tsconfig.spec.json' },
        ],
    },
    // NestJS 12 and friends ship ESM-only; let ts-jest transpile them to CJS.
    transformIgnorePatterns: ['/node_modules/(?!(\\.pnpm/)?(@nestjs|nestjs-pino))'],
    moduleFileExtensions: ['ts', 'js', 'html'],
    coverageDirectory: '../../coverage/apps/backend',
};
