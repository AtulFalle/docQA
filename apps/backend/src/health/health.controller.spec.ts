import { Test } from '@nestjs/testing';
import { HealthCheckService, PrismaHealthIndicator } from '@nestjs/terminus';
import { PrismaService } from '../prisma/prisma.service';
import { AiServiceHealthIndicator } from './ai-service.health';
import { HealthController } from './health.controller';

describe('HealthController', () => {
    const check = jest.fn();
    let controller: HealthController;

    beforeEach(async () => {
        check.mockReset();
        const moduleRef = await Test.createTestingModule({
            controllers: [HealthController],
            providers: [
                { provide: HealthCheckService, useValue: { check } },
                { provide: PrismaHealthIndicator, useValue: { pingCheck: jest.fn() } },
                { provide: AiServiceHealthIndicator, useValue: { isHealthy: jest.fn() } },
                { provide: PrismaService, useValue: {} },
            ],
        }).compile();
        controller = moduleRef.get(HealthController);
    });

    it('liveness returns ok without touching dependencies', () => {
        expect(controller.liveness()).toEqual({ status: 'ok' });
        expect(check).not.toHaveBeenCalled();
    });

    it('readiness maps the terminus result', async () => {
        check.mockResolvedValue({
            status: 'ok',
            info: { database: { status: 'up' }, aiService: { status: 'up' } },
            error: {},
            details: {},
        });
        await expect(controller.readiness()).resolves.toEqual({
            status: 'ok',
            info: { database: { status: 'up' }, aiService: { status: 'up' } },
            error: {},
        });
        expect(check).toHaveBeenCalledWith(
            expect.arrayContaining([expect.any(Function), expect.any(Function)]),
        );
    });

    it('readiness defaults missing info/error to empty objects', async () => {
        check.mockResolvedValue({ status: 'ok', details: {} });
        await expect(controller.readiness()).resolves.toEqual({
            status: 'ok',
            info: {},
            error: {},
        });
    });
});
