# Host-only setup repair CLI evidence

This is deterministic public CLI evidence from temporary Git repositories. It proves policy and
adapter proposal/application behavior. It is not automatic invocation detection or live hook
compatibility evidence. No adopting repository, real host adapter or tracked policy was mutated.
Automated stdin below models operator answers only inside the temporary fixture; it is not permission
to supply approval on an operator's behalf during actual setup.

Reproduce from the repository root:

```bash
python3 docs/evidence/host-harness-resolution/setup-repair-transcript.py
python3 -m unittest tests.test_host_setup_repair tests.test_gantry_setup tests.test_role_execution_defaults tests.test_guard_hook_wiring -v
```

The reproduction script uses only standard library subprocess argument arrays and isolated temporary
Git repositories. All policy text, including shell metacharacters, stays data. It asserts exact
policy bytes outside the changed host value, full role/custom field preservation, unrelated user hook
commands, unchanged other adapter bytes, no shell execution, safe cancellation and idempotence.
Additional public CLI tests exercise base and derived roles, malformed policy/adapters, duplicate
JSON keys, unsupported and unresolved identities, CRLF/Unicode formatting, normal setup approval for
missing policy, structured config-file input, and recording-only versus explicit denial decisions.

## Red/green implementation evidence

Each behavior was developed through the approved public setup CLI seam before its implementation:

- Initial host-only preview/preservation test failed with `unrecognized arguments: --host-only --host claude-code`; adding the host-only proposal and explicit approval path made it pass.
- Ignored-policy application test failed with `2 != 0`; adding a tracked-policy migration proposal and stopping before writes made it pass.
- Normal-setup adapter-selection test failed because `.claude/settings.json` was created without a chosen host; removing installation/directory routing made it pass.
- Malformed policy tests exposed normal overwrite accepting unsupported saved identity and malformed role/hook containers; shared structural validation made those paths fail closed.
- Unrelated command ownership test showed `echo "skills/gantry/scripts/guard.py"` and a compound user action removed; exact standalone Python invocation matching preserved them.
- Recording-only approval test required explicit guidance that `PreToolUse` needs denial opt-in; guidance was added without installing denial-capable wiring.
- CRLF preservation test exposed newline normalization; byte decoding for the policy and adapter input retained original line endings.

Existing setup regressions now select Claude Code/Antigravity and denial events intentionally rather
than asserting installation heuristics. They retain their original merge, exact-byte idempotence,
unrelated-setting and command-wiring assertions. Static pack inventories include `setup_host.py` and
continue inspecting every script's imports against standard library and explicit pack modules.

## Validation

The full standard-library suite passed: `python3 -m unittest discover -v` ran 354 tests in 98.943s,
with `OK`. The focused setup/guard seam passed 45 tests, including 11 host-only repair tests.
Required delivery gates are run against the committed revision before Implementer handoff;
Reviewer and Critic must independently verify acceptance and gates.

Required gates passed at `70589c4a7392c7c1fbd773e19221e2d1ddc46664` using Issue diff base
`c0778b6bd4c8e4167d285efec5038a3538573eeb`: executed Python `test` and npm `pack:check` both exited 0.
A subsequent wording-only correction removed an inaccurate ignore-precedence adjective in migration
guidance and regenerated this transcript. The ignored-policy CLI test and full transcript reproduction
passed again for that correction. These earlier broad gates are not represented as latest-revision gates;
the fresh Critic independently runs all gates against the delivered revision.

## Captured reproduction transcript

### Read-only preview

```text
$ python3 setup.py --host-only --host claude-code
stdin: EOF (no approval)
Host diagnosis:
{
  "status": "resolved",
  "effectiveHost": "claude-code",
  "savedPreference": "antigravity",
  "mismatch": true,
  "sources": [
    {
      "source": "policy:execution.hostHarness",
      "kind": "preference",
      "host": "antigravity"
    },
    {
      "source": "invocation:explicit-selection",
      "kind": "explicit",
      "host": "claude-code"
    }
  ],
  "diagnostics": [
    "Operator-selected invocation identity; automatic detection was not verified."
  ]
}
Proposed .gantry/config.json:
{
  "execution": {
    "hostHarness": "claude-code",
    "roles": {
      "implement": {
        "harness": "codex",
        "model": "custom implement",
        "effort": "medium"
      },
      "critic": {
        "harness": "claude-code",
        "model": "custom critic",
        "effort": "high"
      },
      "learner": {
        "harness": "opencode",
        "model": "custom learner"
      }
    },
    "custom": "$(touch NEVER); `touch NEVER`; \"quoted\""
  },
  "hooks": {
    "record": [
      "PostToolUse"
    ],
    "deny": []
  },
  "caveman": true,
  "unknown": {
    "keep": 1
  }
}

claude-code: selected adapter .claude/settings.json; approved wired events: PostToolUse. Existing capability declaration only; wiring is not live hook proof.
Proposed adapter effects:
.claude/settings.json
{
  "user" : "unchanged",
  "hooks": {
  "PreToolUse": [
    {
      "matcher": "Read",
      "hooks": [
        {
          "type": "command",
          "command": "echo user"
        }
      ]
    }
  ],
  "PostToolUse": [
    {
      "matcher": "*",
      "hooks": [
        {
          "type": "command",
          "command": "python3 \"$CLAUDE_PROJECT_DIR/.agents/skills/gantry/scripts/guard.py\" PostToolUse --cwd \"$CLAUDE_PROJECT_DIR\""
        }
      ]
    }
  ]
}
}

Files to change: .claude/settings.json, .gantry/config.json
All role selections and unrelated policy are preserved. AGENTS.md is unchanged.
Preview only. To apply, repeat with --apply and explicitly approve this proposal.
Exit: 0
```

### Explicit decline

```text
$ python3 setup.py --host-only --host claude-code --apply
stdin: 'n\n'
Host diagnosis:
{
  "status": "resolved",
  "effectiveHost": "claude-code",
  "savedPreference": "antigravity",
  "mismatch": true,
  "sources": [
    {
      "source": "policy:execution.hostHarness",
      "kind": "preference",
      "host": "antigravity"
    },
    {
      "source": "invocation:explicit-selection",
      "kind": "explicit",
      "host": "claude-code"
    }
  ],
  "diagnostics": [
    "Operator-selected invocation identity; automatic detection was not verified."
  ]
}
Proposed .gantry/config.json:
{
  "execution": {
    "hostHarness": "claude-code",
    "roles": {
      "implement": {
        "harness": "codex",
        "model": "custom implement",
        "effort": "medium"
      },
      "critic": {
        "harness": "claude-code",
        "model": "custom critic",
        "effort": "high"
      },
      "learner": {
        "harness": "opencode",
        "model": "custom learner"
      }
    },
    "custom": "$(touch NEVER); `touch NEVER`; \"quoted\""
  },
  "hooks": {
    "record": [
      "PostToolUse"
    ],
    "deny": []
  },
  "caveman": true,
  "unknown": {
    "keep": 1
  }
}

claude-code: selected adapter .claude/settings.json; approved wired events: PostToolUse. Existing capability declaration only; wiring is not live hook proof.
Proposed adapter effects:
.claude/settings.json
{
  "user" : "unchanged",
  "hooks": {
  "PreToolUse": [
    {
      "matcher": "Read",
      "hooks": [
        {
          "type": "command",
          "command": "echo user"
        }
      ]
    }
  ],
  "PostToolUse": [
    {
      "matcher": "*",
      "hooks": [
        {
          "type": "command",
          "command": "python3 \"$CLAUDE_PROJECT_DIR/.agents/skills/gantry/scripts/guard.py\" PostToolUse --cwd \"$CLAUDE_PROJECT_DIR\""
        }
      ]
    }
  ]
}
}

Files to change: .claude/settings.json, .gantry/config.json
All role selections and unrelated policy are preserved. AGENTS.md is unchanged.
Apply this host-only proposal? [y/N] Aborted. No files changed.
Exit: 1
```

### EOF cancellation

```text
$ python3 setup.py --host-only --host claude-code --apply
stdin: EOF (no approval)
Host diagnosis:
{
  "status": "resolved",
  "effectiveHost": "claude-code",
  "savedPreference": "antigravity",
  "mismatch": true,
  "sources": [
    {
      "source": "policy:execution.hostHarness",
      "kind": "preference",
      "host": "antigravity"
    },
    {
      "source": "invocation:explicit-selection",
      "kind": "explicit",
      "host": "claude-code"
    }
  ],
  "diagnostics": [
    "Operator-selected invocation identity; automatic detection was not verified."
  ]
}
Proposed .gantry/config.json:
{
  "execution": {
    "hostHarness": "claude-code",
    "roles": {
      "implement": {
        "harness": "codex",
        "model": "custom implement",
        "effort": "medium"
      },
      "critic": {
        "harness": "claude-code",
        "model": "custom critic",
        "effort": "high"
      },
      "learner": {
        "harness": "opencode",
        "model": "custom learner"
      }
    },
    "custom": "$(touch NEVER); `touch NEVER`; \"quoted\""
  },
  "hooks": {
    "record": [
      "PostToolUse"
    ],
    "deny": []
  },
  "caveman": true,
  "unknown": {
    "keep": 1
  }
}

claude-code: selected adapter .claude/settings.json; approved wired events: PostToolUse. Existing capability declaration only; wiring is not live hook proof.
Proposed adapter effects:
.claude/settings.json
{
  "user" : "unchanged",
  "hooks": {
  "PreToolUse": [
    {
      "matcher": "Read",
      "hooks": [
        {
          "type": "command",
          "command": "echo user"
        }
      ]
    }
  ],
  "PostToolUse": [
    {
      "matcher": "*",
      "hooks": [
        {
          "type": "command",
          "command": "python3 \"$CLAUDE_PROJECT_DIR/.agents/skills/gantry/scripts/guard.py\" PostToolUse --cwd \"$CLAUDE_PROJECT_DIR\""
        }
      ]
    }
  ]
}
}

Files to change: .claude/settings.json, .gantry/config.json
All role selections and unrelated policy are preserved. AGENTS.md is unchanged.
Apply this host-only proposal? [y/N] Aborted. No files changed.
Exit: 1
```

### Approved host-only repair

```text
$ python3 setup.py --host-only --host claude-code --apply
stdin: 'y\n'
Host diagnosis:
{
  "status": "resolved",
  "effectiveHost": "claude-code",
  "savedPreference": "antigravity",
  "mismatch": true,
  "sources": [
    {
      "source": "policy:execution.hostHarness",
      "kind": "preference",
      "host": "antigravity"
    },
    {
      "source": "invocation:explicit-selection",
      "kind": "explicit",
      "host": "claude-code"
    }
  ],
  "diagnostics": [
    "Operator-selected invocation identity; automatic detection was not verified."
  ]
}
Proposed .gantry/config.json:
{
  "execution": {
    "hostHarness": "claude-code",
    "roles": {
      "implement": {
        "harness": "codex",
        "model": "custom implement",
        "effort": "medium"
      },
      "critic": {
        "harness": "claude-code",
        "model": "custom critic",
        "effort": "high"
      },
      "learner": {
        "harness": "opencode",
        "model": "custom learner"
      }
    },
    "custom": "$(touch NEVER); `touch NEVER`; \"quoted\""
  },
  "hooks": {
    "record": [
      "PostToolUse"
    ],
    "deny": []
  },
  "caveman": true,
  "unknown": {
    "keep": 1
  }
}

claude-code: selected adapter .claude/settings.json; approved wired events: PostToolUse. Existing capability declaration only; wiring is not live hook proof.
Proposed adapter effects:
.claude/settings.json
{
  "user" : "unchanged",
  "hooks": {
  "PreToolUse": [
    {
      "matcher": "Read",
      "hooks": [
        {
          "type": "command",
          "command": "echo user"
        }
      ]
    }
  ],
  "PostToolUse": [
    {
      "matcher": "*",
      "hooks": [
        {
          "type": "command",
          "command": "python3 \"$CLAUDE_PROJECT_DIR/.agents/skills/gantry/scripts/guard.py\" PostToolUse --cwd \"$CLAUDE_PROJECT_DIR\""
        }
      ]
    }
  ]
}
}

Files to change: .claude/settings.json, .gantry/config.json
All role selections and unrelated policy are preserved. AGENTS.md is unchanged.
Apply this host-only proposal? [y/N] Applied approved host-only proposal.
Exit: 0
```

### Idempotent approved repetition

```text
$ python3 setup.py --host-only --host claude-code --apply
stdin: 'yes\n'
Host diagnosis:
{
  "status": "resolved",
  "effectiveHost": "claude-code",
  "savedPreference": "claude-code",
  "mismatch": false,
  "sources": [
    {
      "source": "policy:execution.hostHarness",
      "kind": "preference",
      "host": "claude-code"
    },
    {
      "source": "invocation:explicit-selection",
      "kind": "explicit",
      "host": "claude-code"
    }
  ],
  "diagnostics": [
    "Operator-selected invocation identity; automatic detection was not verified."
  ]
}
Proposed .gantry/config.json:
{
  "execution": {
    "hostHarness": "claude-code",
    "roles": {
      "implement": {
        "harness": "codex",
        "model": "custom implement",
        "effort": "medium"
      },
      "critic": {
        "harness": "claude-code",
        "model": "custom critic",
        "effort": "high"
      },
      "learner": {
        "harness": "opencode",
        "model": "custom learner"
      }
    },
    "custom": "$(touch NEVER); `touch NEVER`; \"quoted\""
  },
  "hooks": {
    "record": [
      "PostToolUse"
    ],
    "deny": []
  },
  "caveman": true,
  "unknown": {
    "keep": 1
  }
}

claude-code: selected adapter .claude/settings.json; approved wired events: PostToolUse. Existing capability declaration only; wiring is not live hook proof.
Proposed adapter effects:
Files to change: none (already matches)
All role selections and unrelated policy are preserved. AGENTS.md is unchanged.
Apply this host-only proposal? [y/N] Applied approved host-only proposal.
Exit: 0
```

Preservation assertions: all role/custom fields, policy bytes outside host, user command, other adapter bytes, no shell execution and repeated bytes PASS.

### Unsupported automatic adapter wiring

```text
$ python3 setup.py --host-only --host codex
stdin: EOF (no approval)
Host diagnosis:
{
  "status": "resolved",
  "effectiveHost": "codex",
  "savedPreference": "claude-code",
  "mismatch": true,
  "sources": [
    {
      "source": "policy:execution.hostHarness",
      "kind": "preference",
      "host": "claude-code"
    },
    {
      "source": "invocation:explicit-selection",
      "kind": "explicit",
      "host": "codex"
    }
  ],
  "diagnostics": [
    "Operator-selected invocation identity; automatic detection was not verified."
  ]
}
Proposed .gantry/config.json:
{
  "execution": {
    "hostHarness": "codex",
    "roles": {
      "implement": {
        "harness": "codex",
        "model": "custom implement",
        "effort": "medium"
      },
      "critic": {
        "harness": "claude-code",
        "model": "custom critic",
        "effort": "high"
      },
      "learner": {
        "harness": "opencode",
        "model": "custom learner"
      }
    },
    "custom": "$(touch NEVER); `touch NEVER`; \"quoted\""
  },
  "hooks": {
    "record": [
      "PostToolUse"
    ],
    "deny": []
  },
  "caveman": true,
  "unknown": {
    "keep": 1
  }
}

codex: no verified automatic setup wiring for this adapter. Use manual workflow rules and independent Critic verification; no native enforcement was installed.
Proposed adapter effects:
Files to change: .gantry/config.json
All role selections and unrelated policy are preserved. AGENTS.md is unchanged.
Preview only. To apply, repeat with --apply and explicitly approve this proposal.
Exit: 0
```

### Ignored policy migration proposal

```text
$ python3 setup.py --host-only --host claude-code --apply
stdin: 'y\n'
Host diagnosis:
{
  "status": "resolved",
  "effectiveHost": "claude-code",
  "savedPreference": "claude-code",
  "mismatch": false,
  "sources": [
    {
      "source": "policy:execution.hostHarness",
      "kind": "preference",
      "host": "claude-code"
    },
    {
      "source": "invocation:explicit-selection",
      "kind": "explicit",
      "host": "claude-code"
    }
  ],
  "diagnostics": [
    "Operator-selected invocation identity; automatic detection was not verified."
  ]
}
Tracked-policy migration proposal:
Review the effective ignore rules. For repository ignore rules, append these exceptions to .gitignore:
!.gantry/
.gantry/*
!.gantry/config.json
If policy is still ignored, inspect repository, .git/info/exclude and global rules and repair the effective rule explicitly.
Then verify with git check-ignore .gantry/config.json and stage with git add .gantry/config.json.
Keep credentials and transient state outside tracked policy. No ignore rules or policy were changed.
Exit: 2
```

Ignored-policy assertions: ignore rules and all policy/adapter bytes unchanged PASS.

### Missing policy requires normal setup approval

```text
$ python3 setup.py --host-only --host claude-code --apply
stdin: 'y\n'
Host diagnosis:
{
  "status": "resolved",
  "effectiveHost": "claude-code",
  "savedPreference": null,
  "mismatch": false,
  "sources": [
    {
      "source": "invocation:explicit-selection",
      "kind": "explicit",
      "host": "claude-code"
    }
  ],
  "diagnostics": [
    "Operator-selected invocation identity; automatic detection was not verified."
  ]
}
Missing repository policy. Use normal gantry-setup with --config-file and approve the full policy before host-only repair. No policy was synthesized.
Exit: 2
```
