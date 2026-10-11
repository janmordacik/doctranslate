status: done
last change: 2026-10-11
type: feature
group: ai/ollama/observability/context
dependency: 2-2026-10-11-ollama-context-length
description: Do not assume a fixed VRAM size or force the model maximum context by default. Discover model and runner capabilities through Ollama API and log the effective values for diagnosing truncated responses.

Plan and estimates:
- S01: Make context override optional and leave automatic resource-aware selection to Ollama by default. Estimate: 10 minutes, 35 logical lines, 500 tokens. Dependencies: none.
- S02: Query /api/tags and /api/ps and log model size, supported context, runtime context and VRAM allocation. Estimate: 15 minutes, 70 logical lines, 900 tokens. Dependencies: S01.
- S03: Update tests and documentation. Estimate: 10 minutes, 40 logical lines, 500 tokens. Dependencies: S01, S02.

Acceptance:
- No fixed 32 GB VRAM assumption exists in context selection.
- Model metadata is obtained through Ollama API, not by scanning model files.
- Runtime diagnostics log requested, supported and actual context values plus model and VRAM sizes when reported.
- Default requests do not force a context larger than Ollama's resource-aware choice.
- An explicit ollama_context_length override remains supported.

comments:
- 2026-10-11: Implemented optional context override, Ollama API capability probing and runtime logging. A live smoke test with an explicit num_ctx=131072 showed that the API reports runtime context_length=131072. The production default is now automatic instead of hardcoded.
