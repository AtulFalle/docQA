import { Module } from '@nestjs/common';
import { AI_SERVICE_CLIENT, aiServiceClientProvider } from './ai-service.client';

/** Provides the typed ai-api client to any module that imports it. */
@Module({
    providers: [aiServiceClientProvider],
    exports: [AI_SERVICE_CLIENT],
})
export class AiServiceModule {}
