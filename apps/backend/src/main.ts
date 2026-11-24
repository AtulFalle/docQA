import './instrumentation';
import { type INestApplication, VersioningType } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { NestFactory } from '@nestjs/core';
import { Logger } from 'nestjs-pino';
import { AppModule } from './app.module';
import { type Env } from './config/env';
import { writeOpenApiDocument } from './openapi/openapi';

const EXPORT_FLAG = '--export-openapi=';

function configure(app: INestApplication): void {
    app.setGlobalPrefix('api');
    app.enableVersioning({ type: VersioningType.URI, defaultVersion: '1' });
}

async function emitNxReadySignal(app: INestApplication): Promise<void> {
    // Set when Nx waits for this server to be ready
    if (!process.env.NX_READY_SIGNAL_SOCKET) {
        return;
    }
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

async function bootstrap(): Promise<void> {
    const app = await NestFactory.create(AppModule, { bufferLogs: true });
    const logger = app.get(Logger);
    app.useLogger(logger);
    configure(app);
    app.enableShutdownHooks();

    const port = app.get<ConfigService<Env, true>>(ConfigService).get('PORT', { infer: true });
    await app.listen(port);
    await emitNxReadySignal(app);
    logger.log(`Application is running on port ${port} (prefix /api, version v1)`);
}

/** `node main.js --export-openapi=<file>` writes the OpenAPI document and exits (no listen). */
async function exportOpenApi(path: string): Promise<void> {
    const app = await NestFactory.create(AppModule, { logger: false });
    configure(app);
    writeOpenApiDocument(app, path);
    await app.close();
}

const exportArg = process.argv.find((arg) => arg.startsWith(EXPORT_FLAG));
void (exportArg ? exportOpenApi(exportArg.slice(EXPORT_FLAG.length)) : bootstrap());
