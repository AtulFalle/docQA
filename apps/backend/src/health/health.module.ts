import { Module } from '@nestjs/common';
import { TerminusModule } from '@nestjs/terminus';
import { AiServiceModule } from '../ai-service/ai-service.module';
import { AiServiceHealthIndicator } from './ai-service.health';
import { HealthController } from './health.controller';

@Module({
    imports: [TerminusModule, AiServiceModule],
    controllers: [HealthController],
    providers: [AiServiceHealthIndicator],
})
export class HealthModule {}
