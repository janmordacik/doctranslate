status: done
last change: 2026-10-10
dependency: ../done/3-2026-10-10-ai-kontrakt-a-segmentovy-preklad.md, ../done/2-2026-10-10-ai-profily-a-bezpecna-autentizace.md
group: translation/providers/claude
type: feature
description:
M09: Anthropic Claude API backend s API klíčem
Priority: 3 (normal)
Created: 2026-10-10

Analysis:
[Implementační analýza](../../doc/modularization-analysis.md), sekce A06–A10; UML P01/P04/P05.
Tento task je zadání budoucí implementace; založení neznamená hotovou funkci.

Evidence:
Statická revize 2026-10-10 a explicitní požadavky uživatele na modularizaci formátů/AI, provider-specific konfiguraci a autentizaci.

Affected files/symbols:
ai/claude.py, registrace/options, optional SDK extra, test/mock fixtures.

Recommended change:
1. Ověřit oficiální Claude API/SDK. Implementovat text/batch API se společným promptem a explicitními ID.
2. API key přes AuthProvider. Model/max output/options validovat; neposílat Ollama num_ctx/keep_alive/think.
3. Správně zpracovat content blocks, text, stop reason/refusal/token truncation; nontext/tool output nepřijímat jako překlad.
4. Discovery dle skutečné dokumentované dostupnosti, ne browser session. Žádné cookies/OAuth tokeny Claude Code ani automatický subscription workaround.
5. Mapovat auth/permission/quota/429/5xx/request ID/usage, bounded retry a lazy optional SDK.

Acceptance:
1. Mock text/content blocks a batch s přeloženými IDs; strukturovaný režim jen pro podporovanou capability.
2. Nontext/empty/refusal/truncated text i quota/auth chyby nepovažovány za success.
3. Config nesmí obsahovat secret; sentinel test raw SDK exception/traceback bezpečný.
4. Bez SDK fungují jiné poskytovatele a startup; testy bez live API.

Constraints:
Před prací načíst projektový AGENTS.md a doc/tools.md. Respektovat současný dirty worktree. Kód src/, testy test/, trvalé fixture test/mock. Bez souhlasu žádný commit/push/live cloud nebo sazba knihy. Lokálního implementačního agenta do odvolání nespouštět.
Public boundaries typed; komentáře vysvětlují invarianty/důvody. JSONL bez secrets; bezpečné chybové zprávy. High-level strukturu a všechny procesy dokumentovat Mermaid class/sequence; aktualizovat centrální diagramy, neduplikovat je bez potřeby.
Každý task vlastní offline testy. Případné doplňující informace nebo důvod neprovedené části zapsat do datovaných comments, status zůstává z povoleného slovníku.

Implementation:
2026-10-10: Implementován Claude Messages API backend s API-key hlavičkou, transportem a chybovým kontraktem.

comments:
2026-10-10: M09 dokončen; mock transport testy prošly, živé API nebylo voláno.
2026-10-10: Založeno jako M09; specifikace a acceptance připraveny, žádná změna produkčního kódu.
2026-10-10: Skutečný Anthropic API účet/klíč a účtování jsou vstupy k pozdějšímu smoke, ne podmínka psaní offline backendu.
