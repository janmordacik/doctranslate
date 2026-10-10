status: done
last change: 2026-10-10
dependency: ../done/3-2026-10-10-registr-formatu-a-dostupnost.md, ../done/3-2026-10-10-openai-api-provider.md, ../done/3-2026-10-10-gemini-api-provider.md, ../done/3-2026-10-10-claude-api-provider.md, ../done/3-2026-10-10-gemini-browser-oauth.md, ../done/3-2026-10-10-cli-worker-a-profily-jobu.md
group: app/gui/providers
type: feature
description:
M13: Výběr provider/profil/model a specifické konfigurační dialogy
Priority: 3 (normal)
Created: 2026-10-10

Analysis:
[Implementační analýza](../../doc/modularization-analysis.md), sekce A07, A08, A11; UML P01–P03/P06.
Tento task je zadání budoucí implementace; založení neznamená hotovou funkci.

Evidence:
Statická revize 2026-10-10 a explicitní požadavky uživatele na modularizaci formátů/AI, provider-specific konfiguraci a autentizaci.

Affected files/symbols:
QueueGui v queue_app.py, nový gui/provider_dialogs.py, GUI_TEXT cs/en; bez import tkinter do ai.

Recommended change:
1. Job editor provider/profil/model + Konfigurace…; format read/write combo samostatně. Zachovat Worker/Job/General a status bar.
2. UI registry dialog_factory podle provider ID. Ollama endpoint/options; OpenAI/Claude API key/options; Gemini API key nebo OAuth + Login/Logout/setup.
3. Save nová profile revize a dirty job přiřazení, Update publish; Cancel beze změny včetně staged credentials rollback.
4. Discovery async/timeout/cache a stale profile/revision/request_generation guard. No_models vs unavailable vs auth_required; ne zobrazit model count.
5. Při switch provideru znovu validovat model; manual model ID jen descriptor podporuje. Nepřepisovat selection/scroll/drafts v pollu.
6. Start/Update cancels pending stop; Stop disabled při stopping; control mimo job list. Nové texty/chyby cs/en a žádné secrets v status.

Acceptance:
1. Fake UI controller test Save/Cancel/Update/Start/dirty-close, provider switch a revision pinning.
2. Slow/stale discovery výsledky nepřepisují současný výběr; label bez počtu modelů.
3. Provider-specific auth možnosti odpovídají capabilities; worker login se nikdy neotevře automaticky.
4. Poll selection/scroll a job edits drží; stop UI regresní testy.
5. Ruční checklist všech dialogů cs/en bez skutečných klíčů a bez cloud generace.

Constraints:
Před prací načíst projektový AGENTS.md a doc/tools.md. Respektovat současný dirty worktree. Kód src/, testy test/, trvalé fixture test/mock. Bez souhlasu žádný commit/push/live cloud nebo sazba knihy. Lokálního implementačního agenta do odvolání nespouštět.
Public boundaries typed; komentáře vysvětlují invarianty/důvody. JSONL bez secrets; bezpečné chybové zprávy. High-level strukturu a všechny procesy dokumentovat Mermaid class/sequence; aktualizovat centrální diagramy, neduplikovat je bez potřeby.
Každý task vlastní offline testy. Případné doplňující informace nebo důvod neprovedené části zapsat do datovaných comments, status zůstává z povoleného slovníku.

Implementation:
2026-10-10: GUI rozšířeno o provider/profile/model, provider-specific konfiguraci, Gemini login hook a cs/en lokalizaci.

comments:
2026-10-10: M13 dokončen; GUI/provider kontrakt a queue regrese prošly.
2026-10-10: Založeno jako M13; specifikace a acceptance připraveny, žádná změna produkčního kódu.
2026-10-10: GUI pole nejsou implementovaná tímto task souborem. Dialog rozsah při implementaci lze rozdělit provider-by-provider, kontrakt UI factory zachovat.
