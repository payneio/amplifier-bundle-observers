---
bundle:
  name: writing-review
  version: 0.1.0
  description: Observers for written content quality - documentation, emails, reports

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
        max_concurrent: 4
        timeout_per_observer: 45
        on_timeout: skip
      observers:
        - observer: "@observers:observers/writing-quality"
          watch:
            - type: conversation
              include_reasoning: true

        - observer: "@observers:observers/communication-reviewer"
          watch:
            - type: conversation
              include_reasoning: true

        - observer: "@observers:observers/argument-analyzer"
          watch:
            - type: conversation
              include_reasoning: true

        - observer: "@observers:observers/simplicity-guardian"
          watch:
            - type: conversation
              include_reasoning: true

tools:
  - module: tool-observations
    source: git+https://github.com/payneio/amplifier-bundle-observers@main#subdirectory=modules/tool-observations
---

# Writing Review Bundle

Observers focused on written content quality. Useful for documentation, emails, reports, and communications.

## Usage

```bash
amplifier bundle add examples/writing-review.md --name writing-review
amplifier run -B writing-review
```

## Observers

| Observer | Focus |
|----------|-------|
| writing-quality | Clarity, structure, grammar, tone |
| communication-reviewer | Message effectiveness, audience fit |
| argument-analyzer | Logical structure, evidence, persuasion |
| simplicity-guardian | Unnecessary complexity, jargon, verbosity |

## Try It

Draft an email or document and ask for feedback:

> "Review this announcement for our team about the new deployment process..."

The observers will analyze your writing for clarity, effectiveness, and potential improvements.
