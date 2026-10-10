status: done
last change: 2026-10-10
dependency: ../done/3-2026-10-10-kanonicke-xhtml-a-codec.md, ../done/3-2026-10-10-registr-formatu-a-dostupnost.md
group: architecture/formats/pdf
type: refactor
description:
M03: Produkční PDF input/output a resource validace
Priority: 3 (normal)
Created: 2026-10-10

Analysis:
[Implementační analýza](../../doc/modularization-analysis.md), sekce A03–A05; UML P04/P07.
Tento task je zadání budoucí implementace; založení neznamená hotovou funkci.

Evidence:
Statická revize 2026-10-10 a explicitní požadavky uživatele na modularizaci formátů/AI, provider-specific konfiguraci a autentizaci.

Affected files/symbols:
Nový formats/pdf/; legacy extract_blocks/make_block/block_metadata/export_html_images/FontResolver/layout_block/process_page/save_pdf_atomic a run_html_typesetting v translate.py.

Recommended change:
1. read(Path) vrací kanonický dokument s kompletními dosavadními styly, řádky TOC, hard breaks, page dimensions/rotation a source-template resource.
2. Nepovýšit dnešní zjednodušený get_text('blocks') adapter na production; použít dosavadní propracovanou extrakci.
3. write(XhtmlDocument,Path) interně řeší source-template podle dokumentu/base path a ověřuje SHA-256; explicitní remap jen stejný obsah.
4. PDF writer sestavit s rendererem/ResourceResolver v factory; obyčejný uživatel nesmí narazit na 'No PDF renderer configured'. Formátový modul neimportuje AI/GUI/frontu.
5. Zachovat offline sazbu, source geometry/font verifikaci, row/TOC/justification heuristiky, obrázky a atomický výstup. Přesun metod po odpovědnostech, ne nové heuristiky bez reprodukce.
6. Capabilities page range/export policy interně nakonfigurovat, veřejné read/write signatures zachovat.

Acceptance:
1. Input contract test malého trvalého PDF: IDs/text/styly/TOC rows/rotation/resources odpovídají očekávání.
2. Fake renderer integration ověří write API, správný dokument/target/resources a absenci Ollama/cloud volání.
3. Missing source/hash mismatch/locked target/disk-full nepřepíšou validní HTML/PDF; budoucí remap stejného hash funguje.
4. Dosavadní regrese obsahu/číslování nepřestanou procházet. Zvláštní ruční vizuální sazbu spustí uživatel dle M14 checklistu.

Constraints:
Před prací načíst projektový AGENTS.md a doc/tools.md. Respektovat současný dirty worktree. Kód src/, testy test/, trvalé fixture test/mock. Bez souhlasu žádný commit/push/live cloud nebo sazba knihy. Lokálního implementačního agenta do odvolání nespouštět.
Public boundaries typed; komentáře vysvětlují invarianty/důvody. JSONL bez secrets; bezpečné chybové zprávy. High-level strukturu a všechny procesy dokumentovat Mermaid class/sequence; aktualizovat centrální diagramy, neduplikovat je bez potřeby.
Každý task vlastní offline testy. Případné doplňující informace nebo důvod neprovedené části zapsat do datovaných comments, status zůstává z povoleného slovníku.

Implementation:
2026-10-10: PDF input vystavuje hash, source-template resource a page layout; output má injektovatelný renderer a hash validaci.

comments:
2026-10-10: M03 dokončen; PDF adapter testy prošly. Vizuální sazba knihy nebyla spuštěna.
2026-10-10: Založeno jako M03; specifikace a acceptance připraveny, žádná změna produkčního kódu.
2026-10-10: Sazbu celé knihy nyní nespouštět. Bez ruční evidence netvrdit vizuální shodu; v comments uvést rozsah offline ověření.
