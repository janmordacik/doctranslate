# 04 — Adaptery formátů

status: created
last change: 2026-10-10
dependency: 02-xhtml-contract.md, 03-translation-pipeline.md
group: 03-formats
type: feature
description: Oddělit načtení a výstup dokumentu přes adaptery; PDF ponechat jako plugin.
comments: 2026-10-10 — Zadání připraveno; agent nebyl spuštěn.

## Kontext

Načti context/00-scope.md, context/01-architecture.md,
context/02-contracts.md. Nepřepisuj celou legacy sazbu bez testu.

## Úkol

Vytvoř nebo sjednoť protokoly input/output adapterů a registraci podle media
type nebo přípony. PDF adapter smí znát PDF knihovnu; core nikoli. Přenos
metadata, bounding boxů, stránek a pořadí musí být explicitní. Připrav hranici
pro budoucí HTML/EPUB/DOCX bez jejich implementace.

## Akceptace

- adapter lze fake-nout v testu;
- neexistující, šifrovaný a textově prázdný PDF vstup má předvídatelnou chybu;
- format-independent pipeline funguje bez importu PDF;
- adapter nezapisuje neúplný výstup při chybě.

## Ověření

Unit test registrace, fake adapterů, chyb vstupu a minimální PDF smoke test,
jen pokud je PDF knihovna dostupná. PDF sazbu uživatelského dokumentu nespouštěj.
