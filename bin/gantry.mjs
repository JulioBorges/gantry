#!/usr/bin/env node
import { spawnSync } from 'node:child_process';
import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const packageRoot = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const [command, ...options] = process.argv.slice(2);

if (!command || ['--help', '-h', 'help'].includes(command)) {
  console.log(`Gantry skill pack installer

Usage: gantry add [skills options]
       gantry --version

Install into the current project:
  npx @julioborges/gantry add
  npx @julioborges/gantry add --agent codex --yes

Install into your user environment:
  npx @julioborges/gantry add --global

List bundled skills without installing:
  npx @julioborges/gantry add --list

Options are passed to the skills CLI. After installation, invoke gantry-setup
inside your coding harness. Runs execute in the harness, not this installer.`);
} else if (['--version', '-v'].includes(command)) {
  console.log(JSON.parse(readFileSync(resolve(packageRoot, 'package.json'), 'utf8')).version);
} else if (command === 'add') {
  const require = createRequire(import.meta.url);
  const skillsRoot = dirname(require.resolve('skills/package.json'));
  const manifest = JSON.parse(readFileSync(resolve(skillsRoot, 'package.json'), 'utf8'));
  const result = spawnSync(process.execPath, [
    resolve(skillsRoot, manifest.bin.skills), 'add', resolve(packageRoot, '.agents/skills'), ...options,
  ], { stdio: 'inherit' });
  if (result.error) {
    console.error(`Gantry installation failed: ${result.error.message}`);
  }
  process.exitCode = result.status ?? 1;
} else {
  console.error(`Unknown command: ${command}. Use gantry --help.`);
  process.exitCode = 1;
}
