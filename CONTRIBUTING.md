# Contributing to Rigi

Rigi is a personal library. Contributions are accepted in a narrow scope — read this document in full before opening a pull request. PRs that do not meet these requirements will be closed without review.

---

## What we accept

| Type | Accepted |
|---|:---:|
| Bug fixes | ✓ |
| Code optimization / refactoring | ✓ |
| Cross-platform improvements | ✓ |
| Missing Textual feature support | ✓ |
| New terminal / OS compatibility | ✓ |
| Feature requests | ✗ |
| "How do I…" questions | ✗ |
| Documentation additions | ✗ |
| Breaking API changes | ✗ |

We do not accept issues, discussions, or support requests of any kind — those channels are disabled.

---

## Requirements

### Python version

Code must be compatible with **Python 3.10 and above**. Do not use syntax or stdlib features introduced after 3.10.

Use `from __future__ import annotations` at the top of every file that needs it.

### All checks must pass

Every PR must pass all four checks with zero errors before it will be considered:

```bash
ruff check src/ tests/
black --check src/ tests/
pyright src/
pytest tests/
```

Run them locally before pushing:

```bash
# install dev dependencies
pip install -e ".[dev]"

# lint
ruff check src/ tests/

# format check
black --check src/ tests/

# type check
pyright src/

# tests
pytest tests/
```

To auto-fix formatting:

```bash
ruff check src/ tests/ --fix
black src/ tests/
```

### Code style

- Formatted with **black** (`line-length = 100`).
- Linted with **ruff** — all rules in `pyproject.toml` apply.
- Type-checked with **pyright** in strict mode.
- No comments unless the **why** is non-obvious. Never explain what the code does.
- No docstrings on internal/private classes and functions.
- No unused imports, variables, or dead code.
- `from __future__ import annotations` on every file with type hints.

### Tests

- All existing tests must pass.
- New functionality should include tests in `tests/`.
- Tests use `pytest` with `pytest-asyncio` for async Textual tests.
- Do not mock what can be tested directly. Prefer integration-style tests.

---

## Pull request checklist

Before submitting:

- [ ] `ruff check src/ tests/` — no errors
- [ ] `black --check src/ tests/` — no changes needed
- [ ] `pyright src/` — no errors
- [ ] `pytest tests/` — all pass
- [ ] No new comments explaining what the code does
- [ ] No breaking changes to the public API in `src/rigi/__init__.py`
- [ ] PR description explains **what** changed and **why**

---

## Project structure

See the [README](README.md) for the full directory layout and module descriptions.
