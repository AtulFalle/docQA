import { type IncomingMessage } from 'node:http';
import { trace } from '@opentelemetry/api';
import { type Params } from 'nestjs-pino';
import { type Env } from '../config/env';
import { currentRequestContext, requestIdFor } from './request-context';

/**
 * Fields on every log line, shared with the Python services:
 * service, env, request_id, trace_id, span_id, tenant_id, user_id, level (label), timestamp (ISO).
 */
export function correlationFields(): Record<string, string> {
    const fields: Record<string, string> = {};
    const span = trace.getActiveSpan()?.spanContext();
    if (span) {
        fields['trace_id'] = span.traceId;
        fields['span_id'] = span.spanId;
    }
    const ctx = currentRequestContext();
    if (ctx?.tenantId) fields['tenant_id'] = ctx.tenantId;
    if (ctx?.userId) fields['user_id'] = ctx.userId;
    return fields;
}

export type LoggerEnv = Pick<Env, 'LOG_LEVEL' | 'SERVICE_NAME' | 'APP_ENV' | 'NODE_ENV'>;

export function loggerParams(env: LoggerEnv): Params {
    return {
        pinoHttp: {
            level: env.LOG_LEVEL,
            base: { service: env.SERVICE_NAME, env: env.APP_ENV },
            timestamp: () => `,"timestamp":"${new Date().toISOString()}"`,
            formatters: { level: (label: string) => ({ level: label }) },
            mixin: correlationFields,
            genReqId: requestIdFor,
            // Bind only `request_id` to each request's logger (not the whole req object).
            quietReqLogger: true,
            customAttributeKeys: { reqId: 'request_id' },
            redact: ['req.headers.authorization', 'req.headers.cookie'],
            transport:
                env.NODE_ENV === 'development'
                    ? { target: 'pino-pretty', options: { timestampKey: 'timestamp' } }
                    : undefined,
            autoLogging: {
                // Skip only the liveness probe. Readiness calls the DB and ai-api, so it is logged.
                ignore: (req: IncomingMessage) => req.url === '/api/v1/health',
            },
        },
    };
}
