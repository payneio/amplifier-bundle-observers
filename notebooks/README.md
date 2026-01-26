# Bundle Composition Debug Notebooks

This directory contains interactive Python notebooks for debugging and understanding Amplifier bundle composition behavior.

## Setup

The notebooks directory has its own isolated virtual environment:

```bash
cd notebooks

# Activate the environment
source .venv/bin/activate

# Dependencies are already installed (jupyter, pyyaml)
# To reinstall: uv pip install -r requirements.txt
```

## Available Notebooks

### `bundle-composition-debug.ipynb`

Interactive investigation of the systems-thinking bundle composition issue.

**What it demonstrates:**
- How `deep_merge()` handles dicts vs lists
- How `merge_module_lists()` combines module configs
- Bundle composition order (who wins when configs conflict)
- Why sub-bundles including their root creates problems
- Extracting and inspecting session mount plans

**How to run:**

```bash
source .venv/bin/activate
jupyter notebook bundle-composition-debug.ipynb
```

Then execute cells in order (Shift+Enter) to walk through the investigation.

## What You'll Learn

By the end of the notebook, you'll understand:

1. ✅ Deep merge and module merging work correctly (they're not the bug)
2. ✅ Composition order is correct (last bundle wins)
3. ❌ Sub-bundle including its root creates loading/caching issues
4. ✓ The fix: Don't include root from sub-bundles; declare modules directly

## Troubleshooting

**ModuleNotFoundError: amplifier_foundation**

The notebook auto-detects the foundation cache directory. If it fails:

```python
# Manually add foundation to path
import sys
from pathlib import Path

foundation_dir = Path.home() / ".amplifier/cache/amplifier-foundation-<hash>"
sys.path.insert(0, str(foundation_dir))
```

**Session not found**

Update the `session_id` variable in Test 8 to point to your target session.
