import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import test from 'node:test';
import { registryState, validateRelease, versionFromTag, waitForPublished } from '../scripts/github-release.mjs';

const version = '0.1.1';
const manifest = { name: '@julioborges/gantry', version };
const lock = { version, packages: { '': { version } } };
const commit = 'a'.repeat(40);

test('release validates exact stable version, commit and both lock versions', () => {
  validateRelease(version, commit, manifest, lock);
  for (const invalid of ['v0.1.1', '0.1.1-beta.1', '01.1.1', '', '0.1.1;echo bad']) {
    assert.throws(() => validateRelease(invalid, commit, manifest, lock));
  }
  assert.throws(() => validateRelease(version, 'main', manifest, lock));
  assert.throws(() => validateRelease(version, commit, { ...manifest, version: '0.1.0' }, lock));
  assert.throws(() => validateRelease(version, commit, manifest, { ...lock, packages: {} }));
});

test('only a registry 404 authorizes a new publication', async () => {
  assert.equal(await registryState(version, Buffer.from('tarball'), async () => ({ status: 404 })), false);
  for (const status of [401, 403, 429, 500]) {
    await assert.rejects(registryState(version, Buffer.from('tarball'), async () => ({ status, ok: false })));
  }
  await assert.rejects(registryState(version, Buffer.from('tarball'), async () => { throw new Error('offline'); }));
});

test('retry accepts identical published bytes and rejects an occupied version with different bytes', async () => {
  const tarball = Buffer.from('verified release');
  const integrity = `sha512-${createHash('sha512').update(tarball).digest('base64')}`;
  const request = async () => ({ ok: true, status: 200, json: async () => ({ ...manifest, dist: { integrity } }) });
  assert.equal(await registryState(version, tarball, request), true);
  await assert.rejects(registryState(version, Buffer.from('other release'), request), /differs/);
});

test('version comes from a stable v-prefixed tag and rejects malformed or prerelease tags', () => {
  assert.equal(versionFromTag('v0.1.1'), '0.1.1');
  assert.equal(versionFromTag('v10.20.30'), '10.20.30');
  for (const tag of ['0.1.1', 'v01.1.1', 'v0.1.1-beta.1', 'v0.1.1+build', 'v0.1', 'v0.1.1\n', 'v0.1.1;echo bad', undefined]) {
    assert.throws(() => versionFromTag(tag), /Release tag/);
  }
  assert.throws(() => validateRelease(versionFromTag('v0.1.2'), commit, manifest, lock), /must match/);
});

test('post-publication verification waits for registry propagation, then checks exact integrity', async () => {
  const tarball = Buffer.from('verified release');
  const integrity = `sha512-${createHash('sha512').update(tarball).digest('base64')}`;
  let calls = 0;
  const delays = [];
  const request = async () => ++calls < 3
    ? { status: 404 }
    : { status: 200, ok: true, json: async () => ({ ...manifest, dist: { integrity } }) };
  assert.equal(await waitForPublished(version, tarball, {
    request, attempts: 3, delayMs: 10, sleep: async ms => delays.push(ms),
  }), true);
  assert.equal(calls, 3);
  assert.deepEqual(delays, [10, 10]);
});

test('propagation timeout is bounded and integrity or registry errors are never accepted', async () => {
  let calls = 0;
  await assert.rejects(waitForPublished(version, Buffer.from('release'), {
    request: async () => { calls++; return { status: 404 }; },
    attempts: 3, delayMs: 0, sleep: async () => {},
  }), /missing.*after 3 checks/);
  assert.equal(calls, 3);
  for (const response of [
    { status: 403, ok: false },
    { status: 503, ok: false },
    { status: 200, ok: true, json: async () => ({ ...manifest, dist: { integrity: 'wrong' } }) },
  ]) {
    let delays = 0;
    await assert.rejects(waitForPublished(version, Buffer.from('release'), {
      request: async () => response, sleep: async () => delays++,
    }));
    assert.equal(delays, 0);
  }
});
