status: done
last change: 2026-10-10
dependency: none
group: architecture/formats/registry
type: feature
description:
M02: Oddělené read/write registry, výběr formátu a lazy dostupnost
Priority: 3 (normal)
Created: 2026-10-10

Analysis:
[Implementační analýza](../../doc/modularization-analysis.md), sekce A03, A05; UML P01.
Tento task je zadání budoucí implementace; založení neznamená hotovou funkci.

Evidence:
Statická revize 2026-10-10 a explicitní požadavky uživatele na modularizaci formátů/AI, provider-specific konfiguraci a autentizaci.

Affected files/symbols:
translate_core/adapters.py a nový formats/registry.py; composition root, pyproject optional extras v rozsahu availability.

Recommended change:
1. Descriptor id/label_key/media_type/extensions/factory/check_availability; oddělené input/output registry a explicitní built-in registrace.
2. Vyřešit explicit ID před příponou; známá konfliktní přípona → format_conflict; neznámá/chybějící + explicit ID povolena; auto bez rozpoznání → formát vyžádat.
3. Duplicate registrace v jednom směru je chyba, stejný formát v obou směrech je legitimní. Podporovat budoucí read-only/write-only modul.
4. Availability(available,code,reason,remedy) ověřuje pouze lokální runtime; žádné generování PDF, instalace nebo síť.
5. Lazy factories a import dependencies až při použití; PDF knihovna optional extra, plain text/start GUI nevyžadují PDF.

Acceptance:
1. Table-driven testy .PDF/explicit/auto/no extension/conflict/unknown format/duplicate/directional registration.
2. Fake unavailable adapter má konkrétní remedy a neblokuje jiné adaptery.
3. Import composition root s blokovaným PyMuPDF neselže; factory se nevolá jen při listování.
4. Výstupní formát se neodvozuje ze source media_type.

Constraints:
Před prací načíst projektový AGENTS.md a doc/tools.md. Respektovat současný dirty worktree. Kód src/, testy test/, trvalé fixture test/mock. Bez souhlasu žádný commit/push/live cloud nebo sazba knihy. Lokálního implementačního agenta do odvolání nespouštět.
Public boundaries typed; komentáře vysvětlují invarianty/důvody. JSONL bez secrets; bezpečné chybové zprávy. High-level strukturu a všechny procesy dokumentovat Mermaid class/sequence; aktualizovat centrální diagramy, neduplikovat je bez potřeby.
Každý task vlastní offline testy. Případné doplňující informace nebo důvod neprovedené části zapsat do datovaných comments, status zůstává z povoleného slovníku.

Implementation:
2026-10-10: Implementovány směrové registry formátů, explicitní/extension resolver, availability a lazy PDF factory.

comments:
2026-10-10: M02 dokončen; registry testy a regrese prošly.
2026-10-10: Založeno jako M02; specifikace a acceptance připraveny, žádná změna produkčního kódu.
2026-10-10: Samotné read/write PDF funkce jsou M03; neduplikovat legacy fallback registry přepisem při každém startu.
