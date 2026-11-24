import { Module } from '@nestjs/common';
import { TerminusModule } from '@nestjs/terminus';
import { AiServiceHealthIndicator } from './ai-service.health';
import { HealthController } from './health.controller';

@Module({
    imports: [TerminusModule],
    controllers: [HealthController],
    providers: [AiServiceHealthIndicator],
})
export class HealthModule {}
