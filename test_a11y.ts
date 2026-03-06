import { chromium } from 'playwright';

async function run() {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto('file://' + process.cwd() + '/dashboard/index.html');

  // check labels and a11y attributes on inputs/buttons
  const noAriaInputs = await page.locator('input:not([aria-label]):not([id])').count();
  console.log(`Inputs missing aria-label and id: ${noAriaInputs}`);

  const iconButtons = await page.locator('button:has(svg):not([aria-label])').count();
  console.log(`Icon buttons missing aria-label: ${iconButtons}`);

  const allButtons = await page.locator('button:not([aria-label])').count();
  console.log(`All buttons missing aria-label: ${allButtons}`);

  const modalClose = await page.locator('.modal-close:not([aria-label])').count();
  console.log(`Modal close buttons missing aria-label: ${modalClose}`);

  await browser.close();
}

run();
