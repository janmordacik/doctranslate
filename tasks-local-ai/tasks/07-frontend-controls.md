# 07 — Symetrické CLI a GUI

status: created
last change: 2026-10-10
dependency: 05-queue-store.md, 06-worker-lifecycle.md
group: 05-frontend
type: feature
description: Poskytnout GUI bez parametrů a CLI nad stejným QueueStore s jasně oddělenými akcemi.
comments: 2026-10-10 — Zadání připraveno; agent nebyl spuštěn.

## Kontext

Načti context/00-scope.md, context/01-architecture.md,
context/02-contracts.md.

## Úkol

Navrhni přehledné GUI se skupinami Worker, Job, General a Workdir. V seznamu
jobů zobraz stav, pořadí a první řádek globálního stopu. Job podporuje Add,
Pause, Prepare, Delete, Up/Down. Worker podporuje Start, Update, Stop.
Refresh, jazyk a workdir patří do General/Workdir. Status je pod seznamem.

Editace GUI jsou lokální až do Update; Start je neodesílá. CLI add změnu
automaticky odešle. Zavření s neodeslanou editací varuje. Jazyk cs/en se
inicializuje locale a lze jej změnit.

## Akceptace

- GUI a CLI používají stejný kontrakt a transakce;
- Update startuje worker, pokud neběží;
- Refresh nepřepíše neodeslané změny bez varování;
- pořadí se mění šipkami, nikoli prioritním číslem;
- workdir se zobrazuje a ukládá pouze na jednom místě;
- testy ověří command mapping a neodeslané změny.

## Ověření

CLI parser testy a GUI controller testy s fake store/workerem. Interaktivní
desktop ověření je doplňkové, ne náhrada unit testů.
