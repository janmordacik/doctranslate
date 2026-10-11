status: done
last change: 2026-10-11
dependency: done/3-2026-10-11-navrh-pokrocileho-prekladoveho-modulu.md, 3-2026-10-11-pm-p02-engine-kontrakt-a-registr.md, 3-2026-10-11-pm-p03-basic-engine.md, 3-2026-10-11-pm-p04-engine-checkpoint.md
group: translation/engine/integration
type: refactor
estimate:
  time: 60–100 min, implementace + cílené testy + review
  logical_lines: 200–340 včetně testů/dokumentace
  tokens: 3–5 k orientačních pracovních tokenů
  subtasks: S01–S03 níže
description: Bezztrátový legacy XHTML a batch bridge.

## Hierarchie a návrh

Parent: [Překladové moduly – implementace](3-2026-10-11-prekladove-moduly-implementace.md), větev integration, leaf P05.
[První návrh A19](../doc/modularization-analysis.md#a19-první-architektonický-návrh-v01-a-implementace-pro-lunu).
Task spouštět pouze po schválení návrhu a splnění dependency. Nejde o zadání
k přepsání celé aplikace nebo samostatnému přepracování architektury.

## Read – minimální kontext pro Lunu

xhtml_document_from_page_groups, block_metadata, prepare_text_translation/restore_text_translation, translate_batch, write_translation_html.

## Povolené soubory a symboly

- src/doctranslate/integration/__init__.py (nový)
- src/doctranslate/integration/translation_bridge.py (nový)
- src/doctranslate/translate.py
- test/test_translation_bridge.py (nový)

Nové cesty jsou návrh; existující obsah nejprve ověřit. Žádné změny v tmp,
test/mock fixture bez důvodu, cloud credentials, .git nebo vnořeném checkoutu.

## Požadovaná změna

Převést legacy groups/resources/fragmenty na canonical view a zpět bez jiného layoutu. LegacyBatchAdapter plní BatchExecutor a zachová existující prompt. Ruční override/cache importovat pouze po současné validaci. Připravit bridge, ještě nepřepínat Worker.

## Samostatně ověřitelné kroky

| ID | Výsledek / kontrola | Čas | Řádky | Tokeny | Závislost |
|---|---|---:|---:|---:|---|
| S01 | Jedna uvedená zdrojová změna; kontrakt a invarianty odpovídají A19 | 33–55 min | 120–204  | 1.7–2.8 k | dependency tasku |
| S02 | Regresní/boundary testy a související dokumentace | 18–30 min | 80–136  | 1–1.8 k | S01 |
| S03 | Diff review, cílené testy a evidence do comments | 9–15 min | 0 nových | 0.3–0.4 k | S02 |

Řádky nejsou tvrdý limit; dělit další práci jen podle nezávislého chování.
Odhad není garantovaná doba agentní inference; větší scope nejprve popsat do comments.

## Acceptance a validace

- Round-trip více span/br, math/literal, bbox/rotation a images neztratí informaci.
- Basic executor payload se shoduje se současným pro reprezentativní fake fixture.
- Neoznačené staré výsledky smí importovat pouze basic; neblokovat zvolené nové output cesty.

Cílená offline sada z kořene projektu:
C:\Python314\python.exe -m pytest test/test_translation_bridge.py test/test_layout_and_models.py test/test_xhtml_codec.py -q
Nastavit PYTHONPATH na absolutní src dle doc/tools.md, nevytvářet live API volání.
Dále git diff --check; veřejné API docstringy, comments pro netriviální invarianty.
Změní-li se kontrakt/workflow, upravit autoritativní A19 UML/process index
(ne vytvářet duplicitní diagram do tasku).

## Forbidden scope

Nepřepisovat PDF sazbu ani exportní HTML schéma; při nemožném mappingu zapsat důkaz a zastavit task.
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

2026-10-11: Přidán integration/translation_bridge.py a LegacyBatchAdapter. Bridge převádí legacy page groups na canonical XhtmlDocument a zpět, zachovává ID/pořadí/markup/bbox/rotaci/styly/row layout/resources a odmítá mapping mismatch. Worker ani PDF sazba nebyly přepnuty.
2026-10-11: Cílené testy: 13 passed; celá offline sada: 174 passed, 4 subtests passed. git diff --check bez chyb. Explicitní překlad aktualizuje i textovou reprezentaci; žádné otevřené problémy v rozsahu tasku.
