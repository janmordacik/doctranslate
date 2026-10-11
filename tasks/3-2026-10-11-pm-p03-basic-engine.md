status: created
last change: 2026-10-11
dependency: 3-2026-10-11-navrh-pokrocileho-prekladoveho-modulu.md, 3-2026-10-11-pm-p02-engine-kontrakt-a-registr.md
group: translation/engine/basic
type: feature
estimate:
  time: 60–100 min, implementace + cílené testy + review
  logical_lines: 200–320 včetně testů/dokumentace
  tokens: 3–5 k orientačních pracovních tokenů
  subtasks: S01–S03 níže
description: Basic engine nad injektovaným dávkovým executorem.

## Hierarchie a návrh

Parent: [Překladové moduly – implementace](3-2026-10-11-prekladove-moduly-implementace.md), větev foundation, leaf P03.
[První návrh A19](../doc/modularization-analysis.md#a19-první-architektonický-návrh-v01-a-implementace-pro-lunu).
Task spouštět pouze po schválení návrhu a splnění dependency. Nejde o zadání
k přepsání celé aplikace nebo samostatnému přepracování architektury.

## Read – minimální kontext pro Lunu

A19 A03; translate_batch/fill_translation_cache pouze relevantní úseky, stable IDs a fragment schema.

## Povolené soubory a symboly

- src/doctranslate/translation/basic.py (nový)
- src/doctranslate/translation/contracts.py
- test/test_basic_translation_engine.py (nový)

Nové cesty jsou návrh; existující obsah nejprve ověřit. Žádné změny v tmp,
test/mock fixture bez důvodu, cloud credentials, .git nebo vnořeném checkoutu.

## Požadovaná změna

Zabalit lineární řídicí tok za TranslationEngine; BatchExecutor dostává zachované fragmenty a vrací strukturované výsledky. Executor fake či legacy adapter je injektovaný. Engine validuje výsledek a publikuje přijaté dávky, nepřebírá PDF.

## Samostatně ověřitelné kroky

| ID | Výsledek / kontrola | Čas | Řádky | Tokeny | Závislost |
|---|---|---:|---:|---:|---|
| S01 | Jedna uvedená zdrojová změna; kontrakt a invarianty odpovídají A19 | 33–55 min | 120–192  | 1.7–2.8 k | dependency tasku |
| S02 | Regresní/boundary testy a související dokumentace | 18–30 min | 80–128  | 1–1.8 k | S01 |
| S03 | Diff review, cílené testy a evidence do comments | 9–15 min | 0 nových | 0.3–0.4 k | S02 |

Řádky nejsou tvrdý limit; dělit další práci jen podle nezávislého chování.
Odhad není garantovaná doba agentní inference; větší scope nejprve popsat do comments.

## Acceptance a validace

- Fake executor udrží dávky, pořadí, fragment/literal IDs a text/markup.
- Cancel před dávkou i po návratu nedovolí přijmout opožděný výsledek.
- Prázdné a nepřekladové bloky zachová; retry je omezený, ne další nekonečná smyčka.

Cílená offline sada z kořene projektu:
C:\Python314\python.exe -m pytest test/test_basic_translation_engine.py test/test_ai_translation.py test/test_translate_core.py -q
Nastavit PYTHONPATH na absolutní src dle doc/tools.md, nevytvářet live API volání.
Dále git diff --check; veřejné API docstringy, comments pro netriviální invarianty.
Změní-li se kontrakt/workflow, upravit autoritativní A19 UML/process index
(ne vytvářet duplicitní diagram do tasku).

## Forbidden scope

Neměnit prompt nebo batching algoritmus basic bez regresního důkazu; neimportovat legacy do core.
Necommitovat, nepushovat, nespouštět lokální Qwen/Continue. Runtime/GUI/live
ověření mimo offline testy uvést jako samostatný krok, nikoli tvrdit hotové.

## Restart a comments

S01: created
S02: created
S03: created
Actual time: unavailable
Actual logical lines: unavailable
Actual tokens: unavailable

2026-10-11: Připraveno pro Lunu jako jeden bounded leaf. Implementace nezačala;
dotaz/blokátor/důvod neprovedení doplnit sem, nikoli odhadnout mimo kontrakt.
