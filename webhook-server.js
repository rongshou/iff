// Tianshu deploy webhook — triggered by GitHub Actions via nginx proxy
import { createServer } from 'node:http';
import { readFileSync, writeFileSync, existsSync } from 'node:fs';
import { randomBytes } from 'node:crypto';
import { execSync } from 'node:child_process';

const PORT = 7800;
const SECRET_FILE = '/home/admin/tianquan/.webhook-secret';
const CWD = '/home/admin/tianquan';

// Load secret from file (create one if missing)
function loadSecret() {
  if (!existsSync(SECRET_FILE)) {
    const secret = randomBytes(32).toString('hex');
    writeFileSync(SECRET_FILE, secret + '\n', { mode: 0o600 });
  }
  return readFileSync(SECRET_FILE, 'utf-8').trim();
}

const VALID_TOKEN = loadSecret();
console.log(`Webhook secret (save this): ${VALID_TOKEN}`);

createServer((req, res) => {
  const url = new URL(req.url, `http://localhost:${PORT}`);

  if (req.method !== 'POST' || url.pathname !== '/webhook/tianshu') {
    res.writeHead(404);
    return res.end('Not found');
  }

  // Verify bearer token or ?token= param
  const auth = req.headers['authorization'] || '';
  const token = url.searchParams.get('token') || '';
  const bearer = auth.startsWith('Bearer ') ? auth.slice(7) : '';
  if (bearer !== VALID_TOKEN && token !== VALID_TOKEN) {
    res.writeHead(403);
    return res.end('Forbidden');
  }

  res.writeHead(200, { 'Content-Type': 'text/plain; charset=utf-8' });
  res.write('[webhook] deploy triggered...\n');

  try {
    res.write('> git pull origin master\n');
    res.write(execSync('git pull origin master 2>&1', { cwd: CWD, timeout: 30_000, encoding: 'utf-8' }));

    res.write('> npm run build --silent 2>&1\n');
    res.write(execSync('npm run build --silent 2>&1', { cwd: CWD, timeout: 180_000, encoding: 'utf-8' }));

    res.write('> docker restart tianquan-nginx\n');
    execSync('docker restart tianquan-nginx 2>&1', { timeout: 15_000, encoding: 'utf-8' });

    res.write('[webhook] done\n');
  } catch (err) {
    res.write(`[webhook] error: ${err.message}\n`);
  }
  res.end();
}).listen(PORT, () => {
  console.log(`Webhook server running on 127.0.0.1:${PORT}`);
});
