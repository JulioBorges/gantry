#!/usr/bin/env python3
"""Bounded live canonical entry proof; never invokes a role or a provider."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / '.agents/skills/gantry'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host', required=True, help='operator-confirmed active invocation host')
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix='gantry-live-host-entry-') as tmp:
        root = Path(tmp)
        subprocess.run(['git', 'init', '--quiet', str(root)], check=True)
        policy = {'execution': {'hostHarness': 'antigravity', 'roles': {
            'critic': {'harness': 'claude-code', 'model': 'operator-custom', 'effort': 'high'}}},
            'custom': {'preserved': True}, 'budget': {'corrections': 0}}
        path = root / '.gantry/config.json'
        path.parent.mkdir()
        path.write_text(json.dumps(policy))
        before = hashlib.sha256(path.read_bytes()).hexdigest()
        unit = subprocess.check_output(['python3', str(SKILL / 'scripts/runlog.py'), 'unit-id', '--cwd', str(root)], text=True).strip()
        workflow = (SKILL / 'reference/round-workflow.md').read_text().split('```js\n', 1)[1].split('\n```', 1)[0].replace('export const meta', 'const meta', 1)
        invocation = dict(hostHarness=args.host, repoRoot=str(root), skillDir=str(SKILL), policy=policy,
                          paths={}, models={}, round=1, issues=[], isolate=False, branch='entry-proof',
                          runId='run-live-host-entry', unitId=unit, stateRoot=str(root / 'state'), isLastRound=True)
        driver = '''import {spawnSync} from 'node:child_process';
const source = SOURCE;
const args = INVOCATION;
let roleCalls = 0;
const runCommand = async (command, options = {}) => {
  const proc = spawnSync(command, {cwd: options.cwd || args.repoRoot, shell: true, encoding: 'utf8', input: options.input});
  return {exitCode: proc.status ?? 1, stdout: proc.stdout || '', stderr: proc.stderr || ''};
};
const agent = async () => { roleCalls++; throw new Error('This bounded entry proof cannot invoke roles'); };
const parallel = async tasks => Promise.all(tasks.map(task => task()));
const pipeline = async items => { if (items.length) throw new Error('Entry proof requires no Issues'); return []; };
const fn = Object.getPrototypeOf(async function(){}).constructor;
const result = await new fn('args','agent','parallel','pipeline','phase','log','runCommand',source)(args,agent,parallel,pipeline,()=>{},()=>{},runCommand);
process.stdout.write(JSON.stringify({hostResolution:result.hostResolution, roleCalls}));
'''.replace('SOURCE', json.dumps(workflow)).replace('INVOCATION', json.dumps(invocation))
        result = json.loads(subprocess.check_output(['node', '--input-type=module', '--eval', driver], text=True))
        events = [json.loads(line) for line in (root / 'state' / unit / 'runs/run-live-host-entry.jsonl').read_text().splitlines()]
        host = result['hostResolution']
        evidence = {
            'evidenceKind': 'real-canonical-workflow-entry',
            'selectionBoundary': 'operator-confirmed current host; no automatic detection claimed',
            'scope': 'empty round exercises real entry, capabilities and Run lifecycle; role dispatch is not exercised',
            'effectiveHost': host['effectiveHost'], 'savedPreference': host['savedPreference'], 'mismatch': host['mismatch'],
            'tier': host['capabilities']['tier'],
            'provenance': [source for source in host['sources'] if source['kind'] == 'explicit'],
            'policyUnchanged': before == hashlib.sha256(path.read_bytes()).hexdigest(),
            'rolesUnchanged': json.loads(path.read_text())['execution']['roles'] == policy['execution']['roles'],
            'roleInvocations': result['roleCalls'],
            'events': [event['event'] for event in events],
            'recordedHost': events[0]['data']['host'],
        }
        print(json.dumps(evidence, indent=2))
        return 0 if evidence['policyUnchanged'] and evidence['rolesUnchanged'] and evidence['mismatch'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
