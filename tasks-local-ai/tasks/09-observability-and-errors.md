# 09 — Logování, výjimky a okrajové podmínky

status: created
last change: 2026-10-10
dependency: 01-baseline-and-bootstrap.md, 05-queue-store.md, 06-worker-lifecycle.md
group: 07-operations
type: feature
description: Zajistit dohledatelné logy, JSON diagnostiku a konzistentní chyby napříč CLI, GUI a workerem.
comments: 2026-10-10 — Zadání připraveno; agent nebyl spuštěn.

## Kontext

Načti context/03-operational-constraints.md a context/04-quality.md.

## Úkol

Zaveď strukturovaný run log, traceback diagnostiku a volitelný trace režim.
Chyby musí uvést fázi, cestu, job, model, exit code a doporučený další krok,
pokud je známý. GUI nemá zobrazit pouze traceback. Logování nesmí samo shodit
worker při nedostatku místa.

## Akceptace

- normální běh má stručný log, trace přidá detailní události a timing;
- výjimka se uloží do diagnostického souboru best-effort;
- disk full/readonly a chybějící vstupy mají stabilní klasifikaci;
- citlivé údaje a celé překlady se do logu nezapisují bez explicitního trace;
- testy ověří log při úspěchu i selhání.

## Ověření

Fault-injection testy pro log, diagnostiku, ENOSPC, missing file, invalid PDF
a timeout fake backendu.
