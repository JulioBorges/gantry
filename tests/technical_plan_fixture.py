"""Controlled Host boundary replies for tests of unrelated workflow behavior.

Technical Plan enforcement itself uses real commands/repositories in test_technical_plan.
"""
COMMAND_REPLIES = r'''
  if (command.includes('planning-effort') || (command.includes('technical_plan.py') && command.includes(' evaluate '))) {
    const completed = spawnSync(command, { cwd: options.cwd || args.repoRoot, shell: true, encoding: 'utf8', input: options.input });
    if ((completed.stdout || '').trim()) {
      return { exitCode: completed.status ?? 1, stdout: completed.stdout || '', stderr: completed.stderr || '' };
    }
    // Drivers that point at a nonexistent checkout cannot run the real script.
    // Keep their unrelated assertions moving with the documented high-effort request.
    if (command.includes('planning-effort')) {
      let body = {};
      try { body = JSON.parse(options.input || '{}'); } catch {}
      const selection = { ...(body.selection || {}), effort: 'high' };
      return { exitCode: 0, stdout: JSON.stringify({ stop: false, selection, policy: { intent: 'high', selected: 'high', policy: 'supported-high', observed: null, evidence: 'provider effort unobserved' } }) };
    }
    return { exitCode: completed.status ?? 1, stdout: completed.stdout || '', stderr: completed.stderr || '' };
  }
  if (command.includes('/technical_plan.py')) return {exitCode:0, stdout:JSON.stringify(command.includes(' capture ')
    ? {input:{worktree:options.cwd,revision:'fixture-head',issue:args.issues[0].path,spec:args.issues[0].specPath || 'fixture-spec'}}
    : {accepted:true,artifact:'/fixture/technical-plan.json',conflicts:[]})};
'''
AGENT_REPLY = r'''
  if (options.label.startsWith('technical-plan:')) return {
    input: options.technicalInput,
    findings: [{path:options.technicalInput.issue,line:1,behavior:'Existing fixture behavior'}],
    reuse:['Reuse the fixture boundary'],changes:['Extend the assigned delivery'],
    coverage:options.criterionIndexes.map(index => ({index,changes:['Extend delivery'],tests:['Run fixture gates']})),
    adjustments:[],conflicts:[],
  };
'''
