import { chromium } from 'playwright';

async function run() {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto('file://' + process.cwd() + '/dashboard/index.html');

  const inputs = await page.locator('input').all();
  for (const b of inputs) {
      console.log('Input HTML: ', await b.evaluate(node => node.outerHTML));
  }

  const inputsMissingAria = await page.locator('input:not([aria-label])').count();
  console.log('Inputs missing aria-label: ', inputsMissingAria);

  await browser.close();
}

run();
