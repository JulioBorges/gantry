import assert from 'node:assert/strict';
import test from 'node:test';
import { ensureNpmAuthor } from '../scripts/ensure-npm-author.mjs';

test('allows only the authenticated npm author on npmjs.org', () => {
  ensureNpmAuthor((command, args, options) => {
    assert.ok(command);
    assert.deepEqual(args.slice(-3), ['whoami', '--registry', 'https://registry.npmjs.org/']);
    assert.equal(options.timeout, 30_000);
    return { status: 0, stdout: 'julioborges\n' };
  });
});

test('blocks other users, empty identity and lookalike account names', () => {
  for (const stdout of ['another-user', '', 'julioborges-other', 'Julioborges']) {
    assert.throws(() => ensureNpmAuthor(() => ({ status: 0, stdout })), /only npm account julioborges/);
  }
});

test('fails closed on authentication, network and process failures', () => {
  for (const result of [
    { status: 1, stdout: 'julioborges' },
    { status: null, stdout: '', error: new Error('timeout') },
    { status: null, error: new Error('missing npm') },
  ]) {
    assert.throws(() => ensureNpmAuthor(() => result), /could not verify/);
  }
});
