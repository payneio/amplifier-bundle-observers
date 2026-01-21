# Shadow Environment Testing

This directory contains resources for testing the observer bundle in an isolated shadow environment.

## What's Here

| File | Purpose |
|------|---------|
| `shadow-test-bundle.md` | Bundle configuration for shadow testing |
| `buggy_code.py` | Intentionally buggy Python code to trigger observations |
| `README.md` | This file |

## Running the Shadow Test

### Prerequisites

- Amplifier CLI installed (`uv tool install amplifier`)
- Shadow bundle available (included in foundation)
- API key for Anthropic (for the Haiku observer)

### Option 1: Using Amplifier Session (Recommended)

Start an Amplifier session and ask it to run the shadow test:

```
Run the shadow test for amplifier-bundle-observers:
1. Create a shadow with local source from /path/to/amplifier-bundle-observers
2. Install the package and set up the test bundle
3. Copy buggy_code.py and have an agent review it
4. Verify observations are created
```

### Option 2: Manual Shadow Setup

1. **Create the shadow environment:**
   ```bash
   # From an Amplifier session, use the shadow tool:
   shadow(operation="create", local_sources=[
       "/path/to/amplifier-bundle-observers:microsoft/amplifier-bundle-observers"
   ])
   ```

2. **Set up inside the shadow:**
   ```bash
   # Install amplifier
   shadow exec <id> "uv tool install git+https://github.com/microsoft/amplifier"
   
   # Clone the repo (uses local snapshot via git rewriting)
   shadow exec <id> "cd /workspace && git clone https://github.com/microsoft/amplifier-bundle-observers"
   
   # Install the package with amplifier
   shadow exec <id> "uv tool install --force git+https://github.com/microsoft/amplifier \
       --with file:///workspace/amplifier-bundle-observers"
   
   # Install providers
   shadow exec <id> "amplifier provider install -q"
   ```

3. **Register the test bundle:**
   ```bash
   shadow exec <id> "amplifier bundle add \
       /workspace/amplifier-bundle-observers/tests/shadow/shadow-test-bundle.md \
       --name shadow-test"
   ```

4. **Run the test:**
   ```bash
   shadow exec <id> "cd /workspace && amplifier run -B shadow-test --mode single \
       'Review the code in amplifier-bundle-observers/tests/shadow/buggy_code.py and identify all issues'"
   ```

5. **Check observations:**
   ```bash
   shadow exec <id> "amplifier run -B shadow-test --mode single 'observations list'"
   ```

## Expected Results

The `buggy_code.py` file contains intentional issues that observers should catch:

| Category | Issues |
|----------|--------|
| **Security** | SQL injection, code injection (eval), hardcoded credentials |
| **Error Handling** | Missing file error handling, bare except, division by zero risk |
| **Resource Leaks** | Unclosed file handle |
| **Bad Practices** | Global mutable state, unused imports, wildcard import |

A successful test run should:
1. Spawn the "Code Quality Scanner" observer
2. Analyze the buggy code
3. Create multiple observations with appropriate severities
4. Display observations via the hooks-observations-display module

## Troubleshooting

### Observer doesn't spawn
- Check that the hooks-observations module is loaded (`amplifier module list`)
- Verify the `orchestrator:complete` trigger is configured

### No observations created
- Check observer logs for errors
- Verify API key is available in the shadow environment
- Increase observer timeout if it's timing out

### Module not found errors
- Ensure the package is installed with the amplifier tool environment
- Check entry points: `python -c "import importlib.metadata; print(list(importlib.metadata.entry_points(group='amplifier.modules')))"`
