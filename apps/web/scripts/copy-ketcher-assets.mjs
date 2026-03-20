import { cpSync, existsSync, mkdirSync, rmSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const webRoot = resolve(here, '..');
const sourceDir = resolve(webRoot, 'node_modules', 'ketcher-standalone', 'dist');
const targetDir = resolve(webRoot, 'public', 'ketcher', 'dist');

if (!existsSync(sourceDir)) {
  console.warn('[ketcher] source assets not found, skip copy:', sourceDir);
  process.exit(0);
}

rmSync(targetDir, { recursive: true, force: true });
mkdirSync(targetDir, { recursive: true });
cpSync(sourceDir, targetDir, { recursive: true });
console.log('[ketcher] assets copied to', targetDir);
