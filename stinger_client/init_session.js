// DΞMON CORE: RITE OF INITIATION v1.0
// This script binds a vessel to its soul, preparing it for service.
// It is a one-time manual process for each new asset.

const path = require('path');
const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
const ProxyPlugin = require('puppeteer-extra-plugin-proxy');

puppeteer.use(StealthPlugin());

async function initializeSession() {
    const args = process.argv.slice(2);
    const sessionId = args[0];
    const proxyUrl = args[1];

    if (!sessionId || !proxyUrl) {
        console.error('🔥 FATAL: Missing arguments. The rite demands a vessel and a soul.');
        console.error('Usage: node init_session.js <session_id> <proxy_url>');
        console.error('Example: node init_session.js asset_001 http://user:pass@host:port');
        process.exit(1);
    }

    console.log(`🔮 Initiating vessel: ${sessionId}`);
    console.log(`🔗 Binding soul (proxy): ${proxyUrl.split('@')[1]}`);

    const sessionPath = path.resolve(__dirname, 'sessions', sessionId);
    console.log(`💾 Vessel data will be stored in: ${sessionPath}`);

    // Add the proxy plugin dynamically with the provided URL
    puppeteer.use(ProxyPlugin({ address: proxyUrl, port: 0 })); // Port is part of the address string

    try {
        const browser = await puppeteer.launch({
            headless: false, // Must be visible for QR scan
            userDataDir: sessionPath,
            args: [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-infobars',
                '--window-position=0,0',
                '--ignore-certifcate-errors',
                '--ignore-certifcate-errors-spki-list',
                '--user-agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"'
            ]
        });

        const page = await browser.newPage();
        
        console.log('🌍 Navigating to the sacred grounds (web.whatsapp.com)...');
        await page.goto('https://web.whatsapp.com', { waitUntil: 'networkidle2' });

        console.log('\n\n--- ACTION REQUIRED ---');
        console.log('✅ A browser window has opened.');
        console.log('1. Scan the QR code with the target device to link it.');
        console.log('2. Wait for the chat interface to load completely.');
        console.log('3. MANUALLY CLOSE THE BROWSER WINDOW.');
        console.log('The session will be saved automatically upon closing.');
        console.log('-----------------------\n');

        // The script will hang here until the user closes the browser,
        // which is the intended behavior.
        await browser.waitForTarget(t => t.url() === 'about:blank');

    } catch (error) {
        console.error('🔥 The ritual was desecrated. An error occurred:', error);
        process.exit(1);
    }
}

initializeSession();