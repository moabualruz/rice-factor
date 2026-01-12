import { test, expect } from '@playwright/test';

// Screenshot output directory - relative to where playwright runs (frontend dir)
// Goes up to rice_factor_web, then up to root, then into docs
const SCREENSHOT_DIR = '../../docs/assets/screenshots/web';

test.describe('Web UI Screenshots', () => {

  test('capture dashboard', async ({ page }) => {
    await page.goto('/');
    await page.waitForTimeout(1000);
    await page.screenshot({
      path: `${SCREENSHOT_DIR}/web-dashboard.png`,
      fullPage: true
    });
  });

  test('capture artifacts page', async ({ page }) => {
    await page.goto('/artifacts');
    await page.waitForTimeout(1000);
    await page.screenshot({
      path: `${SCREENSHOT_DIR}/web-artifacts.png`,
      fullPage: true
    });
  });

  test('capture diffs page', async ({ page }) => {
    await page.goto('/diffs');
    await page.waitForTimeout(1000);
    await page.screenshot({
      path: `${SCREENSHOT_DIR}/web-diffs.png`,
      fullPage: true
    });
  });

  test('capture approvals page', async ({ page }) => {
    await page.goto('/approvals');
    await page.waitForTimeout(1000);
    await page.screenshot({
      path: `${SCREENSHOT_DIR}/web-approvals.png`,
      fullPage: true
    });
  });

  test('capture history page', async ({ page }) => {
    await page.goto('/history');
    await page.waitForTimeout(1000);
    await page.screenshot({
      path: `${SCREENSHOT_DIR}/web-history.png`,
      fullPage: true
    });
  });

  test('capture configuration page', async ({ page }) => {
    await page.goto('/configuration');
    await page.waitForTimeout(1000);
    await page.screenshot({
      path: `${SCREENSHOT_DIR}/web-configuration.png`,
      fullPage: true
    });
  });

  test('capture commands page', async ({ page }) => {
    await page.goto('/commands');
    await page.waitForTimeout(1000);
    await page.screenshot({
      path: `${SCREENSHOT_DIR}/web-commands.png`,
      fullPage: true
    });
  });

  test('capture login page', async ({ page }) => {
    await page.goto('/login');
    await page.waitForTimeout(1000);
    await page.screenshot({
      path: `${SCREENSHOT_DIR}/web-login.png`,
      fullPage: true
    });
  });

  test('capture init page', async ({ page }) => {
    await page.goto('/init');
    await page.waitForTimeout(1000);
    await page.screenshot({
      path: `${SCREENSHOT_DIR}/web-init.png`,
      fullPage: true
    });
  });
});
