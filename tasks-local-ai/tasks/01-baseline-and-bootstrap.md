# 01 — Baseline a bootstrap

status: created
last change: 2026-10-10
dependency: none
group: 01-foundation
type: feature
description: Zjistit skutečný stav checkoutu a zajistit spustitelný, diagnostický bootstrap bez předpokladu volitelných závislostí.
comments: 2026-10-10 — Zadání připraveno; agent nebyl spuštěn.

## Kontext

Načti context/00-scope.md, context/03-operational-constraints.md a
context/04-quality.md. Nepředpokládej žádnou funkci z jiné dokumentace.

## Úkol

Prozkoumej strukturu projektu, vstupní body a testy. Zajisti, aby hlavní
launcher uměl rozlišit chybějící Python, starou verzi a chybějící volitelné
závislosti. Základní příkaz pro nápovědu nebo status nesmí vyžadovat PDF
knihovnu ani Ollamu, pokud to není nutné.

## Akceptace

- baseline je zaznamenán v task komentáři, ne ve zdrojovém kódu jako domněnka;
- chyby bootstrapu mají nenulový exit code a stručnou příčinu;
- testy pokrývají dostupnost interpreteru a lazy import volitelných závislostí;
- změny se netýkají fronty, workeru ani PDF layoutu.

## Ověření

Spusť cílené bootstrap testy a dostupnou offline suite. Při absenci Pythonu
nebo test runneru uveď přesný workaround, ale nevydávej task za hotový.
