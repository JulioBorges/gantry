# Playwright MCP Configuration

## Overview

The Gantry project is configured with the [Playwright MCP Server](https://github.com/modelcontextprotocol/servers/tree/main/src/playwright), enabling automated browser testing, E2E testing, and visual validation for frontend changes.

This configuration is **harness-agnostic**, meaning it works with any MCP-compatible client:
- Claude Code (CLI, Desktop, VS Code extension)
- Claude API with MCP support
- Any other MCP-compatible harness

## Configuration File

**Location:** `/.mcp.json`

```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["@modelcontextprotocol/server-playwright"],
      "description": "Playwright MCP Server - Browser automation and E2E testing"
    }
  }
}
```

This file:
- ✅ Is versionable (checked into git)
- ✅ Is shared across the team
- ✅ Works with any harness supporting MCP
- ✅ Requires no additional local configuration

## Requirements

### Runtime Dependencies
- **Node.js 18+** - Required to run Playwright
- **npm** - For executing `npx @modelcontextprotocol/server-playwright`
- **Chromium/Firefox/WebKit** - Installed automatically by Playwright on first use

### System Requirements
- **Linux**: Most distributions work; WSL2 recommended for Windows
- **macOS**: 10.14+ with Xcode Command Line Tools
- **Windows**: Windows 10+ with [WSL2](https://learn.microsoft.com/en-us/windows/wsl/install) recommended

## Using Playwright with Claude Code

### Initial Setup

1. **Ensure Node.js is installed:**
   ```bash
   node --version  # Should be 18+
   npm --version
   ```

2. **The Playwright MCP will auto-activate** when:
   - You modify frontend code
   - You request browser testing
   - You ask Claude to validate UI changes

3. **First run:** Playwright downloads browser binaries (~300MB total)
   ```bash
   # Manual trigger to cache browsers:
   npx @modelcontextprotocol/server-playwright --help
   ```

### Testing Frontend Changes

When you modify UI code, Claude will automatically:

1. **Detect frontend changes** from your edits
2. **Use Playwright to test** the implementation
3. **Validate** rendering, interactions, and responsiveness
4. **Report results** in the transcript

### Common Workflows

#### Testing a React Component
```
You: "Create a login form component"
↓
Claude creates the component
↓
Claude uses Playwright to:
  - Render the component
  - Test form input/submission
  - Validate error handling
  - Check accessibility
↓
Reports test results
```

#### Visual Regression Testing
```
You: "Update the button styling"
↓
Claude modifies the CSS
↓
Claude uses Playwright to:
  - Take screenshots before/after
  - Verify responsive behavior
  - Check different viewport sizes
  - Validate hover/focus states
↓
Reports visual changes
```

#### E2E Testing
```
You: "Add a user login flow"
↓
Claude implements authentication
↓
Claude uses Playwright to:
  - Navigate through login page
  - Fill forms
  - Verify redirects
  - Check session state
↓
Reports flow validation
```

## Project Rules

**Rule from AGENTS.md:**
> Any changes to frontend code MUST be validated with Playwright before marking work complete.

### What Triggers Testing
- Modified or created UI components, pages, or layouts
- Updated styling, responsive design, or CSS
- Changed form interactions, validation, or user flows
- Added or modified interactive elements
- Updated accessibility features or ARIA attributes

### What Gets Verified
- ✅ Component renders without errors
- ✅ User interactions work as specified
- ✅ Responsive behavior on multiple screen sizes
- ✅ Form submissions and validation flow
- ✅ Accessibility compliance (keyboard navigation, screen reader compat)
- ✅ Visual consistency with design specs

### Exceptions
Purely non-visual changes (utility functions, business logic without UI impact) don't require Playwright testing.

## Using Playwright with Claude API

If using the Claude API directly with MCP:

```python
import anthropic

client = anthropic.Anthropic()

response = client.messages.create(
    model="claude-opus-5",
    max_tokens=4096,
    tools=[
        {
            "type": "mcp",
            "name": "playwright",
            "uri": "mcp://localhost:3000",  # Or configured MCP endpoint
        }
    ],
    messages=[
        {
            "role": "user",
            "content": "Test the login form for accessibility"
        }
    ]
)
```

**Note:** MCP server configuration depends on your deployment setup.

## Using Playwright with Other Harnesses

The `.mcp.json` file is a standard MCP configuration that any compatible harness can use:

1. **Read** the `.mcp.json` file
2. **Launch** the MCP server using the configured command
3. **Connect** Claude to the server
4. **Execute** Playwright tools as available

Specific implementation varies by harness. Consult your harness documentation for MCP integration steps.

## Playwright Tools Available

Once connected, these Playwright capabilities are available:

| Tool | Purpose |
|------|---------|
| `browser.launch()` | Start a new browser instance |
| `page.navigate()` | Navigate to a URL |
| `page.click()` | Click elements |
| `page.fill()` | Fill form inputs |
| `page.screenshot()` | Capture page screenshots |
| `page.waitForSelector()` | Wait for elements |
| `page.evaluate()` | Execute JavaScript in page context |
| `page.accessibility.snapshot()` | Get accessibility tree |

See [Playwright API Documentation](https://playwright.dev/docs/api/class-page) for complete reference.

## Troubleshooting

### "Playwright not found"
```bash
npm install -g @modelcontextprotocol/server-playwright
# Or let it auto-install via npx (recommended)
```

### "Browser installation failed"
```bash
# Manually install browsers
npx playwright install
```

### "Connection refused"
- Ensure Node.js is running
- Check that port isn't in use
- Verify `.mcp.json` path is correct

### "Timeout waiting for browser"
- Increase timeout settings in your harness
- Check system resources (memory, disk)
- Try restarting the MCP server

### "Security/Sandbox issues"
Some systems require special privileges:

**Linux/WSL2:**
```bash
sudo apt-get install libxss1 libgconf-2-4
```

**macOS:**
```bash
# If prompted about security:
xcode-select --install
```

## Performance Tips

1. **Reuse browser instances** where possible
2. **Run tests in parallel** for independent validations
3. **Cache screenshots** to avoid re-rendering
4. **Use headless mode** (default) for speed
5. **Target specific elements** with precise selectors

## Security Considerations

- ✅ Playwright runs in a sandboxed browser context
- ✅ No access to system files outside project
- ✅ Network requests can be monitored/controlled
- ✅ Sensitive data should not appear in screenshots

**Best Practices:**
- Don't test with real credentials in public logs
- Use test data and fixtures
- Review screenshot content before committing
- Sanitize sensitive information in test output

## Integration with CI/CD

For automated testing pipelines:

```yaml
# Example GitHub Actions
- name: Run Playwright MCP Tests
  run: |
    npm install
    npx @modelcontextprotocol/server-playwright --version
    # Claude will use Playwright for frontend validation
```

## Further Reading

- [Playwright Documentation](https://playwright.dev/)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [Claude API with MCP](https://docs.anthropic.com/en/docs/build-a-system-with-claude/tool-use)
- [AGENTS.md](../AGENTS.md) - Gantry agent rules and frontend testing requirements

## Questions?

Refer to:
- Project issue tracker (`.scratch/*/issues/`)
- Team documentation (`docs/adr/`)
- Context specification (`CONTEXT.md`)
