---
bundle:
  name: full-stack-review
  version: 0.1.0
  description: Comprehensive review for full-stack web development

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
        max_concurrent: 8
        timeout_per_observer: 45
        on_timeout: skip
      observers:
        # Backend (Python)
        - observer: "@observers:observers/python-best-practices"
          watch:
            - type: files
              paths: ["**/*.py"]

        - observer: "@observers:observers/async-patterns"
          watch:
            - type: files
              paths: ["**/*.py"]

        # Frontend (TypeScript/React)
        - observer: "@observers:observers/typescript-reviewer"
          watch:
            - type: files
              paths: ["**/*.ts", "**/*.tsx"]

        - observer: "@observers:observers/react-reviewer"
          watch:
            - type: files
              paths: ["**/*.tsx", "**/*.jsx"]

        # Database
        - observer: "@observers:observers/sql-reviewer"
          watch:
            - type: files
              paths: ["**/*.py", "**/*.sql"]

        # API Design
        - observer: "@observers:observers/api-design"
          watch:
            - type: files
              paths: ["**/routes/**", "**/api/**", "**/*.py"]

        # Security (all code)
        - observer: "@observers:observers/security-auditor"
          model: claude-sonnet-4-20250514
          watch:
            - type: files
              paths: ["**/*"]

        # Accessibility (frontend)
        - observer: "@observers:observers/accessibility-checker"
          watch:
            - type: files
              paths: ["**/*.tsx", "**/*.jsx", "**/*.html"]

        # Config and DevOps
        - observer: "@observers:observers/config-reviewer"
          watch:
            - type: files
              paths:
                - "**/*.yaml"
                - "**/*.yml"
                - "**/*.json"
                - "**/*.toml"
                - "**/Dockerfile"
                - "**/.env*"

tools:
  - module: tool-observations
    source: git+https://github.com/payneio/amplifier-bundle-observers@main#subdirectory=modules/tool-observations
---

# Full-Stack Review Bundle

Comprehensive review for full-stack web development. Covers Python backend, TypeScript/React frontend, SQL, APIs, and infrastructure.

## Usage

```bash
amplifier bundle add examples/full-stack-review.md --name full-stack-review
amplifier run -B full-stack-review
```

## Observers

| Layer | Observer | Focus |
|-------|----------|-------|
| **Backend** | python-best-practices | PEP 8, idioms, patterns |
| | async-patterns | Async/await correctness |
| **Frontend** | typescript-reviewer | TS best practices, types |
| | react-reviewer | React patterns, hooks |
| **Database** | sql-reviewer | Query optimization, N+1 |
| **API** | api-design | REST/GraphQL conventions |
| **Security** | security-auditor | Vulnerabilities (Sonnet) |
| **A11y** | accessibility-checker | WCAG compliance |
| **DevOps** | config-reviewer | Config best practices |

## Best For

- Full-stack web applications
- Projects with Python backend + React frontend
- Teams wanting comprehensive automated review
