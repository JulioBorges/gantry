# Gantry

**Deterministic, harness-agnostic autonomous software factory with SQLite telemetry and context watermark handoffs.**

Gantry is a planned open-source factory operated by a coding harness: approved specs become vertical slices implemented in isolated worktrees, checked against repository quality rules, and integrated through the configured Git workflow. The harness coordinates agents; Gantry validates operations and evidence through a shared CLI, MCP, and dashboard core. Codex and OpenCode are the initial validation targets, including execution across both harnesses.

The Gantry engine uses TypeScript and Node.js and is distributed through npm, so the intended entry point is `npx gantry`. Initial repository adapters target TypeScript/JavaScript and Python projects. Git integration supports local Git and GitHub Pull Requests through `gh`, targeting GitHub.com and GitHub Enterprise; Windows support is expected and remains pending validation.

Named after the [gantry crane](https://en.wikipedia.org/wiki/Gantry_crane): it doesn't lift the cargo itself — it provides the rails, the structure, and the automation so every piece lands in the right place, at the right time.

> **Project status:** requirements and domain documentation. Implementation contracts and the initial support matrix are still being defined; described commands are planned behavior.

---

## Why Gantry?

Agentic coding tools fail in predictable ways. Gantry is designed around the five critical bottlenecks of "vibe coding":

| Bottleneck | Gantry's answer |
|---|---|
| **Context growth** | Default 40% handoff watermark, with monitoring and interruption limited to verified integration capabilities |
| **Horizontal slicing** | Verifiable vertical slices with an estimated complete initial context budget of 15%; no mandatory file-count or test-duration cutoff |
| **Architectural debt** | An entropy gate compares configured check evidence against the current target, blocking new or aggravated problems while preserving absolute rules |
| **AppSec risks** | Explicit repository security and dependency checks with declared coverage and structured evidence |
| **Provider lock-in** | Role routing through validated native harness, detached CLI, or approved gateway integrations |

The principle: **Agents + Code > Agents Alone.** Deterministic code owns the rails; agents own the cognition.

## Design references

- [`PRD.md`](./PRD.md) — full product requirements and architecture

## License

[Apache License 2.0](./LICENSE)
