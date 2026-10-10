status: done
last change: 2026-10-10
dependency: ../done/3-2026-10-10-ai-kontrakt-a-segmentovy-preklad.md, ../done/2-2026-10-10-ai-profily-a-bezpecna-autentizace.md
group: translation/providers/ollama
type: refactor
description:
M06: Převést dosavadní OllamaClient na samostatný AI provider
Priority: 3 (normal)
Created: 2026-10-10

Analysis:
[Implementační analýza](../../doc/modularization-analysis.md), sekce A06–A10; UML P01/P04/P05.
Tento task je zadání budoucí implementace; založení neznamená hotovou funkci.

Evidence:
Statická revize 2026-10-10 a explicitní požadavky uživatele na modularizaci formátů/AI, provider-specific konfiguraci a autentizaci.

Affected files/symbols:
Nový ai/ollama.py; OllamaClient a GPU/context/discovery/payload/stats/recovery funkce v translate.py/queue_app.py.

Recommended change:
1. Implementovat AiTextBackend a batch capability, provider-specific profile schema/options a model discovery.
2. Přesunout HTTP/stream parsing a dosavadní tuning bez závislosti na PDF/job globálech. Prompt/segment validace jsou sdílené M04, ne druhá kopie.
3. Zachovat explicitní --model/--ollama-url/env precedence pro legacy job; resolved endpoint/model/options součást run snapshotu.
4. Missing server/no_models/unknown model/stream truncation odlišit; neinstalovat nebo stahovat automaticky model.
5. Provider obecné registry factory lazy; GPU/keep_alive/think volby pouze Ollama, žádné tunování ostatních služeb.

Acceptance:
1. Mock Ollama translate text + batch, stream/no-stream, partial/truncated/error a discovery.
2. Dva joby model A/B/default nezdědí předchozí mutable model/context/path; timeout/retry budget respektován.
3. Chybějící server/model konkrétně hlášeny; model count label se nevrací.
4. Testy bez Ollamy, Continue a skutečného model downloadu.

Constraints:
Před prací načíst projektový AGENTS.md a doc/tools.md. Respektovat současný dirty worktree. Kód src/, testy test/, trvalé fixture test/mock. Bez souhlasu žádný commit/push/live cloud nebo sazba knihy. Lokálního implementačního agenta do odvolání nespouštět.
Public boundaries typed; komentáře vysvětlují invarianty/důvody. JSONL bez secrets; bezpečné chybové zprávy. High-level strukturu a všechny procesy dokumentovat Mermaid class/sequence; aktualizovat centrální diagramy, neduplikovat je bez potřeby.
Každý task vlastní offline testy. Případné doplňující informace nebo důvod neprovedené části zapsat do datovaných comments, status zůstává z povoleného slovníku.

Implementation:
2026-10-10: Přidán OllamaBackend a compatibility bridge; legacy OllamaClient zůstává pro robustní PDF batch režim.

comments:
2026-10-10: M06 dokončen; native Ollama provider a bridge jsou pokryté mock testy.
2026-10-10: Založeno jako M06; specifikace a acceptance připraveny, žádná změna produkčního kódu.
2026-10-10: Benchmark translategemma:12b ani model instalace nejsou tento task. Získaná partial translation cache migruje přes M11.
