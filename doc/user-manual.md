# Doctranslate – uživatelský manuál

## 1. Účel programu

Doctranslate překládá text dokumentu pomocí AI a zachovává co největší část
původního rozložení. Překlad je oddělený od formátování do dvou kroků:

```text
in -> html -> out
```

Aktuální produkční implementace používá PDF jako vstupní i výstupní formát.
Překladové jádro ale pracuje s HTML/XHTML s metadaty, takže další formáty lze
doplnit adaptéry bez změny samotného překladu.

Podrobný technický popis architektury, kontraktů a stavů je v
[doc/technical-overview.md](technical-overview.md).

## 2. Předpoklady

### 2.1 Povinné minimum

- Windows s dostupným `translate.cmd`.
- Python 3.11 nebo novější.
- Nainstalované projektové Python závislosti podle `pyproject.toml`.
- Dostatek místa pro vstupní soubor, mezisoubory, HTML, logy a výstupní PDF.

### 2.2 Překlad pomocí Ollamy

Pro fázi `in -> html` nebo `in -> html -> out` musí být dostupná Ollama:

```powershell
ollama serve
ollama pull translategemma:12b
```

Název modelu musí odpovídat modelu dostupnému v Ollamě. GUI seznam modelů
načítá z lokálního endpointu Ollamy. Pokud Ollama neběží nebo nemá žádný
model, lze stále provést fázi `html -> out` z již hotového HTML.

### 2.3 Ověření prostředí

```powershell
python --version
ollama list
```

Při spuštění přes `translate.cmd` se kontroluje Python 3.11+. Pokud Python
není nalezen, skript skončí s popisem chyby ještě před spuštěním aplikace.

## 3. Spuštění

### 3.1 GUI

Z kořene projektu spusťte:

```powershell
.\translate.cmd
```

Případně:

```powershell
.\translate.cmd --gui
```

GUI se spouští přes `pythonw`, takže po úspěšném startu nezůstává otevřené
konzolové okno. Pokud `pythonw.exe` není dostupný, použijte instalaci Pythonu
s podporou Tk/GUI.

### 3.2 Přímý CLI běh

Jednorázový překlad lze spustit přímo parametry překladového jádra:

```powershell
.\translate.cmd --infile "book.pdf" --outfile "book-cs.pdf" --phase both
```

Bez parametrů se otevírá GUI. Pro přímý běh tedy vždy uveďte alespoň
`--infile`, `--outfile` nebo použijte frontový příkaz `add`.

## 4. Pracovní adresář a konfigurace

Pracovní adresář obsahuje frontu, checkpointy, logy a výsledné soubory.
V GUI se nastavuje ve skupině **Pracovní adresář**.

Pokud neexistuje konfigurace, použije se aktuální adresář, ze kterého bylo
GUI spuštěno. Konfigurace se ukládá do:

```text
translate.config.json
```

Příklad:

```json
{
  "schema": 2,
  "workdir": "C:\\data\\doctranslate",
  "language": "cs"
}
```

Alternativní umístění konfigurace lze nastavit proměnnou:

```powershell
$env:TRANSLATE_CONFIG_FILE = "C:\\data\\translate.config.json"
```

Pracovní adresář neměňte během běžícího workeru. GUI změnu odmítne nebo
vyžádá zastavení workeru, aby se nemíchaly dvě fronty.

## 5. GUI

### 5.1 Obecné

- **Jazyk** – čeština nebo angličtina; výchozí volba se určuje podle locale.
- **Obnovit** – načte aktuální stav fronty a workeru.
- **Pracovní adresář** – umístění fronty a runtime souborů.

### 5.2 Worker

- **Spustit** – spustí worker, pokud neběží. Neodesílá lokální neodeslané
  změny.
- **Aktualizovat úlohy** – uloží změny z GUI do `queue.json` a worker spustí,
  pokud neběží.
- **Zastavit worker** – požádá worker o kooperativní zastavení. Během čekání
  je tlačítko deaktivováno a stavová lišta informuje, že se worker zastavuje.

  Pokud uživatel během zastavování stiskne **Spustit** nebo
  **Aktualizovat úlohy**, čekání se zruší a worker pokračuje.

Stavová lišta pod seznamem zobrazuje běh workeru, revizi fronty, aktuální
aktivitu a progress bar. Při překladu se zobrazuje počet dokončených jednotek,
například stránek nebo bloků.

### 5.3 Job

Seznam jobů je zpracováván shora dolů. Při výběru jobu se jeho podrobnosti
zobrazí v dolní části skupiny **Úloha** readonly:

- překladový modul (basic, výchozí; advanced se zobrazí jako nedostupný, dokud ho worker nezaregistruje),
- vstupní soubor,
- výstupní soubor,
- fáze,
- přeložené HTML,
- provider, profil a model.

Tlačítka pro práci s jobem:

- **Přidat** – přepne detail jobu do editačního režimu.
- **OK** – zkontroluje a přidá job do lokálního návrhu fronty.
- **Zrušit** – zahodí rozpracované zadání bez změny fronty.
- **Pozastavit** – označí vybraný job jako `paused`; worker dokončí právě
  probíhající bezpečnou hranici a job dále nezpracovává.
- **Připravit** – vrátí job do stavu `prepared`.
- **Smazat** – odstraní job z návrhu. Při mazání právě zpracovávaného jobu GUI
  vyžádá potvrzení; worker pak přeruší aktivní AI požadavek a skončí.
- **Nahoru / Dolů** – změní pořadí jobu ve frontě.

Přidání jobu probíhá přímo na hlavní stránce, nikoli v modálním dialogu.
Při výběru vstupního PDF se do prázdných polí automaticky doplní návrh HTML
a výstupního PDF. Ručně upravené hodnoty se nepřepisují.

### 5.4 Fáze

GUI používá formátově neutrální popisky:

| Popisek v GUI | Význam |
|---|---|
| `in -> html` | pouze načíst vstup a vytvořit/přeložit HTML |
| `html -> out` | použít hotové HTML a vytvořit výstupní formát |
| `in -> html -> out` | provést oba kroky |

Interní hodnoty fronty jsou `html`, `pdf` a `both`. Nejde o veřejný slib,
že vstup i výstup musí vždy být PDF; konkrétní dostupnost formátu určuje
registr adaptérů. Aktuální GUI volby souborů jsou zatím orientované na PDF
a HTML.

Při fázi `html -> out` lze HTML zadat ručně. Pokud není zadáno, worker se ho
pokusí dohledat podle metadat, hash vstupního souboru a cílového jazyka.

## 6. Stav jobu a pořadí

| Stav | Význam |
|---|---|
| `prepared` | čeká na zpracování |
| `in_progress` | má rozpracovaný checkpoint a pokračuje jako první |
| `paused` | uživatel ho pozastavil; nevybírá se automaticky |
| `failed` | poslední běh skončil chybou; ručně vraťte na `prepared` |
| `done` | úspěšně dokončeno |

Neexistují číselné priority. Worker vždy nejdříve hledá nedokončený
`in_progress` job, potom první `prepared` job v seznamu.

Globální stop nemění rozpracovaný job na `paused`; zůstane `in_progress` a po
dalším startu pokračuje z posledního checkpointu. Při vypnutí počítače proto
není nutné job ručně obnovovat.

## 7. CLI fronta

Při příkazu add lze modul uložit explicitně:

```powershell
translate.cmd add book.pdf --translator basic
```

Přímý legacy běh přijímá také --translator basic; jiné moduly odmítne, dokud
pro ně nebude zapojen workerový runner.
Fronta se ovládá krátkými příkazy. Cestu k frontě lze nechat na konfiguraci
pracovního adresáře; interní parametr `--queue` je určen především pro
diagnostiku a testy.

### 7.1 Přidání jobu

```powershell
.\translate.cmd add "book.pdf" --outfile "book-cs.pdf" --phase both --model "translategemma:12b"
```

Příkaz job uloží do fronty a worker spustí. Volitelné parametry:

```text
--outfile PATH
--inlang CODE
--outlang CODE
--model MODEL
--provider PROVIDER
--profile PROFILE
--phase both|html|pdf
--htmlfile PATH
--input-format FORMAT
--output-format FORMAT
```

### 7.2 Ovládání workeru

```powershell
.\translate.cmd start
.\translate.cmd pause JOB_ID
.\translate.cmd stop
.\translate.cmd status
.\translate.cmd status --json
```

`start` pouze spustí nebo obnoví worker. `stop` požádá o zastavení po
bezpečné hranici; při překladu se aktivní AI požadavek zruší, pokud to
provider umožňuje. `status --json` je vhodný pro skripty a diagnostiku.

## 8. Přímé fáze překladového jádra

### 8.1 Oba kroky

```powershell
.\translate.cmd `
  --infile "book.pdf" `
  --outfile "book-cs.pdf" `
  --phase both `
  --inlang en `
  --outlang cs `
  --model "translategemma:12b"
```

### 8.2 Pouze `in -> html`

```powershell
.\translate.cmd --phase html `
  --infile "book.pdf" `
  --outfile "book-cs.pdf" `
  --htmlfile "book-cs.html" `
  --model "translategemma:12b"
```

HTML obsahuje přeložené bloky, metadata zdrojového dokumentu a checkpointy.
Lze ho zkontrolovat nebo ručně opravit před sazbou.

### 8.3 Pouze `html -> out`

```powershell
.\translate.cmd --phase pdf `
  --infile "book.pdf" `
  --htmlfile "book-cs.html" `
  --outfile "book-cs.pdf"
```

Tento režim Ollamu nepotřebuje. Musí být dostupné původní vstupní PDF,
hotové HTML a všechny potřebné rendererové závislosti.

### 8.4 Další diagnostické volby

```text
--ollama-url URL
--trace
--logfile PATH
--compact
--pdf-save-mode adaptive|memory|checkpoint
--pdf-checkpoint-pages N
```

`--trace` zapne detailnější události a měření výkonu. `--logfile` určí vlastní
JSONL run log. `--compact` provede zmenšení staršího PDF bez překladu.

## 9. Názvy souborů

Program přijímá existující názvy souborů bez omezení na ASCII. Automaticky
vytvořené názvy normalizuje takto:

- odstraní diakritiku,
- ponechá písmena, číslice, mezery a spojovník,
- nepoužije znaky mimo `A-Z`, `a-z`, `0-9`, mezeru a `-`,
- zachová příponu podle výstupního formátu.

Například:

```text
Lucio Russo – Zapomenutá revoluce.pdf
-> Lucio Russo - Zapomenuta revoluce.pdf
```

Ručně zadané cesty program nepřepisuje ani dodatečně nenormalizuje.

## 10. Runtime soubory, logy a checkpointy

V pracovním adresáři se mohou objevit:

| Soubor | Účel |
|---|---|
| `queue.json` | fronta a stavy jobů |
| `queue.lock` | krátký zámek zápisu fronty |
| `queue.bak` | poslední záloha fronty |
| `worker.lock` | zajištění jediné instance workeru |
| `worker-state.json` | heartbeat, aktivita a progress workeru |
| `queue.events.log` | strukturované události GUI, CLI a workeru |
| `worker.log` | stdout/stderr workeru |
| `*.run.jsonl` nebo vlastní log | detailní průběh překladu |
| `*.run-error.json` | traceback a informace o chybě |
| `*.plan.json` | plán a checkpointy překladu |
| `*.translations.json` | uložené překladové bloky |

Soubory neodstraňujte během běžícího jobu. Při řešení problému nejdříve
zachovejte `queue.json`, `worker-state.json`, příslušný run log a
`*.run-error.json`.

### 10.1 Retenční politika a úklid

Worker po ukončení automaticky spustí konzervativní úklid ve všech adresářích,
na které odkazují joby ve frontě. Úklid se během živého workeru neprovádí.

Výchozí politika:

- nikdy nemaže vstupní PDF, výstupní PDF ani HTML,
- chrání sidecary aktivních, připravených, pozastavených a chybových jobů,
- starší sidecary (`plan`, překladová cache, logy a diagnostika) maže po 30 dnech,
- vždy ponechá nejnovější dvě sady sidecarů,
- hlídá nejvýše 50 MiB na jeden sidecar a 250 MiB souhrnně na pracovní adresář;
  při překročení odstraní nejstarší nechráněné sidecary, nikdy je nezkracuje,
- dočasné soubory starší než 24 hodin a prázdné adresáře smoke testů může odstranit,
- při chybě úklidu se běh workeru nepovažuje za neúspěšný; chyba se zapíše do
  `queue.events.log`.

Úklid lze spustit i ručně:

```powershell
.\translate.cmd cleanup --dry-run
.\translate.cmd cleanup
.\translate.cmd cleanup --older-than-days 60
```

`--dry-run` pouze vypíše kandidáty. Ruční příkaz také respektuje zámek
workeru, takže při běžícím zpracování nic nemaže.

## 11. Obnova po přerušení

1. Ověřte, že worker neběží:

   ```powershell
   .\translate.cmd status
   ```

2. Zkontrolujte, že vstupní soubor, HTML a výstupní adresář existují.
3. Pokud job zůstal `in_progress`, spusťte:

   ```powershell
   .\translate.cmd start
   ```

4. Pokud job skončil ve stavu `failed`, nejprve ho v GUI připravte znovu nebo
   upravte jeho stav podle aktuálního ovládání fronty.

Překlad pokračuje z platných uložených dávek. Již potvrzené bloky se běžně
nepřekládají znovu.

## 12. Řešení běžných problémů

### Python nebyl nalezen

Nainstalujte Python 3.11+ a ověřte `python --version`. Na Windows musí být
dostupný také `pythonw.exe`, pokud chcete GUI bez konzolového okna.

### Ollama není dostupná

Spusťte `ollama serve`, ověřte `ollama list` a případně nastavte endpoint:

```powershell
$env:TRANSLATE_OLLAMA_URL = "http://localhost:11434"
```

### Model není nainstalovaný

```powershell
ollama pull translategemma:12b
ollama list
```

V GUI se stav zobrazí u výběru modelu. Prázdný seznam modelů není totéž co
nefunkční Ollama; nejprve ověřte obě možnosti.

### Chybí HTML při fázi `html -> out`

Zadejte cestu explicitně pomocí `--htmlfile`, případně ji vyberte v GUI.
U starších souborů ověřte přesný název, příponu a rozdíl mezi `-` a `–`.

### Nedostatek místa

Uvolněte místo v pracovním adresáři i v adresáři dočasných souborů. Překlad
potřebuje místo pro HTML/checkpointy a sazba může dočasně vytvořit další PDF.
Při `--pdf-save-mode adaptive` se program podle dostupné RAM a místa snaží
zvolit vhodný způsob ukládání; nedostatek místa ale nelze obejít.

### Worker se tváří jako běžící

Neukončujte ani nemažte `worker.lock` naslepo. Nejprve zkontrolujte
`worker-state.json`, `worker.log` a proces workeru. Po pádu lze stale zámek
obnovit až tehdy, když je potvrzeno, že původní proces nežije.

## 13. Omezení aktuální verze

- Produkčně je ověřena především cesta PDF -> HTML -> PDF.
- Cloudoví AI provideři mají implementovanou konfiguraci profilů, keyring/env
  credentials, model discovery a smoke kontrakt. Živé ověření API nebylo
  provedeno; lokální Ollama zůstává ověřenou cestou pro běžné zpracování.
- Pro Gemini Login musí být kromě keyringu nastaven skutečný Google OAuth
  client ID. Zadejte ho v Gemini Configuration do pole OAuth client ID nebo
  nastavte TRANSLATE_GEMINI_OAUTH_CLIENT_ID. Výchozí placeholder se nepoužívá;
  při chybějící konfiguraci aplikace zobrazí návod ještě před otevřením
  prohlížeče.
- Vizuální kontrola výsledného PDF je stále samostatný krok uživatele.
- Sazba rozsáhlého PDF může trvat dlouho; průběh sledujte ve stavové liště,
  `worker-state.json` a logu.
- Při chybě zachovejte diagnostické soubory před novým pokusem.

## 14. Doporučený postup pro první dokument

1. Ověřte Python, Ollamu a model.
2. Spusťte `translate.cmd`.
3. Nastavte pracovní adresář.
4. Stiskněte **Přidat**.
5. Vyberte vstupní PDF a zkontrolujte automaticky navržené HTML/PDF cesty.
6. Zvolte model a fázi `in -> html -> out`.
7. Stiskněte **OK**.
8. Stiskněte **Aktualizovat úlohy**.
9. Sledujte progress a stav workeru.
10. Po dokončení vizuálně zkontrolujte HTML i výsledné PDF.

## 15. Stylové profily a benchmark

Ve formuláři Job lze při vytváření nebo kopírování jobu zvolit stylovou variantu. Auto zachovává styl originálu a je výchozí. Explicitní profily jsou určeny pro registr, odborný styl, literární češtinu, archaizaci, slang, argot a stylizované regionální varianty. Výběr stylu se uloží až tlačítkem OK a worker jej obdrží po stisku Aktualizovat úlohy.

CLI aliasy jsou:

    translate.cmd --style cs-modern-literary --infile source.pdf --outfile result.pdf
    translate.cmd --target-variant cs-hantec --inlang en --outlang cs --infile source.pdf --outfile result.pdf

Benchmark Ollamy:

    translate.cmd --benchmark
    translate.cmd --benchmark translategemma:4b translategemma:12b
    translate.cmd --benchmark --style cs-modern-literary

Benchmark používá vlastní vestavěné fixture, modely nestahuje a ukládá JSON report. Bez seznamu modelů se dotáže Ollamy na dostupné modely. Živý běh může trvat dlouho; offline testy Ollamu nepotřebují.

## 16. Technický stav stylového workflow

Stylový katalog je balíčkované JSON runtime data. Job, checkpoint, cache a HTML metadata nesou variantu a revizi profilu; změna explicitního profilu proto nepřevezme cizí překlad. Varianta auto zachovává kompatibilitu historické cache.

Po změně stylového workflow ověřte:

    C:\Python314\python.exe -m pytest test -q
    C:\Python314\python.exe -m compileall -q src/doctranslate

Oba příkazy jsou offline. Vizuální sazbu PDF a živý benchmark spouštějte samostatně až po kontrole vstupů, volné kapacity a dostupnosti Ollamy.

### 16.1 Zdrojový a cílový jazyk

V editaci Job vyberte zdrojový a cílový jazyk. Seznam stylů se filtruje podle
cílového jazyka; auto zachová styl autora a explicitní profil aktivuje řízený
převod registru nebo varianty. Změny se uloží až po stisknutí OK. Přímý převod
v rámci stejného jazyka je povolen pouze s explicitním profilem.


## 17. Srovnání překladových modulů

Projekt nyní obsahuje dva oddělené režimy, které lze vybrat v jobu: basic
(lineární dávkový překlad) a standardní advanced (bounded kontext, glosář,
checkpoint a cílená validace). Advanced agentní relace je volitelná a vyžaduje
výslovné ověření schopnosti konkrétního provideru/modelu; název modelu sám o
sobě dostupnost nepotvrzuje.

Interní akceptační benchmark používá stejný fixture pro oba moduly a zapisuje
čas, stav, text, tokenová metadata, počet oprav a quality metadata do JSONL.
Offline výsledek nad fake backendem slouží pouze ke kontrole kontraktu a režie.
Nezaměňujte jej za jazykové hodnocení nebo živý výkon Ollamy. Pro skutečné
srovnání je nutné samostatně spustit živý běh s konkrétním modelem a výsledek
ručně zkontrolovat.
