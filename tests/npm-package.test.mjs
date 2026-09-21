import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { mkdtempSync, readFileSync, realpathSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { stripVTControlCharacters } from 'node:util';
import test from 'node:test';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');

function run(command, args, cwd) {
  const result = spawnSync(command, args, { cwd, encoding: 'utf8', timeout: 120_000 });
  assert.equal(result.status, 0, `${result.error || ''}\n${result.stdout}\n${result.stderr}`);
  return result.stdout;
}

test('published tarball installs all four skills through npx', () => {
  const temp = mkdtempSync(join(tmpdir(), 'gantry-npm-'));
  try {
    const [pack] = JSON.parse(run('npm', [
      'pack', '--ignore-scripts', '--json', '--pack-destination', temp,
    ], root));
    const paths = pack.files.map(file => file.path);
    assert.equal(pack.name, '@julioborges/gantry');
    for (const skill of ['gantry', 'gantry-setup', 'gantry-dashboard', 'gantry-plan']) {
      assert.ok(paths.includes(`.agents/skills/${skill}/SKILL.md`));
    }
    assert.ok(paths.includes('.agents/skills/gantry/scripts/frontier.py'));
    assert.ok(paths.includes('.agents/skills/gantry/reference/round-workflow.md'));
    assert.ok(paths.includes('.agents/skills/gantry/schemas/critic.json'));
    assert.ok(paths.every(path => !/(__pycache__|\.pyc$|^tests\/|^fixture\/|^\.scratch\/|^\.mcp\.json$|^\.gantry\/)/.test(path)));
    run('npm', ['init', '--yes'], temp);
    run('npm', ['install', '--ignore-scripts', '--no-audit', '--no-fund', join(temp, pack.filename)], temp);
    const manifest = JSON.parse(readFileSync(join(temp, 'node_modules/@julioborges/gantry/package.json'), 'utf8'));
    run(process.execPath, ['-e',
      "require('./node_modules/@julioborges/gantry/.agents/skills/gantry/hooks/opencode.plugin.js')",
    ], temp);
    assert.equal(run('npx', ['--no-install', 'gantry', '--version'], temp).trim(), manifest.version);
    assert.match(run('npx', ['--no-install', 'gantry', '--help'], temp), /gantry add/);
    const listing = run('npx', ['--no-install', 'gantry', 'add', '--list'], temp);
    assert.match(stripVTControlCharacters(listing), /Found 4 skills/);
    run('npx', ['--no-install', 'gantry', 'add', '--agent', 'codex', '--yes'], temp);
    for (const skill of ['gantry', 'gantry-setup', 'gantry-dashboard', 'gantry-plan']) {
      const installed = join(temp, '.agents/skills', skill, 'SKILL.md');
      assert.match(readFileSync(installed, 'utf8'), new RegExp(`name: ${skill}\\n`));
      assert.ok(realpathSync(installed).startsWith(realpathSync(temp)));
    }
    const invalid = spawnSync('npx', ['--no-install', 'gantry', 'unknown'], { cwd: temp, encoding: 'utf8' });
    assert.equal(invalid.status, 1);
    assert.match(invalid.stderr, /Unknown command/);
  } finally {
    rmSync(temp, { recursive: true, force: true });
  }
});
