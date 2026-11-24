import { Inject, Injectable } from '@nestjs/common';
import { type HealthIndicatorResult, HealthIndicatorService } from '@nestjs/terminus';
import { AI_SERVICE_CLIENT, type AiServiceClient } from '../ai-service/ai-service.client';

const TIMEOUT_MS = 2000;

@Injectable()
export class AiServiceHealthIndicator {
    constructor(
        private readonly healthIndicatorService: HealthIndicatorService,
        @Inject(AI_SERVICE_CLIENT) private readonly client: AiServiceClient,
    ) {}

    async isHealthy(key: string): Promise<HealthIndicatorResult> {
        const indicator = this.healthIndicatorService.check(key);
        try {
            const { response } = await this.client.GET('/healthz', {
                signal: AbortSignal.timeout(TIMEOUT_MS),
            });
            if (!response.ok) {
                return indicator.down({
                    message: `AI service responded with HTTP ${response.status}`,
                });
            }
            return indicator.up();
        } catch (err) {
            const message =
                err instanceof Error || err instanceof DOMException
                    ? err.message
                    : 'AI service unreachable';
            return indicator.down({ message });
        }
    }
}
