---
bundle:
  name: shadow-observer-test
  version: 0.1.0
  description: Shadow environment test bundle for observer validation

includes:
  - bundle: git+https://github.com/microsoft/amplifier-foundation@main

# Note: In the shadow environment, the amplifier-bundle-observers package
# is installed with entry points. The module names below are discovered
# via entry points (amplifier.modules group in pyproject.toml).

tools:
  - module: tool-observations
    config: {}

hooks:
  - module: hooks-observations
    config:
      hooks:
        - trigger: "orchestrator:complete"
          priority: 5

      execution:
        mode: parallel_sync
        max_concurrent: 2
        timeout_per_observer: 45
        on_timeout: skip

      observers:
        # Single observer using Haiku for fast, cheap testing
        - name: "Code Quality Scanner"
          role: "Scan code for bugs, security issues, and bad practices"
          focus: |
            Look for these specific issues:
            - Security vulnerabilities (SQL injection, code injection, hardcoded secrets)
            - Missing error handling (uncaught exceptions, no validation)
            - Resource leaks (unclosed files, connections)
            - Logic errors (division by zero, off-by-one)
            - Bad practices (bare except, mutable defaults, global state)
            - Unused imports
            
            Report each issue as a separate observation with appropriate severity:
            - critical: Security vulnerabilities, data exposure
            - high: Logic errors that cause crashes, resource leaks
            - medium: Bad practices, missing validation
            - low: Style issues, minor inefficiencies
          model: "claude-3-5-haiku-latest"
          timeout: 30
          watch:
            - type: files
              paths:
                - "**/*.py"
          metadata:
            purpose: "shadow-test"
            tier: "fast"

  - module: hooks-observations-display
    config:
      style: compact
      show_on_create: true
      show_on_resolve: true
---

# Shadow Test Bundle

This bundle is designed to run in a shadow environment for testing the observer system.

## What It Tests

1. **tool-observations**: State management for observations (CRUD operations)
2. **hooks-observations**: Observer orchestration and change detection
3. **hooks-observations-display**: Visualization of observation status

## Observer Configuration

A single "Code Quality Scanner" observer using Haiku that looks for:
- Security vulnerabilities
- Missing error handling
- Resource leaks
- Logic errors
- Bad practices

## Test Instructions

1. Start amplifier with this bundle in the shadow environment
2. Copy the buggy_code.py file to the workspace
3. Ask the agent to "review the code in buggy_code.py"
4. Observer should trigger and create observations
5. Use `observations list` to see the findings
