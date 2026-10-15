"""Controlled Host boundary replies for tests of unrelated workflow behavior.

Technical Plan enforcement itself uses real commands/repositories in test_technical_plan.
"""
COMMAND_REPLIES = r'''
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
