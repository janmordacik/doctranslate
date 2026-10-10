# 10 — Integrační ověření a dokumentace

status: created
last change: 2026-10-10
dependency: 02-xhtml-contract.md, 03-translation-pipeline.md, 04-format-adapters.md, 05-queue-store.md, 06-worker-lifecycle.md, 07-frontend-controls.md, 08-ollama-discovery.md, 09-observability-and-errors.md
group: 08-release
type: test
description: Ověřit propojení vrstev a udržovat stručnou dokumentaci bez předstírání živého modelu nebo PDF sazby.
comments: 2026-10-10 — Zadání připraveno; agent nebyl spuštěn.

## Kontext

Načti všechny context soubory, ale stav zdrojového kódu vždy zjisti testem a
inspekcí. Tento task je poslední integrační brána, ne místo pro velký refaktor.

## Úkol

Přidej malé integrační scénáře pro CLI/GUI → QueueStore → Worker → fake
translation backend → XHTML/adapter. Ověř restart, stop, pause, revision,
výpadek backendu a obnovu. Aktualizuj projektovou dokumentaci pouze o skutečně
ověřené chování a jasně odděl offline test od živého Ollama/PDF ověření.

## Akceptace

- offline suite je reprodukovatelná bez Ollamy a bez konkrétního modelu;
- každý integrační scénář má očekávaný stav fronty a exit/status výsledek;
- dokumentace obsahuje aktuální strukturu, příkazy a známé limity;
- živý překlad ani PDF sazba se nespouští bez explicitního pokynu uživatele;
- diff neobsahuje generované runtime artefakty.

## Ověření

Spusť cílené i celkové testy dostupné v checkoutu, zkontroluj git diff --check
a uveď přesný počet úspěšných/neúspěšných testů.
