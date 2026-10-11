status: done
last change: 2026-10-11
dependency: done/3-2026-10-11-navrh-pokrocileho-prekladoveho-modulu.md, 3-2026-10-11-pm-p06-job-volba-modulu.md, 3-2026-10-11-pm-p07-worker-engine-dispatch.md
group: translation/engine/gui-cli
type: feature
estimate:
  time: 50–90 min, implementace + cílené testy + review
  logical_lines: 200–340 včetně testů/dokumentace
  tokens: 3–5 k orientačních pracovních tokenů
  subtasks: S01–S03 níže
description: Volba modulu v GUI a CLI.

## Hierarchie a návrh

Parent: [Překladové moduly – implementace](3-2026-10-11-prekladove-moduly-implementace.md), větev integration, leaf P08.
[První návrh A19](../doc/modularization-analysis.md#a19-první-architektonický-návrh-v01-a-implementace-pro-lunu).
Task spouštět pouze po schválení návrhu a splnění dependency. Nejde o zadání
k přepsání celé aplikace nebo samostatnému přepracování architektury.

## Read – minimální kontext pro Lunu

QueueGui edit/copy/confirm/render, cli_main add parser, translate.cli_parser; A18 Volba modulu.

## Povolené soubory a symboly

- src/doctranslate/queue_app.py
- src/doctranslate/translate.py
- test/test_translation_selection_ui.py (nový)
- doc/user-manual.md

Nové cesty jsou návrh; existující obsah nejprve ověřit. Žádné změny v tmp,
test/mock fixture bez důvodu, cloud credentials, .git nebo vnořeném checkoutu.

## Požadovaná změna

GUI job kombo basic/advanced oddělit od provider/model; readonly detail, edit OK/Cancel, copy. CLI add i přímý běh dostanou --translator. Advanced disabled s důvodem dokud není registrovaný; přetrvává vybrané ID i při pollu.

## Samostatně ověřitelné kroky

| ID | Výsledek / kontrola | Čas | Řádky | Tokeny | Závislost |
|---|---|---:|---:|---:|---|
| S01 | Jedna uvedená zdrojová změna; kontrakt a invarianty odpovídají A19 | 28–50 min | 120–204  | 1.7–2.8 k | dependency tasku |
| S02 | Regresní/boundary testy a související dokumentace | 15–27 min | 80–136  | 1–1.8 k | S01 |
| S03 | Diff review, cílené testy a evidence do comments | 7–13 min | 0 nových | 0.3–0.4 k | S02 |

Řádky nejsou tvrdý limit; dělit další práci jen podle nezávislého chování.
Odhad není garantovaná doba agentní inference; větší scope nejprve popsat do comments.

## Acceptance a validace

- GUI/CLI ukládají stejnou selection, výchozí basic; cancel nezapisuje nic.
- EN/CS popisky, dostupnost s důvodem, polling neztratí selection ani neodeslané změny.
- Aktualizovat manuál; v comments uvést ruční GUI smoke jako ověření nebo zůstávající krok.

Cílená offline sada z kořene projektu:
C:\Python314\python.exe -m pytest test/test_translation_selection_ui.py test/test_queue_app.py test/test_cli_input.py -q
Nastavit PYTHONPATH na absolutní src dle doc/tools.md, nevytvářet live API volání.
Dále git diff --check; veřejné API docstringy, comments pro netriviální invarianty.
Změní-li se kontrakt/workflow, upravit autoritativní A19 UML/process index
(ne vytvářet duplicitní diagram do tasku).

## Forbidden scope

Žádný nový modální editor jobu, automatické odesílání GUI změn ani výběr podle provideru.
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


2026-10-11: P08 implementován. Queue CLI add a přímý legacy CLI přijímají --translator; GUI ukládá stejný translator_id jako job selection, výchozí basic, zobrazuje dostupnost modulu a advanced explicitně označuje jako nedostupný bez worker runneru. Copy/detail/readonly a staré test doubles zůstaly kompatibilní. Aktualizován uživatelský manuál.

2026-10-11: Validace: cílené testy 53 passed; celá sada 186 passed, 4 subtests passed. git diff --check bez nálezu.

2026-10-11: Omezení: GUI zatím nemá skutečný přepínač na aktivní advanced engine, protože composition root ho ještě neregistruje; CLI/GUI však volbu perzistují bez tichého fallbacku. Živé GUI smoke nebylo spuštěno v rámci offline testu.
