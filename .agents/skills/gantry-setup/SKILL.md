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
   - Only an intentional host selection in the proposed policy or `--harness` selects an adapter. Installed binaries, `.agents/`, `.codex/` and inherited environment hints never select adapters.
   - Persist approved hook event names in `hooks.record` and `hooks.deny`. Decision-bearing `PreToolUse` requires explicit denial approval; recording-only approval cannot install its existing denial-capable guard. Recording events such as `PostToolUse` use `hooks.record`.
   - For selected Claude Code or Antigravity, setup reuses the existing pack fragment for approved events only. It preserves unrelated commands, wrapper settings and all other adapters. Capability declarations describe the existing boundary; adapter installation is not live hook compatibility proof.
   - Unrelated repository policy, hook settings and Caveman opt-in are preserved during merges.

5. **Codex Host Harness & Defense in Depth**:
   - Select Codex explicitly through the normal setup conversation or `--harness codex`. Installation hints are not invocation identity.
   - Guide operator to verify authentication (`codex login`) and test model discovery (`discovery.py --harness codex`) before finalizing configuration.
   - Normal setup with `--harness codex` and no config input proposes legacy role defaults and asks approval for the full policy. A supplied config file specifies independent role selections instead. Host-only repair never initializes or replaces roles.
   - Inject Codex-specific orchestration rules (bounded subprocess dispatch via `codex exec`) and defense-in-depth guardrail directives into the marked Gantry policy block in `AGENTS.md`.

6. **Constraints**:
   - Creates no engine, database, MCP service, or automatic cleanup.
   - All setup-generated policy, prompts, and marked content must be English.

7. **Applying the Policy**:
   Write the reviewed JSON to a local file, then pass its path as a structured argument:

   ```bash
   python3 .agents/skills/gantry/scripts/setup.py --config-file /absolute/path/to/proposed-policy.json
   ```

   The script previews the full policy and selected adapter contents before approval. An existing policy
   offers separate merge and overwrite proposals plus abort; a missing policy requires explicit normal
   setup approval. Never interpolate JSON into a shell command or provide synthetic overwrite confirmation.
   When invoking through a tool, pass the executable and arguments as an argument array where available.
   Quotes, dollar signs, backticks and shell metacharacters in configuration remain data.

8. **Host-only Diagnosis and Repair**:
   Diagnose the invocation with `execution.py host --host <operator-confirmed-host> --json`. Automatic
   detection is not verified for the current integrations. The saved preference is shown separately;
   a mismatch does not change roles or tracked policy during a Run.

   ```bash
   python3 .agents/skills/gantry/scripts/setup.py --host-only --host claude-code
   python3 .agents/skills/gantry/scripts/setup.py --host-only --host claude-code --apply
   ```

   The first command previews only. The second still displays the concrete policy and adapter effects
   and asks `Apply this host-only proposal? [y/N]`. Decline, EOF or any answer other than `y`/`yes` writes
   nothing. Unsupported identity, malformed policy or a malformed selected adapter fails before writes.
   `--config`, `--config-file`, `--harness` and `--verify-auth` cannot accompany host-only repair.

   Host-only repair changes `execution.hostHarness` and only Gantry-owned entries in the selected JSON
   adapter, according to existing approved hook policy. It preserves every base/derived role, model,
   effort, execution extension, check, artifact, Caveman preference and unknown field. Policy member bytes
   outside the host value remain intact; adapter bytes outside the hooks value and unrelated hook values
   remain intact. Other adapter files and `AGENTS.md` remain byte-for-byte unchanged. Repetition is a no-op.
   Existing command entries are owned only when they are standalone Python invocations of Gantry's exact
   guard script; unrelated commands mentioning that path or combining additional user actions survive.

   Codex has no native hook events. OpenCode has a declared plugin adapter, but setup does not install or
   rewrite that plugin automatically. Both receive manual workflow and independent Critic guidance without
   fabricated enforcement. Antigravity reuses the existing fragment without expanding its compatibility
   claims or addressing the separate hook compatibility work.

   A missing policy stops host-only repair and directs the operator to the normal setup conversation.
   An ignored policy stops application and prints a tracked-policy migration proposal, including concrete
   `.gitignore` exceptions and staging guidance. The operator reviews effective repository, local and global
   ignore rules; setup never edits ignore rules, relocates state or forces files into Git. After the approved
   migration, repeat diagnosis and preview. See [operator examples](../../../docs/role-execution.md) and the
   [reproducible CLI evidence](../../../docs/evidence/host-harness-resolution/setup-repair.md).
