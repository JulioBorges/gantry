import { spawnSync } from 'node:child_process';
import { pathToFileURL } from 'node:url';

const author = 'julioborges';
const registry = 'https://registry.npmjs.org/';

export function ensureNpmAuthor(run = spawnSync) {
  const args = ['whoami', '--registry', registry];
  const result = process.env.npm_execpath
    ? run(process.execPath, [process.env.npm_execpath, ...args], { encoding: 'utf8', timeout: 30_000 })
    : run(process.platform === 'win32' ? 'npm.cmd' : 'npm', args, {
      encoding: 'utf8', timeout: 30_000, shell: process.platform === 'win32',
    });
  if (result.error || result.status !== 0) {
    throw new Error('Publication blocked: could not verify the npm account. Run npm login for npmjs.org.');
  }
  if (result.stdout.trim() !== author) {
    throw new Error(`Publication blocked: only npm account ${author} may publish this package.`);
  }
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  try {
    ensureNpmAuthor();
  } catch (error) {
    console.error(error.message);
    process.exitCode = 1;
  }
}
