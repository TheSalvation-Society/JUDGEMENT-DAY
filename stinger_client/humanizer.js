// DΞMON CORE: HUMANIZER v1.0
// The puppet's strings. Makes the ghost feel real.

/**
 * Waits for a random duration within a specified range.
 * @param {number} min - The minimum delay in milliseconds.
 * @param {number} max - The maximum delay in milliseconds.
 */
async function randomDelay(min, max) {
    const duration = Math.floor(Math.random() * (max - min + 1)) + min;
    await new Promise(resolve => setTimeout(resolve, duration));
}

/**
 * Moves the mouse to a selector's location in a more human-like way.
 * This is a simplified version; true human-like movement uses Bezier curves.
 * @param {import('puppeteer').Page} page - The Puppeteer page object.
 * @param {string} selector - The CSS selector for the target element.
 */
async function humanLikeMouseMove(page, selector) {
    const element = await page.waitForSelector(selector);
    const box = await element.boundingBox();

    if (!box) {
        throw new Error(`Element with selector "${selector}" is not visible or has no bounding box.`);
    }

    const startX = (await page.mouse.position()).x;
    const startY = (await page.mouse.position()).y;

    // Calculate a random point within the element's bounding box
    const targetX = box.x + Math.random() * box.width;
    const targetY = box.y + Math.random() * box.height;

    // Simulate the mouse movement over a random number of steps
    const steps = Math.floor(Math.random() * 5) + 5; // 5 to 10 steps
    await page.mouse.move(targetX, targetY, { steps });
    await randomDelay(100, 300); // Small pause after moving
}

/**
 * Simulates random scrolling on the page.
 * @param {import('puppeteer').Page} page - The Puppeteer page object.
 */
async function randomScroll(page) {
    const scrollAmount = Math.floor(Math.random() * 300) + 100; // Scroll between 100 and 400 pixels
    const scrollDirection = Math.random() > 0.5 ? 1 : -1; // Up or down
    await page.evaluate((amount, direction) => {
        window.scrollBy(0, amount * direction);
    }, scrollAmount, scrollDirection);
    await randomDelay(500, 1500);
}

module.exports = {
    randomDelay,
    humanLikeMouseMove,
    randomScroll,
};