status: done
last change: 2026-10-10
dependency: ../done/3-2026-10-10-ai-kontrakt-a-segmentovy-preklad.md, ../done/2-2026-10-10-ai-profily-a-bezpecna-autentizace.md
group: translation/providers/gemini
type: feature
description:
M08: Gemini API backend s klíčem a přípravou OAuth
Priority: 3 (normal)
Created: 2026-10-10

Analysis:
[Implementační analýza](../../doc/modularization-analysis.md), sekce A06–A10; UML P01/P04/P05.
Tento task je zadání budoucí implementace; založení neznamená hotovou funkci.

Evidence:
Statická revize 2026-10-10 a explicitní požadavky uživatele na modularizaci formátů/AI, provider-specific konfiguraci a autentizaci.

Affected files/symbols:
ai/gemini.py, registrace/options, optional SDK extra, test/mock fixtures.

Recommended change:
1. Ověřit oficiální Gemini API/SDK; první cesta Gemini API, nezaměňovat s jiným produktem jménem Gemini ani automaticky s Vertex AI.
2. Text + segment batch, provider-specific model/output/structured options; credential source delegovat AuthProvider.
3. API key plně podporovaný. Rozhraní credentials již připravit pro OAuth z M10 bez změny pipeline.
4. Discovery/capabilities: empty model list, unsupported generation model a API error odděleně. Nehádat model ID z prefixu.
5. Safety blocking/finish reason/truncation/empty candidates/quota/rate limit/token usage bezpečně mapovat.

Acceptance:
1. Mock translate/batch/structured and fallback pro validní model capabilities, ID roundtrip.
2. Safety block/empty candidates/truncated/quota/401/403/429/5xx odmítnout podle smlouvy; bounded retry.
3. Injectované credentials fungují jak fake key, tak fake token bez UI/PDF coupling.
4. Missing SDK jen unavailable; žádná síť/Google account v automatických testech.

Constraints:
Před prací načíst projektový AGENTS.md a doc/tools.md. Respektovat současný dirty worktree. Kód src/, testy test/, trvalé fixture test/mock. Bez souhlasu žádný commit/push/live cloud nebo sazba knihy. Lokálního implementačního agenta do odvolání nespouštět.
Public boundaries typed; komentáře vysvětlují invarianty/důvody. JSONL bez secrets; bezpečné chybové zprávy. High-level strukturu a všechny procesy dokumentovat Mermaid class/sequence; aktualizovat centrální diagramy, neduplikovat je bez potřeby.
Každý task vlastní offline testy. Případné doplňující informace nebo důvod neprovedené části zapsat do datovaných comments, status zůstává z povoleného slovníku.

Implementation:
2026-10-10: Implementován Gemini API backend s API-key v hlavičce x-goog-api-key; klíč není v URL.

comments:
2026-10-10: M08 dokončen; mock transport testy prošly, živé API nebylo voláno.
2026-10-10: Založeno jako M08; specifikace a acceptance připraveny, žádná změna produkčního kódu.
2026-10-10: Konkrétní Google Cloud projekt/scopes/client setup a browser flow řeší M10. Pro live smoke budou potřeba uživatelovy credentials.
