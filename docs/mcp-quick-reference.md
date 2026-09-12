# MCP Quick Reference

## What is MCP?

**Model Context Protocol** enables AI assistants to use tools and resources from configured servers. Gantry configures Playwright as an MCP server for browser automation.

## Configuration

**File:** `/.mcp.json`

Defines available MCP servers. Currently includes:
- **playwright** - Browser automation and testing

## How It Works

```
Your prompt
    ↓
Harness (Claude Code, API, etc.)
    ↓
Reads /.mcp.json
    ↓
Launches: npx @modelcontextprotocol/server-playwright
    ↓
Claude uses Playwright tools
    ↓
Browser automation happens
    ↓
Results returned to Claude
```

## Using with Claude Code

### Automatic Activation
No setup needed! Claude automatically detects and uses Playwright when:
- Working on frontend code
- Testing UI changes
- Validating accessibility

### Manual Invocation
```
You: "Test the login form with Playwright"
Claude: [Uses Playwright tools to test]
```

### Requirements
- Node.js 18+
- npm (for npx)
- Internet (first run downloads ~300MB of browsers)

## Using with Claude API

Configure your MCP endpoint in your Claude client:

```python
tools=[
    {
        "type": "mcp",
        "name": "playwright",
        "uri": "mcp://your-mcp-server"
    }
]
```

## Supported Operations

### Navigation
```
- page.goto(url)
- page.navigate(url)
- page.goBack()
- page.goForward()
```

### Interaction
```
- page.click(selector)
- page.fill(selector, text)
- page.type(selector, text)
- page.select(selector, option)
- page.press(key)
```

### Inspection
```
- page.screenshot()
- page.content()
- page.url()
- page.title()
```

### Validation
```
- page.waitForSelector(selector)
- page.isVisible(selector)
- page.textContent(selector)
- page.getAttribute(selector, name)
- page.accessibility.snapshot()
```

## Project Rules

**Mandatory:** Frontend changes must be validated with Playwright.

Applies to:
- ✅ New/modified UI components
- ✅ Styling changes
- ✅ Form interactions
- ✅ Interactive elements
- ✅ Accessibility updates

Exception: Pure logic (no UI impact)

## Common Issues

| Issue | Solution |
|-------|----------|
| "Command not found: npx" | Install Node.js 18+ |
| "Browser not found" | Run `npx playwright install` |
| "Connection refused" | Check MCP server is running |
| "Timeout" | Increase timeout or check system resources |

## Key Differences from Local Testing

| Local Testing | Playwright MCP |
|---|---|
| Manual browser setup | Automatic via MCP |
| Manual interaction | Claude automates |
| Manual validation | Integrated with Claude |
| Human-readable logs | Structured tool results |

## Resources

- **Full Guide:** [playwright-mcp-setup.md](./playwright-mcp-setup.md)
- **Project Rules:** [../AGENTS.md](../AGENTS.md#frontend-implementation-testing)
- **Playwright Docs:** https://playwright.dev/
- **MCP Spec:** https://modelcontextprotocol.io/

## At a Glance

```
Configure:    /.mcp.json
Launch:       npx @modelcontextprotocol/server-playwright
Used by:      Claude automatically on frontend changes
Validates:    Components, interactions, accessibility, responsiveness
Reports:      Test results in transcript
```
