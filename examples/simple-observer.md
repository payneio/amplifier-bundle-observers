---
bundle:
  name: simple-observer
  version: 0.1.0
  description: Minimal setup with a single code quality observer

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
        timeout_per_observer: 30
        on_timeout: skip
      observers:
        - observer: "@observers:observers/code-quality"
          watch:
            - type: files
              paths:
                - "src/**/*.py"
                - "**/*.py"

tools:
  - module: tool-observations
    source: git+https://github.com/payneio/amplifier-bundle-observers@main#subdirectory=modules/tool-observations
---

# Simple Observer Bundle

Minimal setup with a single code reviewer watching Python files. Good starting point for basic code quality monitoring.

## Usage

```bash
# Register the bundle
amplifier bundle add examples/simple-observer.md --name simple-observer

# Run with it
amplifier run -B simple-observer
```

## What It Does

After each response, the code-quality observer analyzes any Python files that were read or modified during the conversation and surfaces observations about code quality issues.
