import { type Provider } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import createClient, { type Client } from 'openapi-fetch';
import { type AiApi } from '@docqa/contracts';
import { type Env } from '../config/env';

/** Typed client for the internal ai-api, generated from its OpenAPI document. */
export type AiServiceClient = Client<AiApi.paths>;

export const AI_SERVICE_CLIENT = Symbol('AI_SERVICE_CLIENT');

export const aiServiceClientProvider: Provider<AiServiceClient> = {
    provide: AI_SERVICE_CLIENT,
    inject: [ConfigService],
    useFactory: (config: ConfigService<Env, true>): AiServiceClient =>
        createClient<AiApi.paths>({ baseUrl: config.get('AI_SERVICE_URL', { infer: true }) }),
};
