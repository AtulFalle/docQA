import { validateEnv } from './env';

describe('validateEnv', () => {
    it('applies defaults for optional values', () => {
        const env = validateEnv({ DATABASE_URL: 'postgresql://u:p@localhost:5432/db' });
        expect(env).toMatchObject({
            NODE_ENV: 'development',
            PORT: 3000,
            AI_SERVICE_URL: 'http://localhost:8001',
            LOG_LEVEL: 'info',
            SERVICE_NAME: 'docqa-backend',
            APP_VERSION: '0.1.0',
            OTEL_ENABLED: false,
        });
    });

    it('coerces PORT and parses OTEL_ENABLED', () => {
        const env = validateEnv({
            DATABASE_URL: 'postgresql://u:p@localhost:5432/db',
            PORT: '8080',
            OTEL_ENABLED: 'true',
        });
        expect(env.PORT).toBe(8080);
        expect(env.OTEL_ENABLED).toBe(true);
    });

    it('throws listing the invalid DATABASE_URL key', () => {
        expect(() => validateEnv({ DATABASE_URL: 'not a url' })).toThrow(/DATABASE_URL/);
    });

    it('throws when DATABASE_URL is missing', () => {
        expect(() => validateEnv({})).toThrow(/DATABASE_URL/);
    });
});
