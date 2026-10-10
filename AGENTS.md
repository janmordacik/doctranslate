# AGENTS.md

## Projektová pravidla

- Na začátku každé práce v tomto projektu načti `doc/tools.md` a použij v něm uvedené recepty.
- Každé nové opakovatelné selhání nástroje nebo ověřený workaround doplň do `doc/tools.md` podle šablony evidence.
- `doc/tools.md` je provozní kuchařka nástrojů, nikoli log aplikačních chyb.
- Před změnami ověř stav pracovního stromu; bez výslovného souhlasu uživatele nevytvářej commit ani neposílej změny do vzdáleného repozitáře.
- Do odvolání nepoužívej lokálního implementačního agenta Qwen/Continue pro tento projekt; implementaci, revizi i testování prováděj přímo.

## High-level architektura a implementační zadání

- High-level strukturu aplikace, veřejné kontrakty a závislosti povinně dokumentuj Mermaid UML classDiagram.
- Všechny high-level aplikační procesy povinně popiš Mermaid UML sequenceDiagram. Veď index procesů s odkazy na diagramy; zahrň důležité alternativy, chyby, přerušení a obnovu.
- Rozlišuj aktuální implementaci a cílový návrh. Diagramy aktualizuj s implementací a zahrň je do akceptačních kritérií příslušných tasků.
- Udržuj nejvyšší užitečnou úroveň, ne diagram každé privátní metody. Tasky odkazují na autoritativní diagramy, nevytvářej redundantní kopie.
- Zadání modularizace a procesní index jsou v doc/modularization-analysis.md; skutečný stav implementace vede status/comments v tasks/.
- Globální rozšíření pravidla pro SW projekty je připravené v doc/global-uml-rule.patch. Zápis ~/.codex/AGENTS.md v této relaci selhal i po udělených oprávněních; tento projektový fallback zůstává povinný, dokud nebude globální patch aplikován.

## Komentáře a docstringy

- Každý veřejný modul, třída a funkce musí mít stručný docstring popisující odpovědnost,
  vstupy, výstup a relevantní chyby nebo vedlejší účinky.
- Komentáře v netriviální logice vysvětlují především důvod, invariant nebo omezení;
  neopisují syntax ani název proměnné.
- Povinně komentuj stavovou, bezpečnostní, výkonnostní a kompatibilitní logiku,
  zejména frontu/worker, zámky, rušení a obnovu, autentizaci, checkpointy a PDF layout.
- Zakomentovaný starý kód se neudržuje. Zastaralý komentář se při změně kódu opraví
  nebo odstraní. Logování nenahrazuje komentář: log popisuje běh, komentář vysvětluje návrh.
- Při review kontroluj dostatečnou dokumentaci veřejných kontraktů a netriviálních bloků;
  pravidlo se nevynucuje počtem komentářů ani mechanickým komentováním samozřejmého kódu.

Další obecná pravidla práce řídí nadřazené instrukce Codexu.
