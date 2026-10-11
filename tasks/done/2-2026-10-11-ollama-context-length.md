status: done
last change: 2026-10-11
type: feature
group: ai/ollama/context
dependency: 1-2026-10-11-ollama-response-pipe-deadlock
description: Initial experiment for explicit Ollama context sizing. The experiment established that the model supports 131072 and that the worker runner can be configured to use it; the production default was later changed to automatic resource-aware Ollama selection.

Plan and estimates:
- S01: Configure the worker-owned Ollama server and every chat request with an explicit context length. Estimate: 10 minutes, 45 logical lines, 600 tokens. Dependencies: none.
- S02: Add payload and composition regression assertions. Estimate: 5 minutes, 20 logical lines, 300 tokens. Dependencies: S01.

Acceptance:
- Worker-owned Ollama accepts an explicit OLLAMA_CONTEXT_LENGTH override.
- Ollama requests include options.num_ctx when an override is configured.
- Job translator_options can override ollama_context_length.
- Existing request and provider tests pass.

comments:
- 2026-10-11: Local Ollama reported translategemma:4b context support 131072. The worker-owned runner had previously used 32768; explicit server and request configuration was implemented. This does not guarantee that a model will produce valid JSON, so output-size-aware batching remains a separate follow-up.
- 2026-10-11: Targeted payload/composition tests and the full project suite passed after implementation.
- 2026-10-11: Superseded as the production default by tasks/done/2-2026-10-11-ollama-runtime-capability-logging.md; automatic mode is now the default so the application does not assume a fixed VRAM size.
