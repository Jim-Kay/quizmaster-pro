import { test, expect } from '@playwright/test';

async function waitForBackend(page: any) {
  let retries = 5;
  while (retries > 0) {
    try {
      const response = await fetch('http://localhost:8000/api/health');
      if (response.ok) {
        return;
      }
    } catch (e) {
      console.log('Backend not ready, retrying...');
    }
    await new Promise(resolve => setTimeout(resolve, 1000));
    retries--;
  }
  throw new Error('Backend not ready after 5 retries');
}

test('settings page access and functionality', async ({ page }) => {
  // Wait for backend to be ready
  await waitForBackend(page);

  // Setup debug listeners
  page.on('console', msg => console.log(`Browser ${msg.type()}: ${msg.text()}`));
  page.on('pageerror', error => console.error(`Browser error: ${error}`));

  // Go to the settings page which should redirect to sign in
  await page.goto('http://localhost:3000/settings');
  await page.waitForURL(/\/auth\/signin/);
  
  // Verify we're on the sign-in page
  const signInHeading = await page.getByRole('heading', { name: 'Welcome to QuizMaster Pro' });
  await expect(signInHeading).toBeVisible();

  // Click the development sign in button
  const signInButton = await page.getByRole('button', { name: 'Development Sign In' });
  await Promise.all([
    signInButton.click(),
    page.waitForURL(/\/settings$/),
  ]);

  // Wait for the settings page to load
  await page.waitForURL(/\/settings$/);
  await page.waitForLoadState('networkidle');
  
  // Verify we're on the settings page
  const settingsHeading = await page.getByRole('heading', { name: 'Settings' });
  await expect(settingsHeading).toBeVisible();
  
  // Check if the form elements are present
  await expect(page.locator('select')).toBeVisible();
  await expect(page.getByLabel(/OpenAI API Key/i)).toBeVisible();
  await expect(page.getByLabel(/Anthropic API Key/i)).toBeVisible();
  
  // Try changing the LLM provider
  await page.selectOption('select', 'anthropic');
  
  // Submit the form
  await page.click('button[type="submit"]');
  
  // Verify success message
  await expect(page.locator('text=Settings updated successfully')).toBeVisible();
});
