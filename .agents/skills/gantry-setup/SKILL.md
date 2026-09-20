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

3. **Caveman Lite Option**:
   - Offer Caveman lite as a recommended, explicitly confirmed repository preference (`"caveman": true`).
   - Explain conversational scope (messages and summaries only; specs, issues, code, contracts, and exact errors retain full detail), user-managed installation, fallback to normal behavior, and variable savings.
   - If declined or skipped, resolve to disabled (`"caveman": false`).
   - When confirmed and Caveman is not installed, guide user with host-harness installation command (`npx skills add caveman` for Claude Code; clone into `~/.gemini/config/skills/caveman` or `.agents/skills/caveman` for Antigravity; `.agents/skills/caveman` for OpenCode/Codex). Gantry runs no installer and changes no global agent configuration.
   - After user reports installation, verify host-harness discovery and readability using `python3 .agents/skills/gantry/scripts/caveman.py check --harness <harness>`.

4. **Role Execution Defaults & Antigravity**:
   - Persist sparse repository role execution defaults under `execution.roles` in `.gantry/config.json`.
   - Each role selection contains `harness`, `model` and optional `effort`.
   - When Antigravity is detected (`.agents/` directory or `agy` CLI on PATH), `setup.py` generates or merges `.agents/hooks.json` to wire `PreToolUse` to `guard.py PreToolUse --json`.
   - Unrelated repository policy, hook settings and Caveman opt-in are preserved during merges.

5. **Codex Host Harness & Defense in Depth**:
   - Detect Codex in environment via `codex` CLI on PATH, `.codex` configuration, or explicit `--harness codex`.
   - Guide operator to verify authentication (`codex login`) and test model discovery (`discovery.py --harness codex`) before finalizing configuration.
   - Configure `execution.hostHarness: "codex"` and role model assignments in `.gantry/config.json`.
   - Inject Codex-specific orchestration rules (bounded subprocess dispatch via `codex exec`) and defense-in-depth guardrail directives into the marked Gantry policy block in `AGENTS.md`.

6. **Constraints**:
   - Creates no engine, database, MCP service, or automatic cleanup.
   - All setup-generated policy, prompts, and marked content must be English.

7. **Applying the Policy**:
   Once the operator confirms the settings, construct the JSON configuration and pipe it to `setup.py`:
   
   ```bash
   python3 .agents/skills/gantry/scripts/setup.py --config '{...}'
   ```
   
   The `setup.py` script renders the full proposed `.gantry/config.json` before writing, supports merge, overwrite, and abort for an existing policy, handles idempotent merging of the Claude Code hook fragment into `.claude/settings.json`, configures `.agents/hooks.json` when Antigravity is detected, supports `--harness codex` with discovery verification, and adds or replaces only the marked Gantry section in `AGENTS.md`. Do not modify these files directly.
