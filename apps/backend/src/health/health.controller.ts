import { Controller, Get } from '@nestjs/common';
import { HealthCheck, HealthCheckService, PrismaHealthIndicator } from '@nestjs/terminus';
import { type LivenessResponse, type ReadinessResponse } from '@docqa/contracts';
import { PrismaService } from '../prisma/prisma.service';
import { AiServiceHealthIndicator } from './ai-service.health';

@Controller({ path: 'health', version: '1' })
export class HealthController {
    constructor(
        private readonly health: HealthCheckService,
        private readonly prismaIndicator: PrismaHealthIndicator,
        private readonly aiService: AiServiceHealthIndicator,
        private readonly prisma: PrismaService,
    ) {}

    @Get()
    liveness(): LivenessResponse {
        return { status: 'ok' };
    }

    @Get('ready')
    @HealthCheck()
    async readiness(): Promise<ReadinessResponse> {
        const result = await this.health.check([
            () => this.prismaIndicator.pingCheck('database', this.prisma),
            () => this.aiService.isHealthy('aiService'),
        ]);
        return { status: result.status, info: result.info ?? {}, error: result.error ?? {} };
    }
}
