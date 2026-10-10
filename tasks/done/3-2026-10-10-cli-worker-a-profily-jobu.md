status: done
last change: 2026-10-10
dependency: ../done/3-2026-10-10-jobrunner-a-identita-checkpointu.md
group: runtime/worker/providers
type: feature
description:
M12: Napojit CLI/worker, profilové joby a formátové volby
Priority: 3 (normal)
Created: 2026-10-10

Analysis:
[Implementační analýza](../../doc/modularization-analysis.md), sekce A09, A11; UML P01/P04/P06.
Tento task je zadání budoucí implementace; založení neznamená hotovou funkci.

Evidence:
Statická revize 2026-10-10 a explicitní požadavky uživatele na modularizaci formátů/AI, provider-specific konfiguraci a autentizaci.

Affected files/symbols:
queue_app.py CLI/QueueStore/make_job/merge_queue_jobs/WorkerController, queue_worker.py JobOptions/run_job, __main__.py/translate.py entrypoint.

Recommended change:
1. CLI/worker jediný JobRunner. Job fields profile_id/profile_revision/model/input_format/output_format; validovat a přijmout legacy schema/job defaults Ollama.
2. Workeru explicitní config path; pin profile revize v add/Update, nepřenášet credential_ref ani secret snapshot do queue.
3. Přidat --profile/--input-format/--output-format k běžnému i add vstupu; providers/profiles/login/configuration bez GUI dependency.
4. Maskovaný API key prompt nebo explicit env reference, nikdy klíč v argv. configuration je textové UI.
5. Active job substantive změny odmítnout; pause → edit/prepare → identity validace. Zachovat stop/pause/failed semantics, single worker lock a krátké queue transactions.
6. GUI Update/CLI publish značí změnu; saving profile samo nemění frontu. Start only, Update cancel pending stop.

Acceptance:
1. CLI parse/probe/list mimo síť; configuration/login bez tkinter, worker neinteraktivní.
2. Legacy job model/default a config path z jiného cwd deterministické.
3. Dlouhý request, last-unit stop/pause, restart, auth_required failed a další připravený job offline lifecycle testy.
4. Queue.lock není drženo během API/login/refresh/export; active mutation konflikt, dirty Start neposílá.
5. Credentials nejsou ani v status --json/queue traceback.

Constraints:
Před prací načíst projektový AGENTS.md a doc/tools.md. Respektovat současný dirty worktree. Kód src/, testy test/, trvalé fixture test/mock. Bez souhlasu žádný commit/push/live cloud nebo sazba knihy. Lokálního implementačního agenta do odvolání nespouštět.
Public boundaries typed; komentáře vysvětlují invarianty/důvody. JSONL bez secrets; bezpečné chybové zprávy. High-level strukturu a všechny procesy dokumentovat Mermaid class/sequence; aktualizovat centrální diagramy, neduplikovat je bez potřeby.
Každý task vlastní offline testy. Případné doplňující informace nebo důvod neprovedené části zapsat do datovaných comments, status zůstává z povoleného slovníku.

Implementation:
2026-10-10: Job a CLI podporují provider/profile/input-format/output-format; worker předává volby do translation composition root.

comments:
2026-10-10: M12 dokončen; queue/CLI/worker regresní testy prošly.
2026-10-10: Založeno jako M12; specifikace a acceptance připraveny, žádná změna produkčního kódu.
2026-10-10: Zachovat souborový protokol; žádné IPC ani nové stavy. Existing JobOptions může být postupně nahrazen JobSpec, ne druhý nekompatibilní model.
