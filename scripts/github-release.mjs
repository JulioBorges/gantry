import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';

const packageName = '@julioborges/gantry';

export function validateRelease(version, commit, manifest, lock) {
  if (!/^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$/.test(version || '')) {
    throw new Error('Release requires a stable x.y.z version without a v prefix.');
  }
  if (!/^[a-f0-9]{40}$/.test(commit || '')) throw new Error('Release requires a full commit SHA.');
  if (manifest.name !== packageName || manifest.version !== version ||
      lock.version !== version || lock.packages?.['']?.version !== version) {
    throw new Error('Release version must match package.json and package-lock.json.');
  }
}

export async function registryState(version, tarball, request = fetch) {
  const response = await request(`https://registry.npmjs.org/${encodeURIComponent(packageName)}/${version}`, {
    signal: AbortSignal.timeout(30_000),
  });
  if (response.status === 404) return false;
  if (!response.ok) throw new Error(`Registry verification failed: HTTP ${response.status}`);
  const metadata = await response.json();
  const integrity = `sha512-${createHash('sha512').update(tarball).digest('base64')}`;
  if (metadata.name !== packageName || metadata.version !== version || metadata.dist?.integrity !== integrity) {
    throw new Error('Published version differs from the verified tarball; refusing to overwrite or tag it.');
  }
  return true;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  try {
    const version = process.env.RELEASE_VERSION;
    validateRelease(version, process.env.RELEASE_COMMIT,
      JSON.parse(readFileSync('package.json')), JSON.parse(readFileSync('package-lock.json')));
    const mode = process.argv[2];
    if (mode !== 'validate') {
      if (!['registry', 'verify'].includes(mode)) throw new Error('Unknown release check.');
      const tarball = readFileSync(join(process.env.RUNNER_TEMP, 'release', `julioborges-gantry-${version}.tgz`));
      const published = await registryState(version, tarball);
      if (mode === 'verify' && !published) throw new Error('Published package is missing from the registry.');
      console.log(`published=${published}`);
    }
  } catch (error) {
    console.error(error.message);
    process.exitCode = 1;
  }
}
