import { Module } from '@nestjs/common';
import { ConfigModule, ConfigService } from '@nestjs/config';
import { APP_FILTER } from '@nestjs/core';
import { LoggerModule } from 'nestjs-pino';
import { AllExceptionsFilter } from './common/all-exceptions.filter';
import { loggerParams } from './common/logger.config';
import { type Env, validateEnv } from './config/env';
import { HealthModule } from './health/health.module';
import { InfoModule } from './info/info.module';
import { PrismaModule } from './prisma/prisma.module';

@Module({
    imports: [
        ConfigModule.forRoot({ isGlobal: true, cache: true, validate: validateEnv }),
        LoggerModule.forRootAsync({
            inject: [ConfigService],
            useFactory: (config: ConfigService<Env, true>) =>
                loggerParams({
                    LOG_LEVEL: config.get('LOG_LEVEL', { infer: true }),
                    SERVICE_NAME: config.get('SERVICE_NAME', { infer: true }),
                    APP_ENV: config.get('APP_ENV', { infer: true }),
                    NODE_ENV: config.get('NODE_ENV', { infer: true }),
                }),
        }),
        PrismaModule,
        HealthModule,
        InfoModule,
    ],
    providers: [{ provide: APP_FILTER, useClass: AllExceptionsFilter }],
})
export class AppModule {}
