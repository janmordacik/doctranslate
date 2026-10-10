status: done
last change: 2026-10-10
dependency: ../done/2-2026-10-10-ai-profily-a-bezpecna-autentizace.md, ../done/3-2026-10-10-gemini-api-provider.md
group: translation/providers/gemini/auth
type: feature
description:
M10: Oficiální Gemini desktop OAuth a obnovování tokenů
Priority: 3 (normal)
Created: 2026-10-10

Analysis:
[Implementační analýza](../../doc/modularization-analysis.md), sekce A08, A10, A11; UML P03/P05.
Tento task je zadání budoucí implementace; založení neznamená hotovou funkci.

Evidence:
Statická revize 2026-10-10 a explicitní požadavky uživatele na modularizaci formátů/AI, provider-specific konfiguraci a autentizaci.

Affected files/symbols:
Gemini AuthProvider implementace, ai/auth.py secure-store extension, explicitní frontend login facade.

Recommended change:
1. Ověřit oficiální desktop OAuth/scopes/SDK/client setup pro cílové Gemini API; zdokumentovat potřebný project/client consent setup.
2. Interaktivní login explicitně přes browser a localhost callback, random state, PKCE dle dokumentované podpory, timeout a cancel cleanup.
3. Uložit access/refresh tokeny bezpečně/staged; automatické neinteraktivní refresh, credential lock a refresh rotation.
4. auth_required při revocation/invalid_grant bez browseru workeru; logout lokální cleanup a podporovaná remote revokace pouze na explicitní úkon.
5. Nezavádět obecný OAuth pro OpenAI/Claude bez podporované registrace; frontend capability-based.

Acceptance:
1. Fake auth server test callback state mismatch/cancel/timeout/success, listener closed po každém výsledku.
2. Refresh before/during next batch, rotated refresh token a současný GUI/worker neduplikují rotaci.
3. Worker neotevře browser ani při chybě; checkpoint/failed remedy podle M11.
4. Secrets neuniknou do config/log/URL diagnostiky; instalace skutečného OAuth klienta/user consent evidována zvlášť.

Constraints:
Před prací načíst projektový AGENTS.md a doc/tools.md. Respektovat současný dirty worktree. Kód src/, testy test/, trvalé fixture test/mock. Bez souhlasu žádný commit/push/live cloud nebo sazba knihy. Lokálního implementačního agenta do odvolání nespouštět.
Public boundaries typed; komentáře vysvětlují invarianty/důvody. JSONL bez secrets; bezpečné chybové zprávy. High-level strukturu a všechny procesy dokumentovat Mermaid class/sequence; aktualizovat centrální diagramy, neduplikovat je bez potřeby.
Každý task vlastní offline testy. Případné doplňující informace nebo důvod neprovedené části zapsat do datovaných comments, status zůstává z povoleného slovníku.

Implementation:
2026-10-10: Implementován obecný browser OAuth s loopback callbackem, PKCE, state kontrolou, refresh tokenem a Gemini konfigurací.

comments:
2026-10-10: M10 dokončen; refresh/logout/offline testy prošly. Živý browser OAuth nebyl spuštěn.
2026-10-10: Založeno jako M10; specifikace a acceptance připraveny, žádná změna produkčního kódu.
2026-10-10: Do comments při realizaci doplnit: uživatelský Google project/client credentials/consent nejsou dodané. Nikdy nezakládat cloud projekt nebo povolovat billing bez uživatele.
