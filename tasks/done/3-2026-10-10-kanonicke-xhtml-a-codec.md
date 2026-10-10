status: done
last change: 2026-10-10
dependency: none
group: architecture/document/xhtml
type: refactor
description:
M01: Kanonické XHTML, metadata, resources a bezpečný codec
Priority: 3 (normal)
Created: 2026-10-10

Analysis:
[Implementační analýza](../../doc/modularization-analysis.md), sekce A04, A06; UML A03 a P04/P07.
Tento task je zadání budoucí implementace; založení neznamená hotovou funkci.

Evidence:
Statická revize 2026-10-10 a explicitní požadavky uživatele na modularizaci formátů/AI, provider-specific konfiguraci a autentizaci.

Affected files/symbols:
src/doctranslate/translate_core/contracts.py, nový xhtml_codec.py; read_translation_html/write_translation_html a bridge v translate.py pouze pro migraci.

Recommended change:
1. Zvolit bezpečný XHTML parser; body strom je jediná autorita. blocks/text/markup pouze odvozené read-only pohledy. Stabilní block/fragment IDs, zdrojová a překladová metadata oddělená.
2. Versioned schema, volitelná stránka pro nestránkové formáty, resource reference s media_type/role/path/SHA-256, namespaced PDF extension. ResourceResolver dostane base path XHTML.
3. Codec load/dump atomicky, validace namespace/IDs/style references/complete; zákaz DTD/externích entit/síťových resources. Legacy HTML migrátor pro br/span/data-block/data-span, bez regex parseru.
4. Ručně editovaný body má přednost před cache/source_markup. Neznámé schema nebo nejasná ID řízeně odmítnout, starý soubor nepřepsat.
5. Navázat na done XHTML bug; MarkupTranslation dočasně migrovat, neponechat nesynchronizovaný document.html.

Acceptance:
1. Roundtrip načíst → přeložit/mutovat → uložit → znovu načíst zachová aktuální text, styly, ID, hard breaks, pořadí i metadata.
2. Regrese: ruční text editace, více inline uzlů, entity, TOC řádek/kapitola, relativní resources po přesunu, null page pro nestránkový dokument.
3. Poškozený/novější schema, duplicate IDs, DTD/externí entity a disk-full odmítnuty bez ztráty posledního souboru.
4. Core/import a codec fungují bez PyMuPDF a provider SDK.

Constraints:
Před prací načíst projektový AGENTS.md a doc/tools.md. Respektovat současný dirty worktree. Kód src/, testy test/, trvalé fixture test/mock. Bez souhlasu žádný commit/push/live cloud nebo sazba knihy. Lokálního implementačního agenta do odvolání nespouštět.
Public boundaries typed; komentáře vysvětlují invarianty/důvody. JSONL bez secrets; bezpečné chybové zprávy. High-level strukturu a všechny procesy dokumentovat Mermaid class/sequence; aktualizovat centrální diagramy, neduplikovat je bez potřeby.
Každý task vlastní offline testy. Případné doplňující informace nebo důvod neprovedené části zapsat do datovaných comments, status zůstává z povoleného slovníku.

Implementation:
2026-10-10: Implementován bezpečný kanonický XHTML codec, resource metadata, atomické dump/load a regresní testy.

comments:
2026-10-10: M01 dokončen; cílené testy XHTML/core prošly.
2026-10-10: Založeno jako M01; specifikace a acceptance připraveny, žádná změna produkčního kódu.
2026-10-10: Přesné jméno parser knihovny lze zvolit při implementaci po kontrole Python >=3.11 včetně místního 3.14. Žádný přepis reálného přeloženého HTML v tmp.
