---
bundle:
  name: tiered-review
  version: 0.1.0
  description: Two-tier review - fast Haiku scans + deep Sonnet analysis

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
        timeout_per_observer: 60
        on_timeout: skip
      observers:
        # Tier 1: Fast scans with Haiku (default model)
        - observer: "@observers:observers/python-best-practices"
          watch:
            - type: files
              paths: ["**/*.py"]

        - observer: "@observers:observers/error-handling"
          watch:
            - type: files
              paths: ["**/*.py"]

        - observer: "@observers:observers/secrets-scanner"
          watch:
            - type: files
              paths: ["**/*"]

        # Tier 2: Deep analysis with Sonnet (override model)
        - observer: "@observers:observers/security-auditor"
          model: claude-sonnet-4-20250514
          watch:
            - type: files
              paths: ["src/**/*.py"]
            - type: conversation
              include_tool_calls: true

        - observer: "@observers:observers/architecture-reviewer"
          model: claude-sonnet-4-20250514
          watch:
            - type: conversation
              include_tool_calls: true
              include_reasoning: true

tools:
  - module: tool-observations
    source: git+https://github.com/payneio/amplifier-bundle-observers@main#subdirectory=modules/tool-observations
---

# Tiered Review Bundle

Two-tier review: multiple fast Haiku observers + deep Sonnet analysis. Cost-effective approach that catches issues quickly while providing thorough analysis where it matters.

## Usage

```bash
amplifier bundle add examples/tiered-review.md --name tiered-review
amplifier run -B tiered-review
```

## Tiers

**Tier 1 (Fast - Haiku):**
| Observer | Focus |
|----------|-------|
| python-best-practices | PEP 8, idioms, common mistakes |
| error-handling | Exception handling, edge cases |
| secrets-scanner | Hardcoded credentials |

**Tier 2 (Deep - Sonnet):**
| Observer | Focus |
|----------|-------|
| security-auditor | Security vulnerabilities, attack vectors |
| architecture-reviewer | Design patterns, system structure |

## Why Tiered?

- Fast observers catch obvious issues cheaply
- Expensive model reserved for complex analysis
- Better cost/quality tradeoff than all-Sonnet
