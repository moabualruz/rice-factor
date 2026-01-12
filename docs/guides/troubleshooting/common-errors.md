# Common Errors

This guide explains common Rice-Factor errors and how to resolve them.

## Artifact Errors

### "Artifact not found"

**Error:**
```
ArtifactNotFoundError: Artifact abc123 not found
```

**Cause:** The specified artifact ID doesn't exist.

**Solution:**
```bash
# List available artifacts
rice-factor artifact list

# Use the correct ID or path
rice-factor approve <correct-id>
```

### "Artifact is not DRAFT"

**Error:**
```
ArtifactStatusError: Cannot modify artifact - status is APPROVED
```

**Cause:** Trying to edit an approved artifact.

**Solution:**
Generate a new artifact instead:
```bash
rice-factor plan project  # Creates new DRAFT
```

### "Artifact validation failed"

**Error:**
```
ArtifactValidationError: Schema validation failed
  - payload.tests: At least 1 item required
```

**Cause:** Generated artifact doesn't meet schema requirements.

**Solution:**
1. Check your requirements in `.project/`
2. Ensure sufficient context for LLM
3. Re-generate: `rice-factor plan tests`

## Status/Lifecycle Errors

### "TestPlan must be locked"

**Error:**
```
Error: TestPlan must be locked before implementation
```

**Cause:** Trying to implement before locking tests.

**Solution:**
```bash
rice-factor approve <test-plan-id>
rice-factor lock tests
```

### "Cannot lock - artifact is DRAFT"

**Error:**
```
Error: Cannot lock artifact with status DRAFT
```

**Cause:** Trying to lock unapproved artifact.

**Solution:**
```bash
# Approve first
rice-factor approve <id>
# Then lock
rice-factor lock tests
```

### "Cannot execute DRAFT artifact"

**Error:**
```
Error: Cannot execute artifact with status DRAFT
```

**Cause:** Trying to scaffold/implement from unapproved artifact.

**Solution:**
```bash
rice-factor approve <id>
rice-factor scaffold  # Now works
```

## LLM/Provider Errors

### "API key not found"

**Error:**
```
Error: ANTHROPIC_API_KEY not set
```

**Solution:**
```bash
# Set the key
export ANTHROPIC_API_KEY=sk-ant-...

# Verify
echo $ANTHROPIC_API_KEY
```

### "Rate limit exceeded"

**Error:**
```
RateLimitError: Rate limit exceeded. Retry after 60 seconds.
```

**Solution:**
1. Wait and retry
2. Lower rate limits in config:
```yaml
rate_limits:
  claude:
    requests_per_minute: 30
```

### "Model not found"

**Error:**
```
Error: Model 'claude-4-opus' not found
```

**Solution:**
```bash
# List available models
rice-factor models list

# Use correct model name
llm:
  model: claude-3-5-sonnet-20241022
```

### "Connection refused" (Local LLM)

**Error:**
```
ConnectionError: Connection refused to http://localhost:11434
```

**Solution:**
```bash
# Start the server
ollama serve  # or start vLLM

# Verify
curl http://localhost:11434/api/version
```

### "Invalid JSON response"

**Error:**
```
JSONDecodeError: Expecting value at line 1
```

**Cause:** LLM returned non-JSON response.

**Solution:**
1. Try with `--stub` to test workflow
2. Check LLM provider status
3. Try different model

## Workflow/Phase Errors

### "Project not initialized"

**Error:**
```
Error: Not a Rice-Factor project. Run 'rice-factor init' first.
```

**Solution:**
```bash
rice-factor init
```

### "Wrong phase for operation"

**Error:**
```
Error: Cannot scaffold - project is in INIT phase
```

**Cause:** Operation not allowed in current phase.

**Solution:**
Check phase requirements:
```bash
# See current phase
rice-factor artifact list

# Complete required steps first
rice-factor plan project
rice-factor approve <id>
# Then scaffold
```

### "Dependency artifact missing"

**Error:**
```
ArtifactDependencyError: Required artifact ProjectPlan not found
```

**Solution:**
```bash
# Generate the required artifact first
rice-factor plan project
rice-factor approve <id>
```

## Diff/Apply Errors

### "Patch failed to apply"

**Error:**
```
error: patch failed: src/main.py:10
```

**Cause:** Code changed since diff was generated.

**Solution:**
```bash
# Regenerate implementation
rice-factor impl src/main.py
rice-factor review
rice-factor apply
```

### "No pending diffs"

**Error:**
```
Error: No pending diffs to apply
```

**Solution:**
```bash
# Generate a diff first
rice-factor impl src/file.py
rice-factor apply
```

### "Diff already applied"

**Error:**
```
Error: Diff already applied or rejected
```

**Solution:**
Generate a new diff if more changes needed:
```bash
rice-factor impl src/file.py
```

## CI/CD Errors

### "CI validation failed"

**Error:**
```
CI Stage 'artifact_validation' failed
  - 2 artifacts have schema errors
```

**Solution:**
```bash
# Get details
rice-factor ci validate --json | jq '.stages[0].errors'

# Fix the issues locally
rice-factor validate
```

### "Unapproved artifacts in CI"

**Error:**
```
CI Stage 'approval_verification' failed
  - Artifact abc123 is not approved
```

**Solution:**
```bash
# Approve locally
rice-factor approve abc123

# Commit and push
git add .project/artifacts/
git commit -m "Approve artifact"
git push
```

## TUI Errors

### "Terminal too small"

**Error:**
```
Error: Terminal must be at least 80x24
```

**Solution:**
Resize terminal or use CLI instead.

### "Textual not installed"

**Error:**
```
ModuleNotFoundError: No module named 'textual'
```

**Solution:**
```bash
pip install rice-factor[tui]
# or
pip install textual
```

## Getting Help

### Debug Mode

Enable verbose output:
```bash
rice-factor --verbose plan project
```

### Diagnose Command

```bash
rice-factor diagnose
```

### Check Logs

```bash
cat .project/audit/logs/*.log
```

### Report Issues

If the error persists, report it:
1. Enable verbose mode
2. Capture the error
3. Include `.project/` state (sanitized)
4. Open issue on GitHub
