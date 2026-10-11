status: done
last change: 2026-10-11
type: bug
group: ai/ollama/transport
dependency: none
description: Worker remains in progress after Ollama finishes because the killable HTTP child can block while writing a large JSON response to stdout. The parent polls for child termination and reads stdout only after termination, creating a pipe deadlock.

Evidence:
- Job: job-66556e5a6ff5, model translategemma:4b, advanced, phase both.
- Worker state remained in_progress with progress 0 and no HTML or checkpoint.
- Ollama GPU activity stopped; the managed endpoint still reported the model loaded.
- netstat showed no active connection to port 11435, while the worker and HTTP child remained alive.
- Relevant implementation path: SubprocessHttpTransport.request starts a child with stdout=PIPE and calls communicate only after process.poll reports termination; _child_main prints the full response before exiting.

Plan and estimates:
- S01: Drain child stdout and stderr concurrently while polling cancellation and timeout. Estimate: 10 minutes, 35 logical lines, 500 tokens. Dependencies: none.
- S02: Add a regression test with a response larger than the OS pipe buffer. Estimate: 5 minutes, 35 logical lines, 400 tokens. Dependencies: S01.

Acceptance:
- Large HTTP child responses complete without blocking.
- Timeout and cancellation still terminate the child and invoke the abort callback.
- Child stderr cannot fill and deadlock the parent.
- Targeted transport tests and the full project test suite pass.

comments:
- 2026-10-11: Root cause confirmed as a classic stdout pipe deadlock. The HTTP connection had already closed, but the child was blocked writing its response to the parent pipe.
- 2026-10-11: Implemented concurrent draining of child stdout and stderr while the parent monitors cancellation and timeout. Added a 200kB response regression test. Targeted tests passed 3/3; full suite passed 253 tests and 4 subtests; compileall and git diff --check passed.
