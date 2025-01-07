import { test, expect } from '@playwright/test';
import type { Response } from '@playwright/test';

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

async function signIn(page: any) {
  // Try to visit topics page which should redirect to signin
  await page.goto('/topics');
  await page.waitForURL('**/auth/signin?callbackUrl=%2Ftopics');
  
  // Verify we're on the sign-in page
  const signInHeading = await page.getByRole('heading', { name: 'Welcome to QuizMaster Pro' });
  await expect(signInHeading).toBeVisible();
  console.log('On sign-in page');

  // Click the development sign in button and wait for redirect
  const signInButton = await page.getByRole('button', { name: 'Development Sign In' });
  await Promise.all([
    signInButton.click(),
    page.waitForURL(/\/topics$/),
  ]);
  console.log('Clicked sign-in button');

  // Wait for the topics page to load completely
  await page.waitForURL(/\/topics$/);
  await page.waitForLoadState('networkidle');
  console.log('Page loaded');

  // Get the access token from the session
  const sessionData = await page.evaluate(async () => {
    const response = await fetch('/api/auth/session');
    return response.json();
  });
  console.log('Got session data');

  // Verify we can access the topics API with proper auth
  const response = await page.request.get('http://localhost:8000/api/topics', {
    headers: {
      'Authorization': `Bearer ${sessionData.accessToken}`,
      'Content-Type': 'application/json'
    }
  });
  expect(response.status()).toBe(200);
  console.log('Verified API access');
}

test('topic creation and editing flow', async ({ page }) => {
  // Set a reasonable timeout
  test.setTimeout(30000);

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

  // Handle confirmation dialogs
  page.on('dialog', dialog => dialog.accept());

  // Sign in
  await signIn(page);

  // Wait for the topics page to be visible
  await expect(page.getByRole('heading', { name: 'Topics' })).toBeVisible();
  console.log('Topics page is visible');

  // Wait for topics to load
  await page.waitForResponse(response => 
    response.url().includes('/api/topics') && 
    response.status() === 200
  );

  // Click on Create Topic button
  await page.getByRole('link', { name: 'Create New Topic' }).click();

  // Wait for the create form to be visible
  await expect(page.getByRole('heading', { name: 'Create New Topic' })).toBeVisible();
  console.log('Create form is visible');

  // Fill in the topic form
  const topicTitle = 'Test Topic ' + Date.now();
  const topicDescription = 'This is a test topic description created by Playwright';
  
  await page.getByLabel('Title').fill(topicTitle);
  await page.getByLabel('Description').fill(topicDescription);
  console.log('Filled in form with:', { topicTitle, topicDescription });
  
  // Submit the form and wait for navigation
  console.log('Submitting form...');
  await Promise.all([
    page.waitForURL('/topics'),
    page.getByRole('button', { name: 'Create Topic' }).click()
  ]);
  console.log('Form submitted, navigated back to topics page');

  // Wait for the topics list to load
  await page.waitForResponse(response => 
    response.url().includes('/api/topics') && 
    response.request().method() === 'GET' &&
    response.status() === 200
  );

  // Log the response data
  const responseData = await page.evaluate(async () => {
    const response = await fetch('/api/topics');
    return response.json();
  });
  console.log('Topics response:', responseData);

  // Find the topic container that has both the title and description
  const topicLocator = page.locator('li', {
    has: page.getByText(topicTitle),
    hasText: topicDescription
  });
  await expect(topicLocator).toBeVisible();
  await page.waitForTimeout(1000); // Wait for any animations to complete

  console.log('Found topic in list:', topicTitle);

  // Click edit on the newly created topic
  const editLink = topicLocator.getByRole('link', { name: 'Edit' });
  await expect(editLink).toBeVisible();
  await expect(editLink).toBeEnabled();
  console.log('Found edit link, clicking...');
  await editLink.click();

  // Wait for the edit form to be visible
  await expect(page.getByLabel('Title')).toBeVisible();
  await expect(page.getByLabel('Description')).toBeVisible();

  // Update the topic
  const updatedTitle = `${topicTitle} - Updated`;
  const updatedDescription = `${topicDescription} - Updated`;
  
  await page.getByLabel('Title').fill(updatedTitle);
  await page.getByLabel('Description').fill(updatedDescription);

  // Submit the edit form
  console.log('Submitting edit form...');
  await page.getByRole('button', { name: 'Save Changes' }).click();

  // Wait for redirect and verify the updated topic appears in the list
  await page.waitForURL('/topics');
  const updatedTopicLocator = page.locator('li', {
    has: page.getByText(updatedTitle),
    hasText: updatedDescription
  });
  await expect(updatedTopicLocator).toBeVisible();

  // Find the updated topic and hover over it to reveal the delete button
  const updatedTopicElement = updatedTopicLocator.first();
  await updatedTopicElement.hover();

  // Wait for any delete button to be visible
  await page.waitForSelector('button[aria-label="Delete topic"]', { state: 'visible' });

  // Get all delete buttons and click the one within our topic
  const deleteButtons = page.locator('button[aria-label="Delete topic"]');
  const count = await deleteButtons.count();
  let deleteButtonFound = false;
  for (let i = 0; i < count; i++) {
    const button = deleteButtons.nth(i);
    const isInTopic = await button.evaluate((el, title) => {
      const listItem = el.closest('li');
      return listItem?.textContent?.includes(title) ?? false;
    }, updatedTitle);
    if (isInTopic) {
      // Wait for both the click and the API response
      await Promise.all([
        page.waitForResponse(response => 
          response.url().includes('/api/topics') && 
          response.request().method() === 'DELETE' &&
          response.status() === 204
        ),
        button.click()
      ]);
      deleteButtonFound = true;
      break;
    }
  }

  // Verify that we found and clicked a delete button
  expect(deleteButtonFound).toBe(true);

  // Wait for the topic element to be removed from the DOM
  await expect(updatedTopicLocator).not.toBeVisible({ timeout: 5000 });
});

test('topic creation and AI blueprint generation flow', async ({ page }) => {
  // Set a longer timeout for AI generation
  test.setTimeout(300000); // 5 minutes

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
    try {
      const contentType = response.headers()['content-type'];
      if (contentType && contentType.includes('application/json')) {
        const data = await response.json();
        console.log('Response data:', data);
      }
    } catch (e) {
      console.error('Error parsing response:', e);
    }
  });

  // Handle confirmation dialogs
  page.on('dialog', dialog => dialog.accept());

  // Sign in
  await signIn(page);

  // Verify we're on the topics page
  await page.waitForSelector('h1:has-text("Topics")');
  console.log('Topics page is visible');

  // Click the new topic button
  await page.click('a[href="/topics/new"]');

  // Wait for the create form to be visible
  await page.waitForSelector('form');
  console.log('Create form is visible');

  // Generate a unique topic title with timestamp
  const timestamp = new Date().toISOString().replace(/[-:]/g, '').split('.')[0];
  const topicTitle = `Playwright Testing ${timestamp}`;
  const topicDescription = 'A comprehensive guide to using Playwright for automated UI testing, covering setup, writing tests, and best practices.';

  // Fill out the form
  await page.fill('input[name="title"]', topicTitle);
  await page.fill('textarea[name="description"]', topicDescription);
  console.log('Form filled with:', { topicTitle, topicDescription });

  // Submit the form and wait for navigation
  await Promise.all([
    page.click('button[type="submit"]'),
    page.waitForResponse(response => 
      response.url().includes('/api/topics') && 
      response.request().method() === 'POST' &&
      response.status() === 201
    )
  ]);
  console.log('Topic created successfully');

  // Wait for navigation to topics page and for the new topic to appear
  await page.waitForURL('/topics');
  await page.waitForResponse(response => 
    response.url().includes('/api/topics') && 
    response.request().method() === 'GET' &&
    response.status() === 200
  );

  // Find and click on the newly created topic's "View topic details" link
  const topicContainer = page.locator('li', {
    has: page.getByText(topicTitle)
  });
  await expect(topicContainer).toBeVisible();
  
  const viewDetailsLink = topicContainer.getByRole('link', { name: 'View topic details' });
  await expect(viewDetailsLink).toBeVisible();
  await viewDetailsLink.click();
  console.log('Navigated to topic page');

  // Wait for the topic details page to load
  await page.waitForSelector('h1:has-text("' + topicTitle + '")');
  console.log('Topic details page loaded');

  // Click the Generate Blueprint button
  const generateButton = page.getByRole('button', { name: 'Generate Blueprint' });
  await expect(generateButton).toBeVisible();
  await generateButton.click();
  console.log('Clicked Generate Blueprint button');

  // Wait for the blueprint generation to start
  await page.waitForResponse(response => 
    response.url().includes('/api/topics') && 
    response.url().includes('/blueprints') &&
    response.request().method() === 'POST' &&
    response.status() === 201
  );
  console.log('Blueprint generation started');

  // Wait for the blueprint to appear in the list
  const blueprintListItem = page.locator('.blueprint-list-item').first();
  await expect(blueprintListItem).toBeVisible({ timeout: 240000 }); // 4 minute timeout
  console.log('Blueprint appeared in list');

  // Click on the blueprint to view details
  await blueprintListItem.click();
  console.log('Clicked on blueprint');

  // Verify blueprint details are visible
  const blueprintDetails = page.locator('.blueprint-details');
  await expect(blueprintDetails).toBeVisible();
  console.log('Blueprint details are visible');

  // Success!
  console.log('Test completed successfully');
});
