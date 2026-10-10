status: done
last change: 2026-10-10
dependency: ../done/3-2026-10-10-ai-kontrakt-a-segmentovy-preklad.md, ../done/2-2026-10-10-ai-profily-a-bezpecna-autentizace.md
group: translation/providers/openai
type: feature
description:
M07: OpenAI API backend s API klíčem
Priority: 3 (normal)
Created: 2026-10-10

Analysis:
[Implementační analýza](../../doc/modularization-analysis.md), sekce A06–A10; UML P01/P04/P05.
Tento task je zadání budoucí implementace; založení neznamená hotovou funkci.

Evidence:
Statická revize 2026-10-10 a explicitní požadavky uživatele na modularizaci formátů/AI, provider-specific konfiguraci a autentizaci.

Affected files/symbols:
ai/openai.py, provider registrace/options, optional SDK extra a test/mock API fixtures.

Recommended change:
1. Ověřit oficiální současnou API/SDK dokumentaci; zvolit podporovaný text endpoint a doložit verzi. Nehardcodovat 'latest' model.
2. Implementovat translate text a segment batch se sdíleným promptem/ID validací; capability output limits/structured response.
3. Credentials jen AuthProvider, model/organization/project/options z profilu; nepropagovat Ollama parametry.
4. Discovery pokud podporované; ověření profilu bez placené generace a s timeoutem. API key první auth, bez převzetí ChatGPT/Codex tokenů.
5. Mapovat text extraction, refusal/incomplete, auth/permission/quota/rate limits/request_id/usage; SDK retry vs společný budget.
6. Lazy optional SDK, čisté backend imports bez tkinter/PDF.

Acceptance:
1. Mock payload s model/lang/prompt/segments a redigovaným auth; správně extrahovaný text/multiple response items bez nežádoucího spojení.
2. 401/403/429/5xx/quota/truncation/refusal a unavailable model mají odpovídající BackendError.
3. Provider list/GUI fungují bez SDK; missing_dependency má instalační remedy.
4. Sentinel klíč i fake raw HTTP SDK exception bez úniku; žádný live request v testu.

Constraints:
Před prací načíst projektový AGENTS.md a doc/tools.md. Respektovat současný dirty worktree. Kód src/, testy test/, trvalé fixture test/mock. Bez souhlasu žádný commit/push/live cloud nebo sazba knihy. Lokálního implementačního agenta do odvolání nespouštět.
Public boundaries typed; komentáře vysvětlují invarianty/důvody. JSONL bez secrets; bezpečné chybové zprávy. High-level strukturu a všechny procesy dokumentovat Mermaid class/sequence; aktualizovat centrální diagramy, neduplikovat je bez potřeby.
Každý task vlastní offline testy. Případné doplňující informace nebo důvod neprovedené části zapsat do datovaných comments, status zůstává z povoleného slovníku.

Implementation:
2026-10-10: Implementován OpenAI API backend s API-key auth, standard-library transportem a bezpečným mapováním chyb.

comments:
2026-10-10: M07 dokončen; mock transport testy prošly, živé API nebylo voláno.
2026-10-10: Založeno jako M07; specifikace a acceptance připraveny, žádná změna produkčního kódu.
2026-10-10: Ke skutečnému smoke bude potřeba OpenAI API projekt/klíč, síť a souhlas s náklady; zaznamenat v comments, backend implementaci ověřit fake transportem.
