import { Controller, Get } from '@nestjs/common';
import {
    HealthCheck,
    HealthCheckService,
    type HealthIndicatorResult,
    PrismaHealthIndicator,
} from '@nestjs/terminus';
import {
    type DependencyChecks,
    type LivenessResponse,
    type ReadinessResponse,
} from '@docqa/contracts';
import {
    ApiOkResponse,
    ApiOperation,
    ApiServiceUnavailableResponse,
    ApiTags,
} from '@nestjs/swagger';
import { contractRef } from '../openapi/openapi';
import { PrismaService } from '../prisma/prisma.service';
import { AiServiceHealthIndicator } from './ai-service.health';

@ApiTags('health')
@Controller({ path: 'health', version: '1' })
export class HealthController {
    constructor(
        private readonly health: HealthCheckService,
        private readonly prismaIndicator: PrismaHealthIndicator,
        private readonly aiService: AiServiceHealthIndicator,
        private readonly prisma: PrismaService,
    ) {}

    @Get()
    @ApiOperation({ summary: 'Liveness probe' })
    @ApiOkResponse({ schema: contractRef('LivenessResponse') })
    liveness(): LivenessResponse {
        return { status: 'ok' };
    }

    @Get('ready')
    @HealthCheck({ swaggerDocumentation: false })
    @ApiOperation({ summary: 'Readiness of the backend and its dependencies' })
    @ApiOkResponse({ schema: contractRef('ReadinessResponse') })
    @ApiServiceUnavailableResponse({
        description: 'A dependency is down',
        schema: contractRef('ReadinessResponse'),
    })
    async readiness(): Promise<ReadinessResponse> {
        const result = await this.health.check([
            () => this.prismaIndicator.pingCheck('database', this.prisma),
            () => this.aiService.isHealthy('aiService'),
        ]);
        return {
            status: result.status,
            info: toChecks(result.info),
            error: toChecks(result.error),
        };
    }
}

function toChecks(checks: Partial<HealthIndicatorResult> | undefined): DependencyChecks {
    return Object.fromEntries(
        Object.entries(checks ?? {}).filter(
            (entry): entry is [string, DependencyChecks[string]] => entry[1] !== undefined,
        ),
    );
}
