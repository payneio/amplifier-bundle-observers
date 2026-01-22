---
bundle:
  name: multi-observer
  version: 0.1.0
  description: Multiple specialized observers for comprehensive code review

includes:
  - bundle: git+https://github.com/microsoft/amplifier-foundation@main
  - bundle: git+https://github.com/payneio/amplifier-bundle-observers@main

hooks:
  - module: hooks-observations
    source: git+https://github.com/payneio/amplifier-bundle-observers@main#subdirectory=modules/hooks-observations
    config:
      hooks:
        - trigger: "orchestrator:complete"
          priority: 5
      execution:
        mode: parallel_sync
        max_concurrent: 5
        timeout_per_observer: 45
        on_timeout: skip
      observers:
        - observer: "@observers:observers/security-auditor"
          watch:
            - type: files
              paths: ["src/**/*.py"]
            - type: conversation
              include_tool_calls: true

        - observer: "@observers:observers/secrets-scanner"
          watch:
            - type: files
              paths: ["**/*.py", "**/*.yaml", "**/*.json", "**/*.env*"]

        - observer: "@observers:observers/performance-reviewer"
          watch:
            - type: files
              paths: ["src/**/*.py"]

        - observer: "@observers:observers/test-quality"
          watch:
            - type: files
              paths: ["src/**/*.py", "tests/**/*.py"]

        - observer: "@observers:observers/logic-checker"
          watch:
            - type: conversation
              include_tool_calls: true
              include_reasoning: true

tools:
  - module: tool-observations
    source: git+https://github.com/payneio/amplifier-bundle-observers@main#subdirectory=modules/tool-observations
---

# Multi-Observer Bundle

Multiple specialized observers running in parallel for comprehensive review. Each observer focuses on a specific aspect of code quality.

## Usage

```bash
amplifier bundle add examples/multi-observer.md --name multi-observer
amplifier run -B multi-observer
```

## Observers

| Observer | Focus |
|----------|-------|
| security-auditor | Security vulnerabilities, injection attacks |
| secrets-scanner | Hardcoded credentials, API keys |
| performance-reviewer | Performance issues, inefficiencies |
| test-quality | Test coverage and quality |
| logic-checker | Logical errors and reasoning flaws |
