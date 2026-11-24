import { type HealthIndicatorService } from '@nestjs/terminus';
import createClient from 'openapi-fetch';
import { type AiApi } from '@docqa/contracts';
import { AiServiceHealthIndicator } from './ai-service.health';

describe('AiServiceHealthIndicator', () => {
    let fetchMock: jest.Mock<Promise<Response>, [Request]>;
    let indicator: AiServiceHealthIndicator;

    beforeEach(() => {
        fetchMock = jest.fn<Promise<Response>, [Request]>();
        const service = {
            check: (key: string) => ({
                up: () => ({ [key]: { status: 'up' } }),
                down: (data?: Record<string, unknown>) => ({ [key]: { status: 'down', ...data } }),
            }),
        } as unknown as HealthIndicatorService;
        // The real generated client, with fetch stubbed, so the test covers the contract too
        const client = createClient<AiApi.paths>({ baseUrl: 'http://ai:8001', fetch: fetchMock });
        indicator = new AiServiceHealthIndicator(service, client);
    });

    it('is up on 2xx and calls GET /healthz with a timeout', async () => {
        fetchMock.mockResolvedValue(Response.json({ status: 'ok' }));
        await expect(indicator.isHealthy('aiService')).resolves.toEqual({
            aiService: { status: 'up' },
        });
        const request = fetchMock.mock.calls[0]?.[0];
        expect(request?.method).toBe('GET');
        expect(request?.url).toBe('http://ai:8001/healthz');
        expect(request?.signal).toBeDefined();
    });

    it('is down on non-2xx', async () => {
        fetchMock.mockResolvedValue(new Response(null, { status: 503 }));
        const res = await indicator.isHealthy('aiService');
        expect(res['aiService']).toMatchObject({
            status: 'down',
            message: 'AI service responded with HTTP 503',
        });
    });

    it('is down on timeout', async () => {
        fetchMock.mockRejectedValue(new DOMException('timed out', 'TimeoutError'));
        const res = await indicator.isHealthy('aiService');
        expect(res['aiService']).toMatchObject({ status: 'down', message: 'timed out' });
    });
});
