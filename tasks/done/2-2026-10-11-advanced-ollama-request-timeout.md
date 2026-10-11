status: done
last change: 2026-10-11
dependency: none
group: translation/advanced/ollama
type: bug
estimate:
  time: 30–60 min
  logical_lines: 40–100
  tokens: 1–2 k
  subtasks: S01–S03
description: Advanced job job-c7e21af95de6 failed during the first contextual Ollama translation request.

## Evidence

Queue job:

- ID: job-c7e21af95de6
- input: tmp/salesforce/Kapitanov K. Salesforce Developer I Certification. Learn the Basics...2024.pdf
- model: translategemma:4b
- provider: ollama
- phase: both
- translator_id: advanced
- translator_options: empty
- output/html: normalized Salesforce paths in tmp/salesforce

Relevant queue.events.log entries:

    2026-10-11T12:06:53.244701Z worker.job.started model=translategemma:4b phase=both translator_id=advanced
    2026-10-11T12:06:53.275873Z worker.translation.engine.selected translator_id=advanced translator_revision=advanced-standard-v1
    2026-10-11T12:10:58.580451Z worker.job.failed error_type=TranslationError error=backend_error: timed out
    2026-10-11T12:10:58.626075Z worker.state state=failed error=backend_error: timed out

Run log:

    tmp/salesforce/Kapitanov K Salesforce Developer I Certification Learn the Basics2024-cs-layout.run.log
    run.configured: phase=both, model=translategemma:4b

Traceback evidence saved in queue.json for the job:

    ai/transport.py:33 request.urlopen(..., timeout=timeout)
    ai/transport.py:44 BackendError("network_error", "timed out", retryable=True)
    ai/ollama.py:255 OllamaBackend.translate_batch
    translation/advanced.py:159 _translate_with_retry
    translation/advanced.py:170 TranslationError("backend_error", str(exc), retryable=False)

## Analysis

The input PDF was found and the production advanced registry/runner was
selected successfully. Failure occurred before a translated batch was
committed. HttpAiBackend used its fixed default timeout of 120 seconds.
Advanced mode retried the same request twice, so the job failed after roughly
245 seconds. The empty translator_options map gave the job no way to select a
longer local-model timeout. No PDF typesetting failure was involved.
The first implementation used a longer synchronous request timeout, but that
did not make Stop reliable: a blocking urllib response read still lived in the
worker process.

## Required change

Use a 1800-second total wall-clock limit for one Ollama request unless the job
specifies another positive value. Run the request in a disposable child
process so Stop and timeout can terminate it. The worker remains the
supervisor. When configured for a worker-owned Ollama instance, the provider
module must stop and restart only that instance after a timeout or cancellation.
Retry the unchanged batch once; after the retry is exhausted, keep the job
restartable in paused state and do not advance its checkpoint or mark it failed.
An external Ollama instance must never be killed implicitly.

## Acceptance

- Existing offline tests remain green.
- Default production Ollama timeout for an advanced job is 1800 seconds.
- Explicit translator_options.request_timeout is passed unchanged.
- The timeout is a total wall-clock limit for one provider request.
- The default advanced runtime uses a worker-owned Ollama process on port 11435;
  its executable and port are configurable. Setting manage_ollama=false leaves
  an external service untouched.
- Stop terminates the request child promptly and preserves the job as
  in_progress; an exhausted timeout retry changes it to paused, not failed.
- Checkpoint files are not advanced by a timed-out batch.
- Live rerun of the failed Salesforce job is a separate manual verification;
  this task must not silently launch a long Ollama translation.

## Subtasks

| ID | Result | Estimate |
|---|---|---:|
| S01 | Add wall-clock child-process HTTP cancellation | 20–35 min, 80–150 lines |
| S02 | Add worker-owned Ollama lifecycle and restart boundary | 15–25 min, 60–110 lines |
| S03 | Map timeout/cancel to retry, paused, and restartable states | 10–20 min, 30–60 lines |
| S04 | Offline regression tests, review, and task evidence | 10–20 min, 25–60 lines |

## Comments

2026-10-11: Task created from the failed GUI run and queue diagnostics.

2026-10-11: Původní dílčí oprava pouze prodloužila synchronní HTTP limit na
600 sekund; po požadavku na okamžité zastavení a řízení vlastních procesů je
nahrazena robustnějším návrhem s request child procesem a Ollama runtime.

2026-10-11: Implementována izolace Ollama HTTP požadavku, výchozí celkový limit
1800 sekund, worker-owned Ollama runtime, restart po timeoutu/cancelu a převod
vyčerpaného timeoutu na paused. Čeká cílená a úplná offline validace; živý
rerun Salesforce jobu zůstává ruční operací.

2026-10-11: Validace dokončena: 252 testů a 4 subtesty prošly, compileall
prošel. Přidán lokální HTTP smoke test child transportu a wall-clock timeoutu.
Živý překlad, ověření dostupnosti executable ollama a dlouhý rerun Salesforce
jobu nebyly spuštěny.

2026-10-11: Finální regresní běh odhalil předčasný start managed Ollamy při
konstrukci jobu. Start byl přesunut lazy až před první AI request; tím zůstává
validace vstupního PDF nezávislá na dostupnosti Ollamy. Po opravě znovu prošlo
252 testů a 4 subtesty.
