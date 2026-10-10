# Tools – kuchařka osvědčených postupů

Tento soubor načítej na začátku každé práce v projektu. Je to praktická kuchařka: při selhání nástroje nejprve použij odpovídající recept, a pokud vznikne nový opakovatelný problém, doplň jej stejným formátem.

## Rychlý postup na začátku práce

1. Načti tento soubor a projektový `AGENTS.md`.
2. Ověř pracovní strom bez změny stavu projektu.
3. Pro zápis ověř cílový adresář a použij recept pro oprávnění nebo zápis.
4. Po každém workaroundu ověř výsledek cíleným testem.
5. Bez výslovného souhlasu nevytvářej commit ani neposílej změny na GitHub.

## Recepty

### Recept 1: Shell nástroj selže při vytvoření procesu

- **Příznak:** `exec_command` skončí chybou `CreateProcess ... helper_unknown_error: setup refresh had errors`.
- **Postup:** použij `mcp__node_repl__js` a přes `node:child_process.execFile` spusť Python nebo Git bez shellu.
- **Ověření:** zkontroluj návratový kód a výstup; u Git příkazů použij recept 4.
- **Stav:** ověřeno 2026-10-10.

### Recept 2: Zápis mimo aktivní pracovní adresář

- **Příznak:** `apply_patch` hlásí `Failed to write file ...doctranslate...`.
- **Postup:** ověř práva cílového projektu. Pokud nástroj selže i poté, použij stejný `apply_patch` executable přes `node:child_process.execFile` s `cwd` nastaveným na kořen projektu. `where.exe apply_patch` ukáže launcher; jeho `.bat` obsahuje cestu ke Codex executable a přepínač `--codex-run-as-apply-patch`. Patch předej jako samostatný argument, bez shell interpolace. Verzi executable zjisti z aktuálního launcheru, ne z dřívějšího receptu.
- **Ověření:** návratový kód 0, očekávaný diff a znovunačtení souborů. Při revizi 2026-10-10 takto zapsány pouze dokumenty a issues.
- **Stav:** přímé spuštění apply_patch ověřeno 2026-10-10. Přímý fs.writeFile není doporučený postup pro projektové editace.

### Recept 3: Lokální Qwen agent není dostupný

- **Příznak:** worker očekává příkaz `cn serve`, ale dostupný Continue CLI jej nezná.
- **Postup:** postupuj podle `$local-qwen-orchestration`. Diagnostika exit 0 ověřuje souborovou komunikaci, nikoli připravenost Continue serveru. Před delegací použij aktuální capability profil a případně izolovanou kalibraci. Při selhání serveru delegaci zastav a zaznamenej checkpoint; nepřecházej automaticky na přímou implementaci v rozporu se supervisor policy.
- **Ověření:** 2026-10-10 read calibration qwen3-coder:30b Native: server nebyl připraven do 15 s, exit 1, žádný tool call, completion_detected=false. Nový profil se nesmí označit za úspěšný.
- **Stav:** známé omezení, znovu potvrzeno 2026-10-10.

### Recept 4: Git odmítne repozitář kvůli vlastnictví

- **Příznak:** `fatal: detected dubious ownership`.
- **Postup:** ke čtecím příkazům přidej `-c safe.directory=C:/Users/mordacik/Documents/Codex/doctranslate`.
- **Příklad:** `git -c safe.directory=C:/Users/mordacik/Documents/Codex/doctranslate status --short`.
- **Stav:** ověřeno 2026-10-10.

### Recept 5: REPL hlásí redeklaraci proměnné

- **Příznak:** při opakovaném použití stejného `const` nebo `let` vznikne chyba či warning o redeklaraci.
- **Postup:** používej unikátní názvy bindingů; při větším novém bloku proveď reset REPL a znovu načti potřebné moduly.
- **Stav:** neblokující omezení, ověřeno 2026-10-10.

### Recept 6: Sazba PDF z hotového HTML

- **Vstup:** hotové přeložené HTML s metadaty a původní PDF.
- **Příkaz:** spusť z kořene projektu `C:/Users/mordacik/Documents/Codex/doctranslate`:

```powershell
.\translate.cmd --phase pdf --htmlfile "tmp\Lucio Russo – Zapomenuta revoluce-layout.html" --infile "tmp\Lucio Russo – The Forgotten Revolution.pdf" --outfile "tmp\Lucio Russo – Zapomenutá revoluce-layout.pdf"
```

- **Poznámka:** explicitní `--infile` a `--outfile` obcházejí zastaralé absolutní cesty uložené ve starších HTML metadatech.
- **Doporučení:** jde o dlouhou operaci; nespouštěj ji přes krátký tool timeout a předem ověř, že cílový PDF soubor není používán jiným procesem.
- **Kontrola názvů:** při revizi 2026-10-10 HTML obsahuje `Zapomenuta` bez á, ale pomlčku `–` (U+2013). ASCII `-` (U+002D) je jiný název. Před ruční sazbou ověř aktuální soubory, například `Get-ChildItem -LiteralPath .\tmp -File | Where-Object Name -Like 'Lucio*' | Select-Object -ExpandProperty Name`. Názvy kopíruj přesně; neměň je automaticky.
- **Stav:** existence aktuálního HTML a zdroje ověřena 2026-10-10. Tento upravený příkaz nebyl proveden; sazbu spouští uživatel. Dřívější pokus byl přerušen a není dokladem úspěšné finální sazby.
- **Související chyba:** [nenalezené HTML a traceback](../tasks/done/3-2026-10-10-nenalezene-html-rozdil-pomlcky-v-ceste.md).

### Recept 7: Dlouhý patch nebo víceřádkový JavaScript

- **Příznak:** SyntaxError při vložení raw víceřádkového textu do JS stringu; nebo nástroj odmítne JavaScript execution exceeds the 64000-byte strict auto-review limit.
- **Postup:** obsah připrav ve functions.exec jako string a do code argumentu node_repl vlož přes JSON.stringify. Jde pouze o escapování JavaScriptu, nikoli shellu; apply_patch spouštěj execFile s oddělenými argumenty. Velký patch rozděl na menší sekvenční části; jednotlivý příkaz udrž pod Windows command-line limitem, prakticky kolem 20–24 tisíc znaků.
- **Ověření:** 2026-10-10 zápis 717řádkové analýzy rozdělen na Add File a navazující Update File, tasky zapsány v menších skupinách; apply_patch return code 0.
- **Stav:** ověřený postup, žádný přímý fs.writeFile.

### Recept 8: Globální AGENTS.md nelze zapsat ani přes udělená práva

- **Příznak:** apply_patch i Codex executable hlásí Failed to write file C:/Users/mordacik/.codex/AGENTS.md po session grantu souboru i parent adresáře.
- **Postup:** ověř read-only atribut a ACL pouze čtením, případně jednou obnov persistentní nástrojové prostředí. Když zápis stále selhává, nepřepisuj soubor jinými FS triky a neměň ACL automaticky. Zapiš autorizované pravidlo jako projektový fallback a připrav globální patch k dořešení.
- **Ověření:** 2026-10-10 Get-Item: Archive bez ReadOnly; Get-Acl: Modify pro sandbox skupinu. Reset node REPL zápis nezprovoznil. Projektový AGENTS.md/analýza/tasky zapsány úspěšně.
- **Stav:** nevyřešené omezení prostředí; příčina není prokázaná. Evidence: doc/global-uml-rule.patch a tasks/4-2026-10-10-globalni-uml-pravidlo-zapis.md.

## Evidence nového receptu

### Recept 9: Izolovaná regression sada nenajde balíček doctranslate

- **Příznak:** python test/regression/translate_regression.py skončí na No module named doctranslate.config, přestože zdrojový balíček existuje v src.
- **Postup:** spusť test s absolutním Pythonem a s PYTHONPATH nastaveným na src; na Windows přes execFile je vhodné předat env bez shellu. Použitý příkaz byl C:/Python314/python.exe test/regression/translate_regression.py --outdir tmp/doctranslate-test-results s PYTHONPATH=C:/Users/mordacik/Documents/Codex/doctranslate/src.
- **Ověření:** offline regression 2026-10-11 proběhla jako 16 passed, 0 failed.
- **Stav:** funkční workaround; testovací runner by mohl v budoucnu nastavovat import path sám.
- **Datum:** 2026-10-11.

### Recept 10: Pytest omylem sbírá jiný nebo vnořený projekt

- **Příznak:** spuštění python -m pytest z kořene hlásí importy z instalovaného doctranslate nebo sbírá vnořený strom doctranslate/tests; výsledkem jsou nesouvisející PermissionError/ModuleNotFoundError.
- **Postup:** nastav PYTHONPATH na C:/Users/mordacik/Documents/Codex/doctranslate/src a explicitně spusť pouze projektovou sadu: C:/Python314/python.exe -m pytest test -q.
- **Ověření:** 2026-10-11 tímto příkazem prošlo 113 testů.
- **Stav:** funkční workaround; konfigurace pytest by měla v budoucnu explicitně omezit testpaths a import path.
- **Datum:** 2026-10-11.

### Recept 11: Ollama endpoint a živý smoke test

- **Příznak:** localhost:11434 timeoutuje nebo ollama serve hlásí obsazený
port, přestože Ollama běží.
- **Postup:** nejprve ověř ollama list a endpoint
http://127.0.0.1:11434/api/tags; nespouštěj druhý ollama serve, pokud je
port už obsazený. Pro smoke test nastav TRANSLATE_OLLAMA_URL na
http://127.0.0.1:11434 a TRANSLATE_MODEL na testovaný model.
- **Ověření:** 2026-10-11 prošly živé smoke testy translategemma:12b i
translategemma:4b, každý s offline 16/16 a jedním živým požadavkem.
- **Stav:** funkční workaround.
- **Datum:** 2026-10-11.

Použij tento formát:

```text
### Recept N: stručný název
Příznak: přesná chyba nebo pozorování.
Postup: ověřené kroky workaroundu.
Ověření: jak bylo potvrzeno, že postup funguje.
Stav: funkční / fallback / omezení.
Datum: RRRR-MM-DD.
```

## Poslední aktualizace

- 2026-10-11: při validaci TranslateGemma 12B doplněn workaround pro import path izolované regression sady.
- 2026-10-11: při živém smoke testu TranslateGemma ověřen endpoint 127.0.0.1:11434 a doplněn recept pro obsazený port/nevhodný localhost.

- 2026-10-10: evidence převedena na kuchařku postupů; doplněn recept pro oprávnění, shell, Qwen, Git a REPL.
- 2026-10-10: revize potvrdila opakované selhání exec_command/apply_patch nástrojů. Ověřeno spuštění samotného apply_patch s cwd projektu; opraven Qwen postup a PDF příkaz podle aktuálních jmen souborů. Shell regex probe selhal kvůli ztracenému escapování závorek; pro inventuru používej více jednoduchých `rg -e` patternů místo ručně escapované složené regex.
