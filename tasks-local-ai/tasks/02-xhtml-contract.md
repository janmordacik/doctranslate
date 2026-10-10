# 02 — XHTML kontrakt

status: created
last change: 2026-10-10
dependency: 01-baseline-and-bootstrap.md
group: 02-core
type: feature
description: Vytvořit nebo zpřesnit formátově nezávislý XHTML dokument s metadaty, bloky a stabilní validací.
comments: 2026-10-10 — Zadání připraveno; agent nebyl spuštěn.

## Kontext

Načti context/00-scope.md, context/01-architecture.md,
context/02-contracts.md a context/04-quality.md.

## Úkol

Navrhni minimální datové typy/protokoly pro metadata dokumentu, blok textu a
XHTML reprezentaci. Přidej validaci povinných polí, pořadí bloků, stabilních ID,
stránek a bezpečné serializace. Jádro nesmí importovat PDF knihovnu.

## Akceptace

- dokument lze načíst, validovat a znovu serializovat bez ztráty metadat;
- blok má stabilní ID, stránku, pořadí, text a volitelný markup/layout;
- nevalidní cardinalita nebo chybějící metadata skončí čitelnou chybou;
- testy dokazují nezávislost core na PDF závislosti.

## Ověření

Unit testy modelu, serializace, nevalidních vstupů a izolovaného importu.
