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

test('authentication flow', async ({ page }) => {
  // Wait for backend to be ready
  await waitForBackend(page);

  // Listen to console messages for debugging
  page.on('console', msg => {
    console.log(`Browser ${msg.type()}: ${msg.text()}`);
  });

  // Listen to page errors
  page.on('pageerror', error => {
    console.error(`Browser error: ${error}`);
  });

  // Listen to network requests for debugging
  page.on('request', request => {
    console.log('Request:', request.method(), request.url());
  });

  page.on('response', async response => {
    console.log('Response:', response.status(), response.url());
    if (response.url().includes('/api/auth/session')) {
      try {
        const data = await response.json();
        console.log('Session data:', data);
      } catch (e) {
        console.error('Error parsing session response:', e);
      }
    }
  });

  // Try to visit topics page which should redirect to signin
  await page.goto('/topics');
  await page.waitForURL('**/auth/signin?callbackUrl=%2Ftopics');
  
  // Verify we're on the sign-in page
  const signInHeading = await page.getByRole('heading', { name: 'Welcome to QuizMaster Pro' });
  await expect(signInHeading).toBeVisible();

  // Click the development sign in button and wait for the callback URL
  const signInButton = await page.getByRole('button', { name: 'Development Sign In' });
  await Promise.all([
    signInButton.click(),
    page.waitForURL(/\/topics$/),
  ]);

  // Wait for the topics page to load
  await page.waitForURL(/\/topics$/);
  await page.waitForLoadState('networkidle');

  // Verify we're on the topics page and can see the content
  const topicsHeading = await page.getByRole('heading', { name: 'Topics' });
  await expect(topicsHeading).toBeVisible();

  // Get the access token from the session
  const sessionData = await page.evaluate(async () => {
    const response = await fetch('/api/auth/session');
    return response.json();
  });
  
  // Verify we can access the topics API with proper auth
  const response = await page.request.get('http://localhost:8000/api/topics', {
    headers: {
      'Authorization': `Bearer ${sessionData.accessToken}`,
      'Content-Type': 'application/json'
    }
  });
  expect(response.status()).toBe(200);

  // Make sure we stay on the topics page after reload
  await page.reload();
  await expect(topicsHeading).toBeVisible();

  // Log auth state for debugging
  const cookies = await page.context().cookies();
  console.log('Cookies:', cookies);

  const localStorage = await page.evaluate(() => {
    const items: Record<string, string> = {};
    const length: number = window.localStorage.length;
    for (let i = 0; i < length; i++) {
      const key = window.localStorage.key(i);
      if (key) {
        items[key] = window.localStorage.getItem(key) || '';
      }
    }
    return items;
  });
  console.log('LocalStorage:', localStorage);
});
