status: done
last change: 2026-10-10
dependency: ../done/3-2026-10-10-kanonicke-xhtml-a-codec.md, ../done/3-2026-10-10-registr-formatu-a-dostupnost.md, ../done/3-2026-10-10-pdf-vstup-a-vystup-jako-moduly.md, ../done/3-2026-10-10-ai-kontrakt-a-segmentovy-preklad.md, ../done/2-2026-10-10-ai-profily-a-bezpecna-autentizace.md, ../done/3-2026-10-10-ollama-provider-a-migrace.md
group: architecture/orchestration/jobrunner
type: refactor
description:
M11: JobRunner, neutrální fáze, cache identity a legacy migrace
Priority: 3 (normal)
Created: 2026-10-10

Analysis:
[Implementační analýza](../../doc/modularization-analysis.md), sekce A09, A10; UML P04–P07.
Tento task je zadání budoucí implementace; založení neznamená hotovou funkci.

Evidence:
Statická revize 2026-10-10 a explicitní požadavky uživatele na modularizaci formátů/AI, provider-specific konfiguraci a autentizaci.

Affected files/symbols:
Nový job_runner.py, immutable JobSpec/RunContext; translate.py run_translation/run_html_typesetting/cache_key/job_identity/matching_plan.

Recommended change:
1. Orchestrace input/codec → pipeline → output, existující html/pdf/both phases zachovat. Backend sestavit jen pro chybějící překlad.
2. Profile revision/model/endpoint/options připnout do run identity; credentials mimo identitu a artefakty. Runtime instance data bez sdílených globálů.
3. Machine cache key provider/endpoint/model/language/source/prompt/segmenter/output-affecting options. Změna identity conflict, ne silent reuse.
4. Explicitní validovaný import legacy Ollama cache/plan; unknown endpoint/policy nepřiřadit cloudům; hotové ruční XHTML zachovat.
5. Commit pouze validované jednotky, disk failure brání další generaci, export identity podle aktuálního XHTML/layout/resource hash.
6. Control callback po jednotce a při bezpečném backoff; stop nevyvolá další retry, auth_required zachová checkpoint a failed remedy.

Acceptance:
1. Fake input/backend/output pipeline funguje; PDF-only ani úplné XHTML nevytvoří AI/auth/network.
2. Restart při shodné identitě nepřekládá hotové jednotky; rozdílný provider/model/endpoint/prompt identity se nesmíchá.
3. Secrets nejsou v identity/plan/cache; key refresh neruší kompatibilitu.
4. Source remap, invalid schema, partial reply a disk-full respektují poslední validní artefakt.
5. Dva následné joby nemají sdílený mutable context; legacy artefakty čitelné přes migraci.

Constraints:
Před prací načíst projektový AGENTS.md a doc/tools.md. Respektovat současný dirty worktree. Kód src/, testy test/, trvalé fixture test/mock. Bez souhlasu žádný commit/push/live cloud nebo sazba knihy. Lokálního implementačního agenta do odvolání nespouštět.
Public boundaries typed; komentáře vysvětlují invarianty/důvody. JSONL bez secrets; bezpečné chybové zprávy. High-level strukturu a všechny procesy dokumentovat Mermaid class/sequence; aktualizovat centrální diagramy, neduplikovat je bez potřeby.
Každý task vlastní offline testy. Případné doplňující informace nebo důvod neprovedené části zapsat do datovaných comments, status zůstává z povoleného slovníku.

Implementation:
2026-10-10: Implementován JobRunner, JobSpec/RunContext, provider-aware cache identity a atomické checkpointy s uloženými překlady.

comments:
2026-10-10: M11 dokončen; restart z checkpointu ověřen offline.
2026-10-10: Založeno jako M11; specifikace a acceptance připraveny, žádná změna produkčního kódu.
2026-10-10: Vyžaduje nejvíce multi-file práce; při implementaci rozdělit na testovatelné facade/cache/import části se zachováním invariantů. Nepřepisovat všechny legacy funkce najednou.
