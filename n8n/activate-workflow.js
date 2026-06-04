const http = require('http');

const N8N_PORT = 5678;
const WORKFLOW_ID = 'e1b2c3d4-5a6b-7c8d-9e0f-a1b2c3d4e5f6';
const OWNER_EMAIL = 'admin@datamarket.local';
const OWNER_PASSWORD = 'Admin123!';

function req(method, path, body, cookie) {
    return new Promise((resolve) => {
        const opts = {
            hostname: 'localhost', port: N8N_PORT,
            path: path, method: method,
            headers: { 'Content-Type': 'application/json' }
        };
        if (cookie) opts.headers['Cookie'] = cookie;
        const r = http.request(opts, (res) => {
            let data = '';
            res.on('data', (c) => data += c);
            res.on('end', () => {
                res.body = data;
                resolve(res);
            });
        });
        r.on('error', (err) => resolve({ statusCode: 0, body: err.message }));
        if (body) r.write(JSON.stringify(body));
        r.end();
    });
}

function parseCookie(res) {
    const val = res.headers['set-cookie'];
    if (!val) return null;
    const arr = Array.isArray(val) ? val : [val];
    for (const c of arr) {
        if (c.startsWith('n8n-auth=')) return c.split(';')[0];
    }
    return null;
}

async function main() {
    console.log('Setting up owner...');
    let res = await req('POST', '/rest/owner/setup', {
        email: OWNER_EMAIL, password: OWNER_PASSWORD,
        firstName: 'Admin', lastName: 'DataMarket'
    });
    console.log('Owner setup: ' + res.statusCode);

    console.log('Logging in...');
    res = await req('POST', '/rest/login', {
        emailOrLdapLoginId: OWNER_EMAIL, password: OWNER_PASSWORD
    });
    if (res.statusCode !== 200) {
        console.log('Login failed: ' + res.statusCode + ' ' + res.body);
        return;
    }
    const cookie = parseCookie(res);
    if (!cookie) { console.log('No cookie received'); return; }
    console.log('Logged in');

    console.log('Fetching workflow...');
    res = await req('GET', '/rest/workflows/' + WORKFLOW_ID, null, cookie);
    if (res.statusCode !== 200) {
        console.log('Get workflow failed: ' + res.statusCode + ' ' + res.body.substring(0,200));
        return;
    }
    const workflow = JSON.parse(res.body).data;
    const versionId = workflow.versionId;
    console.log('versionId: ' + versionId);

    console.log('Activating workflow...');
    res = await req('POST', '/rest/workflows/' + WORKFLOW_ID + '/activate', { versionId }, cookie);
    if (res.statusCode === 200) {
        const data = JSON.parse(res.body).data;
        console.log('Activated! Active: ' + data.active + ', Triggers: ' + data.triggerCount);
    } else {
        console.log('Activation failed: ' + res.statusCode + ' ' + res.body.substring(0,200));
    }
}

main().catch((err) => console.error('Script error:', err.message));
