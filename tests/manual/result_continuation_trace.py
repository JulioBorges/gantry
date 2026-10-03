"""Opt-in bounded live Codex Critic trace; never part of automatic tests."""
import datetime
import json
from pathlib import Path
import subprocess
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tests.test_result_continuation import ResultContinuationTests
from tests.test_canonical_gantry_workflow import parse_issue

with tempfile.TemporaryDirectory() as temp:
    root = Path(temp) / 'repo'
    helper, issue, args = ResultContinuationTests().fixture(root)
    args.update(statusDuringWait=True, liveCritic={'harness':'codex','model':'gpt-6.1-sol','effort':'medium'},liveTimeout=180)
    out = helper.run_workflow('round-workflow.md',args)
    events = helper.read_run_log_events(Path(args['stateRoot']),args['unitId'],args['runId'])
    trace = {'kind':'bounded-real-role-canonical-host-driver', 'date':datetime.datetime.now(datetime.timezone.utc).isoformat(),
             'hostDriver':'Node canonical workflow adapter; conversational status steering simulated',
             'roleSelection':args['liveCritic'], 'timeoutSeconds':180,'error':out['error'],
             'outcome':out['result']['results'][0]['outcome'] if out['result'] else None,
             'issueStatus':parse_issue(issue).status,
             'branch':subprocess.check_output(['git','branch','--show-current'],cwd=root,text=True).strip(),
             'clean':not subprocess.check_output(['git','status','--porcelain'],cwd=root,text=True).strip(),
             'statusReplies':out['statusReplies'],
             'events':[{'event':e['event'],'role':e.get('data',{}).get('role'),'status':e.get('data',{}).get('status'),'ts':e['ts']} for e in events],
             'limitations':['Only the Critic invocation is real; Implement/Review and conversational status steering are fixtures.',
                            'No daemon or continuation after closing Host is claimed.',
                            'Requested model/effort does not prove server-side identity.']}
    target = Path(__file__).resolve().parents[2] / 'docs/evidence/run-execution-reliability/issue03-bounded-trace-second.json'
    target.write_text(json.dumps(trace,indent=2)+'\n')
    print(json.dumps({k:trace[k] for k in ['outcome','issueStatus','clean','error']}))
