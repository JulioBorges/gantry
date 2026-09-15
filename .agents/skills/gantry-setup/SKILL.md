---
name: gantry-setup
description: Conversational repository setup. The sole writer of repository policy and its marked AGENTS.md section.
---

# Gantry Setup

You are the sole conversational writer of repository policy.

1. **Present Decisions**: Present each artifact, template, check, Git, and hook decision to the operator.
   - For each decision, provide its benefit, trade-off, default, and confirmation.
   - Preserves pack defaults when skipped.

2. **Capabilities & Hooks**:
   - Reads capability declarations (from `.agents/skills/gantry/capabilities/*.json`) to offer only supported hook choices.
   - Enables recording by default.
   - Asks before denial hooks.

3. **Constraints**:
   - Creates no engine, database, MCP service, or automatic cleanup.
   - All setup-generated policy, prompts, and marked content must be English.

4. **Applying the Policy**:
   Once the operator confirms the settings, construct the JSON configuration and pipe it to `setup.py`:
   
   ```bash
   python3 .agents/skills/gantry/scripts/setup.py --config '{...}'
   ```
   
   The `setup.py` script renders the full proposed `.gantry/config.json` before writing, supports merge, overwrite, and abort for an existing policy, handles idempotent merging of the Claude Code hook fragment into `.claude/settings.json`, and adds or replaces only the marked Gantry section in `AGENTS.md`. Do not modify these files directly.
