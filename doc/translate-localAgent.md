# Current local-agent assignment

## TASK-001 — XHTML core and PDF adapter boundary

Read the existing source in src/doctranslate/translate.py and the repository plan in doc/translate-testingRules.md.

Implement only phase 1 under src/doctranslate/. Keep the existing command-line workflow functional. Introduce a small, dependency-light internal XHTML document contract with source metadata and explicit adapter protocols/interfaces for input and output. Move only the smallest safe pieces needed to make translation orchestration depend on the contract rather than directly on PDF-specific operations. Preserve existing behavior; do not rewrite the entire translator.

Allowed files:

- src/doctranslate/translate.py
- new focused Python modules under src/doctranslate/translate_core/
- new focused tests under `test/`

Forbidden:

- changing or deleting user PDF/HTML/JSON artifacts;
- modifying the nested `doctranslate/` repository;
- model installation, network calls, or Git commits;
- broad formatting-only rewrites.

Required validation:

- python -m py_compile src/doctranslate/translate.py src/doctranslate/translate_core/*.py
- run focused unit tests if added;
- ensure imports work without an Ollama server.

Respond with exactly: `TASK-001: <short validation result>`.


## Outcome

The task was not executed by the local agent. Two Native Qwen3-Coder starts failed before any tool call because qwen-worker.ps1 invokes cn serve, while the installed Continue CLI has no serve command. Codex implemented the bounded phase directly after documenting the fallback.

Independent validation:
- py_compile passed for src/doctranslate modules.
- 4 unittest tests passed.
- translate.cmd --help passed.
- git diff --check passed.
