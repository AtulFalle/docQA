import { type Provider } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import createClient, { type Client, type Middleware } from 'openapi-fetch';
import { type AiApi } from '@docqa/contracts';
import { REQUEST_ID_HEADER, currentRequestContext } from '../common/request-context';
import { type Env } from '../config/env';

/** Typed client for the internal ai-api, generated from its OpenAPI document. */
export type AiServiceClient = Client<AiApi.paths>;

export const AI_SERVICE_CLIENT = Symbol('AI_SERVICE_CLIENT');

export const aiServiceClientProvider: Provider<AiServiceClient> = {
    provide: AI_SERVICE_CLIENT,
    inject: [ConfigService],
    useFactory: (config: ConfigService<Env, true>): AiServiceClient => {
        const client = createClient<AiApi.paths>({
            baseUrl: config.get('AI_SERVICE_URL', { infer: true }),
        });
        client.use(forwardRequestId);
        return client;
    },
};

/**
 * Sends the current request id to ai-api so both services log the same id. Trace context
 * (traceparent) is added by the OpenTelemetry fetch instrumentation.
 */
export const forwardRequestId: Middleware = {
    onRequest({ request }) {
        const requestId = currentRequestContext()?.requestId;
        if (requestId && !request.headers.has(REQUEST_ID_HEADER)) {
            request.headers.set(REQUEST_ID_HEADER, requestId);
        }
        return request;
    },
};
