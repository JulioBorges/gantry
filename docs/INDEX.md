# Documentation Index

## MCP & Playwright Testing

### Quick Start
- **[MCP Quick Reference](./mcp-quick-reference.md)** - At-a-glance guide for developers
  - What is MCP?
  - Configuration overview
  - Common operations
  - Key differences from local testing

### Complete Guides
- **[Playwright MCP Setup](./playwright-mcp-setup.md)** - Comprehensive guide
  - Overview and configuration
  - Requirements (runtime, system)
  - Usage with Claude Code
  - Testing workflows
  - Project rules and requirements
  - Using with Claude API
  - Tool reference
  - Security considerations
  - CI/CD integration

### Troubleshooting
- **[Playwright Troubleshooting](./playwright-troubleshooting.md)** - Problem solving
  - Pre-flight checklist
  - 12+ common issues with solutions
  - Platform-specific guidance (Linux, macOS, Windows)
  - Diagnostic commands
  - Getting help
  - Nuclear recovery option

---

## Project Architecture

### Agent Framework
- **[AGENTS.md](../AGENTS.md)** - Agent capabilities and rules
  - Issue tracking system
  - Roadmap management
  - **Frontend Implementation Testing** - Mandatory Playwright rule

### Product & Decisions
- **[PRD.md](../PRD.md)** - Requirements for Gantry as a skill pack
  - Workflow, gates, guard hooks, dashboard, setup
  - Harness support tiers and acceptance criteria
- **[docs/adr/](./adr/)** - Architecture Decision Records (ADR-0004 explains the pivot from engine to skill pack)
- **[Role Execution & Cross-Harness Guide](./role-execution.md)** - Operator guide for multi-harness execution, discovery, and recovery
- **[Using Gantry](./usage.md)** - Recommended skill workflow and advanced Python CLI reference

### Vocabulary
- **[CONTEXT.md](../CONTEXT.md)** - The glossary (Issue, Spec, Run, Round, Guard Hook, Run Log…)

---

## Getting Started

### For New Team Members
1. Read [MCP Quick Reference](./mcp-quick-reference.md) (5 min)
2. Review [AGENTS.md - Frontend Rule](../AGENTS.md#frontend-implementation-testing) (2 min)
3. Check [CONTEXT.md](../CONTEXT.md) for project overview (10 min)
4. Bookmark [Playwright Troubleshooting](./playwright-troubleshooting.md) for later

### For Frontend Development
1. Make your UI changes
2. Claude will automatically validate with Playwright
3. Review test results in transcript
4. If issues arise: check [Playwright Troubleshooting](./playwright-troubleshooting.md)

### For Integration/DevOps
1. Understand MCP configuration in [/.mcp.json](../.mcp.json)
2. Review [Playwright MCP Setup - CI/CD Integration](./playwright-mcp-setup.md#integration-with-cicd)
3. Follow [Troubleshooting - Diagnostic Commands](./playwright-troubleshooting.md#diagnostic-commands)

---

## Key Files

| File | Purpose |
|------|---------|
| `/.mcp.json` | MCP server configuration (Playwright) |
| `/AGENTS.md` | Agent rules including frontend testing |
| `/PRD.md` | Product requirements |
| `/CONTEXT.md` | Glossary |
| `/docs/playwright-mcp-setup.md` | Complete Playwright guide |
| `/docs/mcp-quick-reference.md` | Quick reference |
| `/docs/playwright-troubleshooting.md` | Problem solving |
| `/docs/role-execution.md` | Role execution and cross-harness operator guide |
| `/docs/usage.md` | Skill-first usage and low-level Python CLI commands |
| `/docs/adr/` | Architecture decisions |

---

## Common Tasks

### "I'm getting an error with Playwright"
→ See [Playwright Troubleshooting](./playwright-troubleshooting.md)

### "How do I test my new React component?"
→ See [Playwright MCP Setup - Testing Frontend Changes](./playwright-mcp-setup.md#testing-frontend-changes)

### "What's required for frontend changes?"
→ See [AGENTS.md - Frontend Implementation Testing](../AGENTS.md#frontend-implementation-testing)

### "How does MCP work?"
→ See [MCP Quick Reference](./mcp-quick-reference.md#what-is-mcp)

### "Can I use Playwright with the Claude API?"
→ See [Playwright MCP Setup - Using with Claude API](./playwright-mcp-setup.md#using-playwright-with-claude-api)

### "What system requirements do I need?"
→ See [Playwright MCP Setup - Requirements](./playwright-mcp-setup.md#requirements)

---

## Organization

```
docs/
├── INDEX.md (this file)
├── playwright-mcp-setup.md
├── mcp-quick-reference.md
├── playwright-troubleshooting.md
└── adr/
    └── (architecture decisions)

.mcp.json (root)
AGENTS.md (root)
PRD.md (root)
CONTEXT.md (root)
```

---

## Updates & Maintenance

**Last Updated:** 2026-09-12 (pivot to skill pack)

Documentation should be updated when:
- MCP configuration changes
- New Playwright features are needed
- Common issues emerge
- Team learnings should be captured

**To Update:**
1. Edit relevant `.md` file
2. Add to git
3. Commit with message describing change
4. Reference issue/spec if applicable

---

## External Resources

- [Playwright Documentation](https://playwright.dev/)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [Claude API Documentation](https://docs.anthropic.com/)
- [Node.js/npm Setup](https://nodejs.org/)

---

## Questions?

1. Check relevant guide above
2. See [Playwright Troubleshooting](./playwright-troubleshooting.md)
3. Check project issues in `.scratch/*/issues/` (created per spec by the `gantry` skill)
4. Review team CONTEXT.md for additional context
