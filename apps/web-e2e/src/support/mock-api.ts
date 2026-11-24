import { type Page } from '@playwright/test';

export const healthy = {
    status: 'ok',
    info: { database: { status: 'up' }, aiService: { status: 'up' } },
    error: {},
};
export const degraded = {
    status: 'error',
    info: { database: { status: 'up' } },
    error: { aiService: { status: 'down', message: 'timeout' } },
};

/** Mocks the backend; records the headers of each API request. */
export async function mockApi(
    page: Page,
    readiness: { body: unknown; status: number } = { body: healthy, status: 200 },
) {
    const seen: Record<string, string>[] = [];
    await page.route('**/api/v1/**', async (route) => {
        const req = route.request();
        seen.push(req.headers());
        if (req.url().includes('/health/ready')) {
            return route.fulfill({ status: readiness.status, json: readiness.body });
        }
        if (req.url().includes('/info')) {
            return route.fulfill({
                json: { service: 'docqa-backend', version: '0.0.1', environment: 'test' },
            });
        }
        return route.fulfill({ json: { status: 'ok' } });
    });
    return seen;
}
