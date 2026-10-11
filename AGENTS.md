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
- Globální rozšíření pravidla pro SW projekty je zapsané v ~/.codex/AGENTS.md; tento projektový fallback pravidlo opakuje kvůli jednoznačnému kontextu projektu.

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

## Plánování tasků a odhady

- Každý nový nebo podstatně rozšířený task musí mít plán rozdělený na samostatné,
  pochopitelné a reviewovatelné subtasks. Jeden subtask představuje jednu
  změnu chování, kontrakt, invariant nebo jiný sémanticky soudržný výsledek.
- Zachovávají se původní orientační řádková kritéria: interaktivní krok je
  přibližně 40 logických řádků a samostatně reviewovatelný task přibližně
  200–400 logických řádků. Dělení se řídí chováním a sémantickou atomicitou,
  nikoli mechanicky počtem řádků.
- Pro plánování lze rozsah hrubě převést na čas: interaktivní krok kolem
  40 řádků obvykle odpovídá přibližně 15–30 minutám čisté práce; task kolem
  200–400 řádků přibližně 2–4 hodinám. Složitost, integrace, testy a neznámý
  kód mají přednost před tímto převodem.
- Každý subtask musí uvést orientační čas, rozsah logických řádků, případně
  tokenový rozpočet, závislosti, očekávaný výsledek a způsob ověření. Tokeny
  jsou doplňkový rozsahový odhad, nikoli pevný limit.
- Po dokončení se podle možností doplní skutečný čas, rozsah změny a výsledek
  validace. Pokud subtask překročí odhad, zapíše se důvod do comments a plán
  se upraví, nikoli mechanicky rozbije.

Další obecná pravidla práce řídí nadřazené instrukce Codexu.
