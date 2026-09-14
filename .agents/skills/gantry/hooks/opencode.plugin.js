// Gantry guard hook wiring for OpenCode.
//
// Per ADR-0003, this plugin never decides whether work is ready or done; it forwards
// each declared event to `guard.py <event>` with the event payload on standard input
// and applies only the decision guard.py returns (allow or deny) to `tool.execute.before`.
// `session.compacted` is a record-only event: guard.py's exit code is ignored and it is
// always allowed to proceed, because compaction has already happened by the time the
// event fires.
"use strict";

const { spawnSync } = require("node:child_process");
const path = require("node:path");

function skillDir() {
  return path.resolve(__dirname, "..");
}

function runGuard(event, payload, projectDir) {
  const script = path.join(skillDir(), "scripts", "guard.py");
  const result = spawnSync("python3", [script, event, "--cwd", projectDir || process.cwd()], {
    input: JSON.stringify(payload || {}),
    encoding: "utf8",
  });
  return {
    allow: result.status === 0,
    message: (result.stdout || result.stderr || "").trim(),
  };
}

module.exports = ({ project } = {}) => {
  const projectDir = (project && project.directory) || process.cwd();
  return {
    "tool.execute.before": async (input, output) => {
      const payload = { ...(output || {}), ...(input || {}) };
      const decision = runGuard("tool.execute.before", payload, projectDir);
      if (!decision.allow) {
        throw new Error(`gantry guard: ${decision.message || "denied by a protected rule"}`);
      }
    },
    "session.compacted": async (input, output) => {
      runGuard("session.compacted", { ...(output || {}), ...(input || {}) }, projectDir);
    },
  };
};
