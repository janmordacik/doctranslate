status: created
last change: 2026-10-11
type: test
group: testing/integration/advanced-ollama/pdf
dependency: 2-2026-10-11-ollama-runtime-capability-logging

description: >-
  Připravit explicitně spouštěný integrační smoke test, který ověří skutečný
  překlad PDF přes advanced modul, Ollamu a model translategemma:4b až po
  výsledné PDF. Test musí být izolovaný od běžné uživatelské fronty, před
  každým pokusem odstranit pouze určené testovací XHTML a PDF výstupy, čekat
  na dokončení workeru, zachovat diagnostické artefakty a umožnit opakování
  po opravě nalezené chyby.

scope:
- Konfigurovatelný vstupní PDF, výstupní PDF, XHTML, queue soubor a pracovní adresář.
- Výchozí scénář: translator_id=advanced, provider=ollama, model=translategemma:4b,
  phase=both, source=en, target=cs.
- Před každým attempt odstranit jen testovací XHTML/PDF; zdrojové PDF a cizí
  soubory nesmí být mazány.
- Spustit worker přes podporované CLI/runner rozhraní, pollovat stav jobu a
  rozlišit done, failed, paused, timeout a neočekávané ukončení workeru.
- Po každém pokusu uložit stav fronty, worker log, run log, error sidecar,
  velikosti výstupů a dobu jednotlivých fází.
- Při chybě vypsat přesnou příčinu a relevantní logové události; opravu kódu
  řeší nadřazený implementační cyklus, nikoli automatický skript bez review.
- Live test nesmí být součástí výchozí pytest sady; spouští se explicitním
  příkazem a předem ověřuje dostupnost Pythonu, Ollamy, modelu a volného místa.

logging_requirements:
- Korelační identifikátor běhu a attemptu.
- Job ID, translator, provider, model, phase a cesty k artefaktům.
- Začátek/konec načtení vstupu, každého AI batch requestu, HTML fáze a PDF fáze.
- Doba požadavku, HTTP stav, velikost odpovědi, počet vstupních/výstupních
  bloků, retry, parse/validation error a stručný výřez diagnostiky bez nutnosti
  ručně dohledávat nečitelný traceback.
- Informace z Ollama API o modelu, runneru, kontextu, velikosti a size_vram,
  pokud jsou dostupné.

plan and estimates:
- S01: Vytvořit izolovaný explicitní live runner s CLI parametry, bezpečným
  úklidem testovacích výstupů a předběžnou kontrolou prostředí. Estimate: 15
  minut, 80 logických řádků, 900 tokenů. Dependencies: none.
- S02: Napojit runner na advanced queue job, polling workeru a timeout/recovery
  stavy. Estimate: 15 minut, 90 logických řádků, 1100 tokenů. Dependencies: S01.
- S03: Rozšířit provozní logování o korelaci, fáze, batch metriky a diagnostiku
  odpovědi. Estimate: 20 minut, 120 logických řádků, 1400 tokenů. Dependencies: S02.
- S04: Přidat offline fixture/contract testy, dokumentaci příkazu a ověřit živý
  běh s translategemma:4b. Estimate: 15 minut, 80 logických řádků, 900 tokenů.
  Dependencies: S01, S02, S03.

acceptance:
- Explicitní příkaz provede celý scénář až po ověřitelné výsledné PDF.
- Druhý attempt začíná s odstraněným předchozím testovacím XHTML/PDF a stejným
  izolovaným queue souborem.
- Chyba je reprodukovatelně spojena s jobem, attemptem, fází a konkrétním
  batch/request logem.
- Test nezasáhne uživatelskou frontu ani nemaže vstupní PDF.
- Selhání dostupnosti Pythonu, Ollamy, modelu nebo disku skončí s konkrétním
  diagnostickým stavem ještě před spuštěním překladu.
- Offline testy projdou bez Ollamy; live test se spouští pouze explicitně.
- Dokumentace popisuje příkaz, mazací rozsah, očekávané artefakty a postup po
  chybě. High-level workflow je doplněn odpovídajícím Mermaid sequenceDiagram
  pouze v autoritativní technické dokumentaci.

comments:
- 2026-10-11: Task založen na požadavku ověřit advanced PDF překlad iterativně
  až do úspěchu a rozšířit logy pro následnou opravu. Implementace zatím
  nezačala; commit obsahuje pouze zadání tasku.
