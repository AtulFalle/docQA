import { Injectable, type OnModuleDestroy } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { PrismaPg } from '@prisma/adapter-pg';
import { type Prisma, PrismaClient } from '../generated/prisma/client';
import { type Env } from '../config/env';

/** Optional per-request identity carried into the database session. */
export interface TenantContext {
    userId?: string;
    requestId?: string;
}

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

    /**
     * Runs `fn` in a transaction with the RLS context set: `app.tenant_id` (read by every
     * tenant policy) plus `app.user_id` and `app.request_id` for defaults and audit.
     * The settings last for this transaction only, so they are safe behind PgBouncer.
     */
    withTenant<T>(
        tenantId: string,
        fn: (tx: Prisma.TransactionClient) => Promise<T>,
        context: TenantContext = {},
    ): Promise<T> {
        return this.$transaction(async (tx) => {
            await tx.$executeRaw`SELECT set_config('app.tenant_id', ${tenantId}, true),
                set_config('app.user_id', ${context.userId ?? ''}, true),
                set_config('app.request_id', ${context.requestId ?? ''}, true)`;
            return fn(tx);
        });
    }
}
