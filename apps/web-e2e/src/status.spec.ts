import { expect, test } from '@playwright/test';
import { degraded, mockApi } from './support/mock-api';

test('shows healthy status and dependency rows', async ({ page }) => {
    await mockApi(page);
    await page.goto('/');
    await expect(page.getByRole('heading', { name: 'System status' })).toBeVisible();
    await expect(page.getByText('All systems operational')).toBeVisible();
    await expect(page.getByRole('listitem').filter({ hasText: 'database' })).toContainText('Up');
    await expect(page.getByRole('listitem').filter({ hasText: 'aiService' })).toContainText('Up');
    await expect(page.getByText('v0.0.1')).toBeVisible();
});

test('shows degraded status on 503', async ({ page }) => {
    await mockApi(page, { body: degraded, status: 503 });
    await page.goto('/');
    await expect(page.getByText('Degraded')).toBeVisible();
    await expect(page.getByRole('listitem').filter({ hasText: 'aiService' })).toContainText('Down');
});

test('requests carry X-Request-ID', async ({ page }) => {
    const seen = await mockApi(page);
    await page.goto('/');
    await expect(page.getByText('All systems operational')).toBeVisible();
    expect(seen.length).toBeGreaterThan(0);
    for (const h of seen) expect(h['x-request-id']).toMatch(/^[0-9a-f-]{36}$/);
});
