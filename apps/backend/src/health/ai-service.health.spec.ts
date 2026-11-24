import { type ConfigService } from '@nestjs/config';
import { type HealthIndicatorService } from '@nestjs/terminus';
import { type Env } from '../config/env';
import { AiServiceHealthIndicator } from './ai-service.health';

describe('AiServiceHealthIndicator', () => {
    const originalFetch = global.fetch;
    let fetchMock: jest.Mock;
    let indicator: AiServiceHealthIndicator;

    beforeEach(() => {
        fetchMock = jest.fn();
        global.fetch = fetchMock as unknown as typeof fetch;
        const service = {
            check: (key: string) => ({
                up: () => ({ [key]: { status: 'up' } }),
                down: (data?: Record<string, unknown>) => ({ [key]: { status: 'down', ...data } }),
            }),
        } as unknown as HealthIndicatorService;
        const config = { get: () => 'http://ai:8001' } as unknown as ConfigService<Env, true>;
        indicator = new AiServiceHealthIndicator(service, config);
    });

    afterEach(() => {
        global.fetch = originalFetch;
    });

    it('is up on 2xx', async () => {
        fetchMock.mockResolvedValue({ ok: true, status: 200 });
        await expect(indicator.isHealthy('aiService')).resolves.toEqual({
            aiService: { status: 'up' },
        });
        expect(fetchMock).toHaveBeenCalledWith(
            'http://ai:8001/healthz',
            expect.objectContaining({ signal: expect.anything() }),
        );
    });

    it('is down on non-2xx', async () => {
        fetchMock.mockResolvedValue({ ok: false, status: 503 });
        const res = await indicator.isHealthy('aiService');
        expect(res['aiService']?.status).toBe('down');
    });

    it('is down on timeout', async () => {
        fetchMock.mockRejectedValue(new DOMException('timed out', 'TimeoutError'));
        const res = await indicator.isHealthy('aiService');
        expect(res['aiService']).toMatchObject({ status: 'down', message: 'timed out' });
    });
});
