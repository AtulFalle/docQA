import { Injectable, type OnModuleDestroy } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { PrismaPg } from '@prisma/adapter-pg';
import { type Prisma, PrismaClient } from '../generated/prisma/client';
import { type Env } from '../config/env';

@Injectable()
export class PrismaService extends PrismaClient implements OnModuleDestroy {
    constructor(config: ConfigService<Env, true>) {
        super({
            adapter: new PrismaPg({
                connectionString: config.get('DATABASE_URL', { infer: true }),
            }),
        });
    }

    async onModuleDestroy(): Promise<void> {
        await this.$disconnect();
    }

    /** Runs `fn` in a transaction with `app.tenant_id` set so Postgres RLS scopes every query. */
    withTenant<T>(tenantId: string, fn: (tx: Prisma.TransactionClient) => Promise<T>): Promise<T> {
        return this.$transaction(async (tx) => {
            await tx.$executeRaw`SELECT set_config('app.tenant_id', ${tenantId}, true)`;
            return fn(tx);
        });
    }
}
