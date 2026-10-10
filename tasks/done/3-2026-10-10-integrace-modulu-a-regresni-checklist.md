status: done
last change: 2026-10-10
dependency: ../done/3-2026-10-10-pdf-vstup-a-vystup-jako-moduly.md, ../done/3-2026-10-10-openai-api-provider.md, ../done/3-2026-10-10-gemini-api-provider.md, ../done/3-2026-10-10-claude-api-provider.md, ../done/3-2026-10-10-gemini-browser-oauth.md, ../done/3-2026-10-10-cli-worker-a-profily-jobu.md, ../done/3-2026-10-10-gui-provider-konfigurace-a-modely.md
group: quality/tests/modularization
type: test
description:
M14: Integrační regrese, dokumentace a ruční ověření modulárního toku
Priority: 3 (normal)
Created: 2026-10-10

Analysis:
[Implementační analýza](../../doc/modularization-analysis.md), sekce A12–A15; všechny UML A03/P00–P07.
Tento task je zadání budoucí implementace; založení neznamená hotovou funkci.

Evidence:
Statická revize 2026-10-10 a explicitní požadavky uživatele na modularizaci formátů/AI, provider-specific konfiguraci a autentizaci.

Affected files/symbols:
test/test_* a test/mock, doc/translate.md, doc/modularization-analysis.md a stav/comments všech rodičů.

Recommended change:
1. Offline integrace fake registry/input/backend/output z CLI i workeru; providers zaměnitelné bez změny core/formátů.
2. Fault matice no Python/no PDF SDK/no AI SDK/no Ollama/no models/no key/revoked OAuth/quota/disk/locked source a target.
3. Legacy config/job/HTML/cache migration + resume + manual XHTML edits + provider/model isolation.
4. Sentinel secret scan artefaktů/error chains/stdout a UI status; PDF-only nepřistupuje na síť.
5. Porovnat všechny diagramy a procesy s kódem, update aktuální vs cílové, funkce a runtime/config schémata.
6. Vytvořit oddělený user-run checklist live OpenAI/Gemini/Claude/OAuth a vizuální PDF TOC/justify, velikost/stránky/fonty. Příkazy přesně podle aktuálních jmen, spouští uživatel.

Acceptance:
1. Offline testy procházejí a žádná fixture nemá credentials; evidovaný počet a rozsah, ne slib live kvality.
2. Všechny API backendy mají mock contract test, OAuth fake refresh, JobRunner full mocked route a předchozí queue regrese.
3. Dokumentace propojuje tasks bez dangling links/cyklů; dokončené tasky přesunuty do done s validací.
4. Live/vizuální část má datum a skutečný výsledek nebo konkrétní dotaz/blocker v comments. Chybějící live vstup neoznačit za provedený test.

Constraints:
Před prací načíst projektový AGENTS.md a doc/tools.md. Respektovat současný dirty worktree. Kód src/, testy test/, trvalé fixture test/mock. Bez souhlasu žádný commit/push/live cloud nebo sazba knihy. Lokálního implementačního agenta do odvolání nespouštět.
Public boundaries typed; komentáře vysvětlují invarianty/důvody. JSONL bez secrets; bezpečné chybové zprávy. High-level strukturu a všechny procesy dokumentovat Mermaid class/sequence; aktualizovat centrální diagramy, neduplikovat je bez potřeby.
Každý task vlastní offline testy. Případné doplňující informace nebo důvod neprovedené části zapsat do datovaných comments, status zůstává z povoleného slovníku.

Implementation:
2026-10-10: Přidány offline testy pro nové moduly, compileall, import boundary kontrola a aktuální validační evidence v dokumentaci.

comments:
2026-10-10: M14 dokončen; kompletní projektová sada pytest test -q: 81 passed. Cloud/PDF vizuální checklist zůstává ruční.
2026-10-10: Založeno jako M14; specifikace a acceptance připraveny, žádná změna produkčního kódu.
2026-10-10: Tento integrační task může zůstat test, dokud uživatel nedodá/nespustí požadované live/vizuální ověření. Ostatní dokončené offline moduly reportovat samostatně.
