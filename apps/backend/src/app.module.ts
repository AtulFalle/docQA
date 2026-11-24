import { randomUUID } from 'node:crypto';
import { type IncomingMessage, type ServerResponse } from 'node:http';
import { Module } from '@nestjs/common';
import { ConfigModule, ConfigService } from '@nestjs/config';
import { APP_FILTER } from '@nestjs/core';
import { trace } from '@opentelemetry/api';
import { LoggerModule } from 'nestjs-pino';
import { AllExceptionsFilter } from './common/all-exceptions.filter';
import { type Env, validateEnv } from './config/env';
import { HealthModule } from './health/health.module';
import { InfoModule } from './info/info.module';
import { PrismaModule } from './prisma/prisma.module';

@Module({
    imports: [
        ConfigModule.forRoot({ isGlobal: true, cache: true, validate: validateEnv }),
        LoggerModule.forRootAsync({
            inject: [ConfigService],
            useFactory: (config: ConfigService<Env, true>) => ({
                pinoHttp: {
                    level: config.get('LOG_LEVEL', { infer: true }),
                    genReqId: (req: IncomingMessage, res: ServerResponse) => {
                        const incoming = req.headers['x-request-id'];
                        const id =
                            (Array.isArray(incoming) ? incoming[0] : incoming) || randomUUID();
                        res.setHeader('X-Request-ID', id);
                        return id;
                    },
                    customProps: () => {
                        const ctx = trace.getActiveSpan()?.spanContext();
                        return ctx ? { trace_id: ctx.traceId, span_id: ctx.spanId } : {};
                    },
                    redact: ['req.headers.authorization', 'req.headers.cookie'],
                    transport:
                        config.get('NODE_ENV', { infer: true }) === 'development'
                            ? { target: 'pino-pretty' }
                            : undefined,
                    autoLogging: {
                        ignore: (req: IncomingMessage) =>
                            req.url?.startsWith('/api/v1/health') ?? false,
                    },
                },
            }),
        }),
        PrismaModule,
        HealthModule,
        InfoModule,
    ],
    providers: [{ provide: APP_FILTER, useClass: AllExceptionsFilter }],
})
export class AppModule {}
