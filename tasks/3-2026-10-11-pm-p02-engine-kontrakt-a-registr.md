status: done
last change: 2026-10-11
dependency: done/3-2026-10-11-navrh-pokrocileho-prekladoveho-modulu.md, 3-2026-10-11-pm-p01-jobrunner-prvni-vystup.md
group: translation/engine/contracts
type: feature
estimate:
  time: 40–70 min, implementace + cílené testy + review
  logical_lines: 160–260 včetně testů/dokumentace
  tokens: 2–4 k orientačních pracovních tokenů
  subtasks: S01–S03 níže
description: Společný kontrakt engine a explicitní registr.

## Hierarchie a návrh

Parent: [Překladové moduly – implementace](3-2026-10-11-prekladove-moduly-implementace.md), větev foundation, leaf P02.
[První návrh A19](../doc/modularization-analysis.md#a19-první-architektonický-návrh-v01-a-implementace-pro-lunu).
Task spouštět pouze po schválení návrhu a splnění dependency. Nejde o zadání
k přepsání celé aplikace nebo samostatnému přepracování architektury.

## Read – minimální kontext pro Lunu

A19 A02/A03; AiBackend a XhtmlDocument; FormatDescriptor/Registry jen jako vzor, nepřejmenovat jej.

## Povolené soubory a symboly

- src/doctranslate/translation/__init__.py (nový)
- src/doctranslate/translation/contracts.py (nový)
- src/doctranslate/translation/registry.py (nový)
- test/test_translation_registry.py (nový)

Nové cesty jsou návrh; existující obsah nejprve ověřit. Žádné změny v tmp,
test/mock fixture bez důvodu, cloud credentials, .git nebo vnořeném checkoutu.

## Požadovaná změna

Definovat TranslationOptions/Context/Result, typed error/cancel, descriptor a register/list/create. Účinné translator_options validovat odděleně od provideru. Advanced dokud není hotový nedostupný; factory injektovat.

## Samostatně ověřitelné kroky

| ID | Výsledek / kontrola | Čas | Řádky | Tokeny | Závislost |
|---|---|---:|---:|---:|---|
| S01 | Jedna uvedená zdrojová změna; kontrakt a invarianty odpovídají A19 | 22–39 min | 96–156  | 1.1–2.2 k | dependency tasku |
| S02 | Regresní/boundary testy a související dokumentace | 12–21 min | 64–104  | 0.7–1.4 k | S01 |
| S03 | Diff review, cílené testy a evidence do comments | 6–10 min | 0 nových | 0.2–0.4 k | S02 |

Řádky nejsou tvrdý limit; dělit další práci jen podle nezávislého chování.
Odhad není garantovaná doba agentní inference; větší scope nejprve popsat do comments.

## Acceptance a validace

- Unknown/duplicate ID, neplatné options a unavailable mají čitelný code/reason.
- List nevytváří model ani transport; fake basic implementuje stejný protokol.
- Core neimportuje fitz, translate.py, queue_app ani Tk; veřejné symboly mají docstring.

Cílená offline sada z kořene projektu:
C:\Python314\python.exe -m pytest test/test_translation_registry.py test/test_translate_core.py -q
Nastavit PYTHONPATH na absolutní src dle doc/tools.md, nevytvářet live API volání.
Dále git diff --check; veřejné API docstringy, comments pro netriviální invarianty.
Změní-li se kontrakt/workflow, upravit autoritativní A19 UML/process index
(ne vytvářet duplicitní diagram do tasku).

## Forbidden scope

Nevytvářet dynamické plugin discovery, měnit AI autentizaci nebo zavádět framework.
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

2026-10-11: Implementováno translation/contracts.py, translation/registry.py a veřejný export balíčku. Registry je explicitní, deterministický, bez dynamického discovery; validuje JSON options, typy, duplicate/unknown/unavailable a factory dostává dependencies.
2026-10-11: Doplněna hraniční validace jazyků a target_variant. Cílené testy: 14 passed; celá offline sada: 161 passed, 4 subtests passed. git diff --check bez chyb. Kontrakt A19/UML se nezměnil; P03 navazuje základním enginem.
