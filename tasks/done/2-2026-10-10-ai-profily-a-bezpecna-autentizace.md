status: done
last change: 2026-10-10
dependency: none
group: translation/providers/auth
type: feature
description:
M05: Verzované profily, CredentialStore a společná autentizační hranice
Priority: 2 (high)
Created: 2026-10-10

Analysis:
[Implementační analýza](../../doc/modularization-analysis.md), sekce A08, A09, A10; UML A03/P02/P03.
Tento task je zadání budoucí implementace; založení neznamená hotovou funkci.

Evidence:
Statická revize 2026-10-10 a explicitní požadavky uživatele na modularizaci formátů/AI, provider-specific konfiguraci a autentizaci.

Affected files/symbols:
config.py, nové ai/profiles.py a ai/auth.py, pyproject pro volitelné secure-store dependencies; bez skutečných credentials.

Recommended change:
1. Config schema 1→2, explicitní profile ID/revision a immutable revize. Zachovat workdir/language, další podporovaná pole a reference starých jobů; unknown newer schema odmítnout.
2. save_config(workdir/language) nesmí smazat AI profily. Atomic storage/krátký config lock; profile revisions se neupravují in place.
3. CredentialStore get/set/delete; Windows Credential Manager nebo bezpečný keyring backend, in-memory fake. Bez store nikdy plaintext fallback.
4. AuthProvider none/api_key a rozhraní OAuth pro M10; explicit env reference pro CLI/CI. credential_ref jen v config, ne job/HTML.
5. Maskované/staged secret uložení před config commitem; selhání zachová starý profil; rollback jen nového secretu. Worker noninteractive.
6. Redakční utility pro HTTP error chain/traceback/raw exceptions, bez úniku secrets i s trace. Krátký credential lock pro refresh rotaci.

Acceptance:
1. Config 1 a chybějící config → legacy Ollama; žádné cloud přesměrování. Workdir/language save zachová všechny profily/revize.
2. Unknown/duplicate ID-revision, chybějící reference a store failure mají řízenou remedy. GUI/worker z jiného cwd může vyřešit explicitní config path.
3. Staged save/cancel/atomic write failure netrápí starý klíč/profil; parallel credential update se serializuje mimo queue.lock.
4. Sentinel key/token nejsou v config/job/cache/HTML/plan/log/stdout/exception chain. Testovat bez skutečného OS account secretu.

Constraints:
Před prací načíst projektový AGENTS.md a doc/tools.md. Respektovat současný dirty worktree. Kód src/, testy test/, trvalé fixture test/mock. Bez souhlasu žádný commit/push/live cloud nebo sazba knihy. Lokálního implementačního agenta do odvolání nespouštět.
Public boundaries typed; komentáře vysvětlují invarianty/důvody. JSONL bez secrets; bezpečné chybové zprávy. High-level strukturu a všechny procesy dokumentovat Mermaid class/sequence; aktualizovat centrální diagramy, neduplikovat je bez potřeby.
Každý task vlastní offline testy. Případné doplňující informace nebo důvod neprovedené části zapsat do datovaných comments, status zůstává z povoleného slovníku.

Implementation:
2026-10-10: Implementovány verzované AiProfile/ProfileStore, zachování konfigurace a CredentialStore hranice včetně env/keyring/memory backendu.

comments:
2026-10-10: M05 dokončen; secrets nejsou v jobu ani profilu, offline testy prošly.
2026-10-10: Založeno jako M05; specifikace a acceptance připraveny, žádná změna produkčního kódu.
2026-10-10: P2 kvůli riziku úniku klíčů a mazání profilů při dosavadním save_config. Skutečné uživatelské klíče a OS live test jsou pozdější explicitní ruční vstup, ne blokátor fake implementace.
