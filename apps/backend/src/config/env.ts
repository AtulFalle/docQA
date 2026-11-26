import { z } from 'zod';

export const envSchema = z.object({
    NODE_ENV: z.enum(['development', 'test', 'production']).default('development'),
    PORT: z.coerce.number().int().min(1).max(65535).default(3000),
    DATABASE_URL: z.url(),
    AI_SERVICE_URL: z.url().default('http://localhost:8001'),
    LOG_LEVEL: z
        .enum(['fatal', 'error', 'warn', 'info', 'debug', 'trace', 'silent'])
        .default('info'),
    SERVICE_NAME: z.string().min(1).default('docqa-backend'),
    /** Deployment environment, same values as DOCQA_ENV in the Python services. */
    APP_ENV: z.enum(['local', 'dev', 'staging', 'prod']).default('local'),
    APP_VERSION: z.string().min(1).default('0.1.0'),
    OTEL_ENABLED: z.stringbool().default(false),
    OTEL_EXPORTER_OTLP_ENDPOINT: z.url().optional(),
});

export type Env = z.infer<typeof envSchema>;

/** Validates raw environment variables; throws a readable error listing every invalid key. */
export function validateEnv(raw: Record<string, unknown>): Env {
    const result = envSchema.safeParse(raw);
    if (result.success) {
        return result.data;
    }
    const lines = result.error.issues.map((issue) => {
        const key = issue.path.length > 0 ? issue.path.join('.') : '(root)';
        return `  - ${key}: ${issue.message}`;
    });
    throw new Error(`Invalid environment configuration:\n${lines.join('\n')}`);
}
