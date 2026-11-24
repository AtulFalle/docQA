import { expect, test } from '@playwright/test';
import { mockApi } from './support/mock-api';

test.beforeEach(async ({ page }) => {
    await mockApi(page);
});

test('navigates to Ask', async ({ page }) => {
    await page.goto('/');
    await page
        .getByRole('navigation', { name: 'Primary' })
        .getByRole('link', { name: 'Ask' })
        .click();
    await expect(page).toHaveURL(/\/ask$/);
    await expect(page.getByText('Answering is coming in M1 (query API)')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Ask' })).toBeDisabled();
});

test('unknown route shows the 404 page with a link home', async ({ page }) => {
    await page.goto('/nope/nothing');
    await expect(page.getByRole('heading', { name: 'Page not found' })).toBeVisible();
    await page.getByRole('link', { name: 'Back to status' }).click();
    await expect(page).toHaveURL(/\/$/);
});
