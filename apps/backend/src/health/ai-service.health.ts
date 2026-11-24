import { Injectable } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { type HealthIndicatorResult, HealthIndicatorService } from '@nestjs/terminus';
import { type Env } from '../config/env';

@Injectable()
export class AiServiceHealthIndicator {
    constructor(
        private readonly healthIndicatorService: HealthIndicatorService,
        private readonly config: ConfigService<Env, true>,
    ) {}

    async isHealthy(key: string): Promise<HealthIndicatorResult> {
        const indicator = this.healthIndicatorService.check(key);
        const baseUrl = this.config.get('AI_SERVICE_URL', { infer: true });
        try {
            const res = await fetch(`${baseUrl}/healthz`, { signal: AbortSignal.timeout(2000) });
            if (!res.ok) {
                return indicator.down({ message: `AI service responded with HTTP ${res.status}` });
            }
            return indicator.up();
        } catch (err) {
            const message = err instanceof Error ? err.message : 'AI service unreachable';
            return indicator.down({ message });
        }
    }
}
