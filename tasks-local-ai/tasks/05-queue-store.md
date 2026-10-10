# 05 — JSON repository a zámky

status: created
last change: 2026-10-10
dependency: 01-baseline-and-bootstrap.md
group: 04-queue
type: feature
description: Implementovat bezpečný QueueStore nad JSON souborem bez databáze a plnotučného IPC.
comments: 2026-10-10 — Zadání připraveno; agent nebyl spuštěn.

## Kontext

Načti context/01-architecture.md, context/02-contracts.md,
context/03-operational-constraints.md.

## Úkol

Implementuj načítání, validaci, revision-aware transakce a atomické zápisy
fronty. Použij krátký .lock pouze pro zápis. Zaveď zálohu a bezpečné
zpracování poškozeného JSON. Rozlišuj zámek fronty od singleton zámku workeru.
Nikdy nedrž zámek během Ollama/PDF práce.

## Akceptace

- souběžné zápisy neztrácí novější runtime stav;
- ENOSPC, readonly adresář a selhání replace zachovají poslední platný soubor;
- stale lock nelze převzít pouze podle stáří;
- poškozený hlavní soubor lze nahradit pouze validní zálohou a stav je oznámen;
- transakce nepovolí duplicitní ID, neznámý state ani poškozenou revision.

## Ověření

Spusť konkurenční, stale-lock, backup, revision a storage fault-injection testy.
