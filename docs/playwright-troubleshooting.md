# Playwright MCP Troubleshooting Guide

## Pre-Flight Checklist

Before troubleshooting, verify:

```bash
# 1. Node.js is installed and version is 18+
node --version

# 2. npm is available
npm --version

# 3. Test MCP server directly
npx @modelcontextprotocol/server-playwright --help
```

---

## Common Issues and Solutions

### Issue: "Cannot find module '@modelcontextprotocol/server-playwright'"

**Symptom:** Error when Claude tries to use Playwright

**Causes:**
- Node.js not installed
- npm installation corrupted
- Network issue during package download

**Solutions:**

1. **Verify Node.js installation:**
   ```bash
   node --version  # Should be v18.0.0 or higher
   ```
   If not installed: https://nodejs.org/

2. **Clear npm cache and retry:**
   ```bash
   npm cache clean --force
   npx @modelcontextprotocol/server-playwright --help
   ```

3. **Install globally as fallback:**
   ```bash
   npm install -g @modelcontextprotocol/server-playwright
   ```

4. **Check npm registry connectivity:**
   ```bash
   npm ping
   ```

---

### Issue: "Playwright browser not found"

**Symptom:** "Failed to launch browser" or "Browser executable not found"

**Causes:**
- Browsers not downloaded yet
- Playwright cache corrupted
- Insufficient disk space

**Solutions:**

1. **Install browsers explicitly:**
   ```bash
   npx playwright install
   npx playwright install chromium  # For specific browser
   ```

2. **Clear and reinstall:**
   ```bash
   npx playwright install --with-deps
   ```

3. **Check disk space:**
   ```bash
   df -h  # Linux/Mac
   dir %USERPROFILE%\AppData\Local  # Windows
   # Playwright needs ~300-500MB
   ```

4. **Verify installation:**
   ```bash
   npx playwright --version
   npx playwright codegen  # Opens browser to verify
   ```

---

### Issue: "Timeout waiting for browser to launch"

**Symptom:** Test runs but hangs waiting for browser

**Causes:**
- System running low on memory
- Browser process taking too long to start
- Too many concurrent browser instances

**Solutions:**

1. **Check available memory:**
   ```bash
   free -h      # Linux
   top -l 1     # Mac (press q to exit)
   tasklist     # Windows
   ```

2. **Close unnecessary applications** to free RAM

3. **Increase timeout in harness configuration:**
   - Claude Code: Increase in session settings
   - API: Set `timeout: 30000` (30 seconds)

4. **Use single browser instance:**
   - Reuse browser context instead of creating new one
   - Reduces startup overhead

5. **Restart harness:**
   ```bash
   # For Claude Code, restart the session
   # For API, reconnect the MCP server
   ```

---

### Issue: "Permission denied" or "EACCES" errors

**Symptom:** "Error: spawn EACCES" or "Permission denied while launching browser"

**Platforms:** Primarily Linux/WSL2

**Causes:**
- Missing system dependencies
- Incorrect file permissions
- Running in restricted environment

**Solutions:**

1. **Install system dependencies (Ubuntu/Debian):**
   ```bash
   sudo apt-get update
   sudo apt-get install -y \
     libglib2.0-0 \
     libgconf-2-4 \
     libx11-6 \
     libxss1 \
     libxtst6 \
     libxrandr2 \
     fonts-liberation \
     libappindicator1 \
     libindicator7 \
     xdg-utils
   ```

2. **Install dependencies for Chromium specifically:**
   ```bash
   npx playwright install-deps chromium
   ```

3. **Fix file permissions:**
   ```bash
   chmod +x ~/.cache/ms-playwright/chromium-*/chrome-linux/chrome
   ```

4. **WSL2 specific setup:**
   ```bash
   # Install required packages
   sudo apt-get install -y xvfb
   
   # Run with headless display
   Xvfb :99 -screen 0 1024x768x24 &
   export DISPLAY=:99
   ```

---

### Issue: "SANDBOX error" or "SUID Sandbox disabled"

**Symptom:** Browser launches but crashes with security warnings

**Causes:**
- Sandbox not available in environment
- Running in Docker/container without proper setup
- User permissions too restrictive

**Solutions:**

1. **Run without sandbox (development only):**
   ```bash
   # Not recommended for production
   npx playwright launch --disable-blink-features=AutomationControlled
   ```

2. **Docker setup (if containerized):**
   ```dockerfile
   FROM node:18
   RUN apt-get update && apt-get install -y \
     libglib2.0-0 libgconf-2-4 libx11-6 libxss1 \
     libxtst6 libxrandr2 fonts-liberation libappindicator1
   RUN npx playwright install
   ```

3. **macOS security prompt:**
   If prompted "Cannot be opened because the developer cannot be verified":
   ```bash
   xattr -d com.apple.quarantine ~/.cache/ms-playwright/chromium-*/
   ```

---

### Issue: "Port already in use" or "Connection refused"

**Symptom:** Cannot connect to MCP server

**Causes:**
- MCP server already running on same port
- Firewall blocking connection
- Previous instance not cleaned up

**Solutions:**

1. **Find process using port:**
   ```bash
   # Linux/Mac
   lsof -i :3000  # Change 3000 to your port
   
   # Windows
   netstat -ano | findstr :3000
   ```

2. **Kill existing process:**
   ```bash
   # Linux/Mac
   kill -9 <PID>
   
   # Windows
   taskkill /PID <PID> /F
   ```

3. **Restart harness and MCP server:**
   - Exit Claude Code session
   - Wait 5 seconds
   - Restart session
   - MCP will reinitialize

4. **Use different port:**
   Configure in `.mcp.json` if needed (advanced)

---

### Issue: "Blank page" or "Navigation timeout"

**Symptom:** Page loads but is blank or takes too long

**Causes:**
- Network connectivity issue
- Site requires authentication
- JavaScript not executing
- Server not responding

**Solutions:**

1. **Verify URL is accessible:**
   ```bash
   curl -I https://example.com
   ```

2. **Increase wait time:**
   ```
   page.goto(url, { waitUntil: 'networkidle', timeout: 60000 })
   ```

3. **Check if authentication needed:**
   - Add headers/cookies to request
   - Use page.context() to manage auth

4. **Enable JavaScript debugging:**
   ```
   page.on('console', msg => console.log(msg.text()))
   ```

5. **Check browser console for errors:**
   ```
   logs = page.context().console_messages
   ```

---

### Issue: "Element not found" or "Selector timeout"

**Symptom:** "Waiting for selector to match" takes forever or fails

**Causes:**
- Wrong selector syntax
- Element not yet rendered
- Element hidden/invisible
- Iframe containing element

**Solutions:**

1. **Verify selector works:**
   ```bash
   npx playwright codegen
   # Interactively test selectors
   ```

2. **Add explicit wait:**
   ```
   page.waitForLoadState('networkidle')
   page.waitForSelector('#my-button', { timeout: 5000 })
   ```

3. **Check for iframe:**
   ```
   frame = page.frameLocator('[name="myframe"]')
   element = frame.locator('#button-in-iframe')
   ```

4. **Use more specific selector:**
   ```
   # Bad: 'button'
   # Better: 'button[type="submit"]'
   # Best: 'button:has-text("Login")'
   ```

5. **Verify element visibility:**
   ```
   is_visible = page.locator('#element').is_visible()
   ```

---

### Issue: "Screenshot is black" or "Screenshot empty"

**Symptom:** Screenshots captured but show black/blank images

**Causes:**
- Page not fully loaded
- Element not visible
- Rendering issues
- Headless mode limitations

**Solutions:**

1. **Wait for page load:**
   ```
   page.goto(url)
   page.waitForLoadState('networkidle')
   page.screenshot()
   ```

2. **Wait for element:**
   ```
   page.waitForSelector('#content')
   page.screenshot()
   ```

3. **Add delay for rendering:**
   ```
   page.waitForTimeout(1000)  # 1 second
   page.screenshot()
   ```

4. **Increase viewport size:**
   ```
   browser.newContext(viewport={'width': 1920, 'height': 1080})
   ```

5. **Check if video mode helps:**
   Enable recording to debug visually

---

### Issue: "Accessibility snapshot fails" or "No accessibility tree"

**Symptom:** Accessibility validation returns empty or errors

**Causes:**
- Page structure not semantic
- JavaScript errors prevent tree generation
- Page completely inaccessible

**Solutions:**

1. **Verify page loads correctly:**
   ```bash
   npx playwright codegen
   # Check page visually before testing a11y
   ```

2. **Check for JavaScript errors:**
   ```
   errors = []
   page.on('pageerror', lambda err: errors.append(err))
   page.goto(url)
   # Review errors list
   ```

3. **Validate HTML structure:**
   - Use proper semantic HTML
   - Ensure all inputs have labels
   - Use ARIA attributes correctly

4. **Try with different browser:**
   ```bash
   npx playwright install firefox
   npx playwright codegen --browser=firefox
   ```

---

## Diagnostic Commands

Use these to gather information for debugging:

```bash
# System info
node --version
npm --version
uname -a          # Linux/Mac
systeminfo        # Windows

# Playwright info
npx playwright --version
npx playwright codegen  # Interactive test

# Network
ping google.com
curl -I https://example.com

# Memory/Process
ps aux | grep node         # Linux/Mac
tasklist | findstr node    # Windows

# Cache info
npm cache verify
npx playwright install --list-browsers
```

---

## Getting Help

If issue persists:

1. **Check logs:**
   - Claude transcript
   - Browser console
   - System logs

2. **Enable debug logging:**
   ```bash
   DEBUG=pw:api npx @modelcontextprotocol/server-playwright
   ```

3. **Report to team:**
   - Create issue in `.scratch/*/issues/`
   - Include error message
   - Include diagnostic command output
   - Describe steps to reproduce

4. **External resources:**
   - [Playwright GitHub Issues](https://github.com/microsoft/playwright/issues)
   - [Playwright Docs - Troubleshooting](https://playwright.dev/docs/troubleshooting)
   - [MCP Protocol Docs](https://modelcontextprotocol.io/)

---

## Quick Recovery

**"Nuclear option" - Start fresh:**

```bash
# 1. Clear all caches
npm cache clean --force

# 2. Reinstall Playwright
npx playwright install --with-deps

# 3. Test
npx playwright --version
npx playwright codegen

# 4. Restart harness
# Exit Claude Code completely
# Restart session
```

This resolves ~90% of issues. Use only if other solutions fail.
