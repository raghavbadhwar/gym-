import { chromium } from 'playwright';

async function run() {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto('file://' + process.cwd() + '/dashboard/index.html');

  const buttons = await page.locator('button:has(svg):not([aria-label])').all();
  for (const b of buttons) {
      console.log('Button HTML: ', await b.evaluate(node => node.outerHTML));
  }

  await browser.close();
}

run();
