import './instrumentation';
import { VersioningType } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { NestFactory } from '@nestjs/core';
import { Logger } from 'nestjs-pino';
import { AppModule } from './app.module';
import { type Env } from './config/env';

async function bootstrap() {
    const app = await NestFactory.create(AppModule, { bufferLogs: true });
    const logger = app.get(Logger);
    app.useLogger(logger);
    app.setGlobalPrefix('api');
    app.enableVersioning({ type: VersioningType.URI, defaultVersion: '1' });
    app.enableShutdownHooks();

    const port = app.get<ConfigService<Env, true>>(ConfigService).get('PORT', { infer: true });
    await app.listen(port);
    // Set when Nx waits for this server to be ready
    if (process.env.NX_READY_SIGNAL_SOCKET) {
        try {
            // Function keeps TypeScript and bundlers from rewriting or bundling the import
            const load = new Function('s', 'return import(s)') as (
                s: string,
            ) => Promise<{ emitReadySignal(server: unknown): boolean }>;
            (await load('@nx/js/ready-signal')).emitReadySignal(app.getHttpServer());
        } catch {
            // @nx/js isn't installed
        }
    }
    logger.log(`Application is running on port ${port} (prefix /api, version v1)`);
}

void bootstrap();
