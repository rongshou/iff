// Tianquan deploy webhook — triggered by GitHub Actions via nginx proxy
import { createServer } from 'node:http';
import { readFileSync, writeFileSync, existsSync } from 'node:fs';
import { randomBytes } from 'node:crypto';
import { execSync } from 'node:child_process';

const PORT = 7800;
const SECRET_FILE = '/home/admin/tianquan/.webhook-secret';
const CWD = '/home/admin/tianquan';
const BRANCH = 'master';

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
    res.write(`> git checkout ${BRANCH} && git pull origin ${BRANCH}\n`);
    res.write(execSync(`git checkout ${BRANCH} && git pull origin ${BRANCH} 2>&1`, {
      cwd: CWD, timeout: 30_000, encoding: 'utf-8',
    }));

    res.write('> npm run build --silent 2>&1\n');
    res.write(execSync('npm run build --silent 2>&1', {
      cwd: CWD, timeout: 180_000, encoding: 'utf-8',
    }));

    // 原子化：tar 打包 dist 后在容器内 rm + 解压
    // 失败时容器不会留下空目录（旧 html 仍在）
    res.write('> tar | docker exec (rm + extract dist)\n');
    res.write(execSync(
      `bash -c 'cd "${CWD}" && tar -C dist -cf - . | docker exec -i tianquan-nginx sh -c "rm -rf /usr/share/nginx/html/* && tar -C /usr/share/nginx/html -xf -"' 2>&1`,
      { timeout: 60_000, encoding: 'utf-8' },
    ));

    // 同步项目根的验证文件（微信、百度、Google 等站点验证用）
    // 规则：项目根下所有非排除目录的 .txt 文件
    res.write('> sync root verification files (e.g. *.txt for wechat)\n');
    const VERIFY_EXCLUDE = ['dist', 'node_modules', '.git', 'tianshu', 'backend', 'tests', 'scripts', 'logs', 'landing', '.github', 'node_modules_cache'];
    // 构建 find prune 表达式
    const pruneExpr = VERIFY_EXCLUDE.map(d => `-name "${d}" -prune -o`).join(' ');
    const verifyCmd = `find . ${pruneExpr} -type f -name "*.txt" -print 2>/dev/null | head -50`;
    const verifyFiles = execSync(verifyCmd, {
      cwd: CWD, encoding: 'utf-8', timeout: 10_000,
    }).trim().split('\n').filter(Boolean);
    for (const f of verifyFiles) {
      const abs = `${CWD}/${f.replace(/^\.\//, '')}`;
      const basename = f.split('/').pop();
      res.write(`  - ${basename}\n`);
      execSync(
        `docker cp "${abs}" tianquan-nginx:/usr/share/nginx/html/${basename} 2>&1`,
        { timeout: 10_000, encoding: 'utf-8' },
      );
    }

    res.write('[webhook] done\n');
  } catch (err) {
    res.write(`[webhook] error: ${err.message}\n`);
  }
  res.end();
}).listen(PORT, () => {
  console.log(`Webhook server running on 127.0.0.1:${PORT}`);
});
