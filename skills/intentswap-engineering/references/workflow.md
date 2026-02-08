# Workflow Reference

## Implementation Checklist

1. Confirm scope from user request.
2. Locate affected files with targeted search.
3. Apply minimal patch.
4. Run syntax/tests relevant to modified files.
5. Update docs and assumptions.
6. Return changed file list and validation commands.

## Validation Defaults

```bash
python3 -m py_compile agent/executor.py
node --check scripts/deploy.js
```

Add Solidity compile/tests when contract behavior changes.

## Reporting Template

- Changes made:
- Assumptions:
- Validation run:
- Not run / gaps:
