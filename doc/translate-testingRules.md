# Translate — plán a stav implementace

## Cíl

Refaktorovat jednoúčelový PDF překladač na obecnější dávkovou pipeline:

1. XHTML je meziformát překladového jádra a nese metadata pro renderer.
2. PDF vstup a výstup jsou adaptery/pluginy.
3. Backend překladu je konfigurovatelný.
4. Logování, trace, výjimky a checkpointy jsou součástí běhu.
5. GUI/CLI spravují JSON frontu a samostatný worker.
6. PDF layout zachovává pořadí bloků a běžné odstavce zarovnává do obou okrajů.
7. GUI má konfigurovatelný workdir a lokalizaci cs/en.

## Fáze

| Fáze | Rozsah | Stav |
|---|---|---|
| 0 | Přístup k repozitáři, lokální Git, diagnostika agenta | hotovo |
| 1 | Core XHTML kontrakt a PDF adaptery | hotovo |
| 2 | CLI, konfigurace, logování, trace, checkpointy | hotovo |
| 3 | Zachování layoutu a velikosti PDF | částečně; heuristika zarovnání hotová, vizuální kontrola čeká |
| 4 | Runner, testy a základní dokumentace | hotovo |
| 5 | JSON fronta, GUI, worker, locky a restart | hotovo; integrační běh s reálnou Ollamou čeká |
| 6 | Workdir, konfigurace a lokalizace GUI | hotovo |
| 7 | Přímé zapojení nové pipeline do legacy sazby | čeká |
| 8 | Benchmark TranslateGemma/Qwen a vizuální regresní test | čeká |


## Akceptační kritéria

- Spuštění přes translate.cmd zůstává použitelné; zdrojové moduly jsou pouze v src/doctranslate/.
- Bez parametrů se otevře GUI fronty.
- add automaticky uloží změnu a nastartuje worker.
- start jen startuje/resumuje worker.
- stop zastaví worker po dokončení aktuální Ollama dávky.
- in_progress má přednost před prepared; prepared respektuje pouze pořadí seznamu.
- paused a failed se automaticky nespouštějí.
- GUI drží editace v paměti až do Update, označí neodeslané změny a upozorní při zavření.
- GUI seskupuje Worker/Job/Refresh/Workdir ovládání, podporuje Delete a lokalizaci cs/en. Modelový combobox načítá lokální nabídku Ollamy a zachová fallback při nedostupném endpointu.
- Bez konfigurace GUI použije aktuální pracovní adresář; workdir a jazyk se uloží explicitní akcí.
- Více zapisujících procesů serializuje zápis přes queue.lock.
- Více workerů nepoběží současně díky worker.lock.
- Queue JSON se zapisuje atomicky a má .bak zálohu.
- Core testy a queue unit testy nevyžadují živou Ollamu.
- Regresní test ověřuje odřádkování TOC se samostatnými čísly podkapitol; opravené HTML strany 4–6 prošly validací všech 5383 bloků.
- translate.md obsahuje Mermaid class a sequence diagramy a aktuální stav.
- Agent nevytváří commit ani vzdálený push.

## Protokol restartu

- Repo: C:/Users/mordacik/Documents/Codex/doctranslate
- Zdrojový balíček: src/doctranslate/; dokumentace: doc/; testovací data: test/mock/; lokální pracovní artefakty: tmp/; runtime fronta: nastavený workdir/
- Pracovní soubory lokálního agenta: tmp/tmp_local_agent_in.md, tmp/tmp_local_agent_out.log; nesmazat automaticky.
- Qwen diagnostika proběhla; delegace skončila před implementací kvůli nekompatibilnímu cn serve.
- Poslední validace: unittesty, explicitní kompilace Python modulů a CLI status byly ověřeny; integrovaná offline regrese prošla 16 kontrolami.
- Před dalším krokem zopakovat unittest, py_compile a git diff --check.
- Bez externího vstupu lze pokračovat pouze unit/integration testy s fake backendem.

## Odložené úkoly vyžadující vstup nebo prostředí

- reprezentativní vstupní/výstupní PDF stránka pro vizuální regresní test;
- dostupná Ollama instance s translategemma:12b a měřicí vzorek;
- rozhodnutí, zda výstupní PDF a překladové artefakty patří do repozitáře;
- výslovný pokyn k vytvoření commitu nebo pushi.
- Překlad zachovává číselný prefix kapitol a podkapitol podle zdrojového PDF; regresní test kryje opravu 7.5/7.6.
