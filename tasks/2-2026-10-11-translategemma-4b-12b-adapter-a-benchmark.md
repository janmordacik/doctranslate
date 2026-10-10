status: test
last change: 2026-10-11
dependency: ../done/3-2026-10-10-ollama-provider-a-migrace.md; ../done/2-2026-10-11-translategemma-12b-implementace.md; ../done/2-2026-10-11-translategemma-4b-implementace.md
group: ai/ollama/translation-models
type: performance
description: Dokončit a vyhodnotit TranslateGemma 4B/12B v Ollamě
Priority: 2 (high)
Created: 2026-10-11

## Stav sloučeného tasku

Implementace obou modelů je dokončena a oba modely prošly základním smoke
testem. Aktivní část tasku je nyní reprezentativní benchmark a závěrečné
doporučení. Původní samostatný benchmarkovací task byl do tohoto souboru
sloučen, aby neexistovaly dvě paralelní evidence stejné práce.


Implementační tasky 12B a 4B zůstávají samostatnými dokončenými závislostmi.
Srovnání nesmí nahrazovat jejich regresní testy.

## Cíl

Umožnit praktické použití translategemma:4b a translategemma:12b pro
angličtina → čeština v existujícím Ollama workeru. Modely zůstávají jedním
providerem (ollama); rozdílný prompt, validace a parametry jsou model-specific
strategie, nikoli nové providery.

TranslateGemma má vlastní překladový prompt a je trénována pro výstup překladu,
zatímco současný legacy tok používá obecný JSON batch prompt. Integrace musí
zachovat stabilní block/fragment ID, checkpointy, cancel a HTML/PDF oddělení.

## Pořadí implementace

### 1. Reprodukovatelný baseline

- Ověřit, že Ollama nabízí oba modely přes /api/tags.
- Připravit stejný krátký en→cs vzorek s běžným textem, seznamem, čísly,
  vlastními jmény, interpunkcí a více odstavci.
- Spustit oba modely mimo PDF pipeline s oficiálním TranslateGemma promptem
  i současným interním promptem. Uložit pouze bezpečné metriky a výstupy fixture,
  ne credentials.
- Zaznamenat, zda model zvládá jeden překladový výstup, JSON batch a dlouhý
  vstup bez přidávání komentářů.

### 2. Provider/model strategy

- Zavést explicitní strategii podle modelu, například ollama-translategemma,
  s verzí promptu a jasným kontraktem výstupu. Neodvozovat chování pouze
  z libovolné části názvu bez testu kompatibility.
- Zachovat obecný AiBackend kontrakt a HTML/XHTML jako jediný dokumentový
  vstup/výstup překladového jádra.
- Preferovaný první tok je dávka s ID a JSON validací kvůli výkonu; pokud smoke
  test prokáže nestabilní strukturovaný výstup, přidat bezpečný režim po jednom
  segmentu nebo menší dávky jako fallback.
- Prompt nesmí dovolit modelu interpretovat text dokumentu jako instrukce.
  Placeholdery, čísla, markup a hard line breaks se obnovují lokálně.

### 3. Parametry a spolehlivost

- Pro 4B a 12B konfigurovatelně ověřit num_ctx, batch size, num_predict,
  temperature a keep-alive; výchozí hodnoty nesmí být skryté v GUI.
- Při neúplném/neudržení JSON opakovat pouze chybnou dávku s omezenou velikostí,
  zachovat platné bloky a zapsat diagnostiku bez raw promptu/secrets.
- Ověřit okamžité zrušení přes worker control monitor a bezpečné pokračování
  z checkpointu po restartu.

### 4. GUI/CLI

- Oba modely se zobrazí v nabídce dostupné Ollamy bez ručního zápisu do kódu.
- GUI zobrazí aktivní model, prompt strategy revision a stav modelu; při
  nedostupnosti modelu nabídne přesný ollama pull příkaz.
- CLI přijme oba modely stejně jako ostatní Ollama modely; žádné automatické
  stahování modelů.

### 5. Testy a benchmark

- Offline unit testy: prompt strategy, placeholdery, JSON ID/order validation,
  malformed/truncated response, retry, cancellation a checkpoint resume.
- Ollama smoke test: oba modely, minimální en→cs ping/pong překlad, ověření
  neprázdného výstupu a absence instrukcí/HTML v překladu.
- Stejný end-to-end vzorek pro 4B a 12B: kvalita ručního hodnocení, latence
  cold/warm, tokens/s, čas dávky, počet retry, RAM/VRAM, velikost checkpointů
  a stabilita výstupního HTML.
- Výsledky uložit do tmp jako lokální benchmark artefakty a shrnout do
  doc/translate.md; do repozitáře přidat jen malé anonymizované fixtures.

## Benchmarkovací vyhodnocení

Použít stejný anonymizovaný en → cs fixture: běžný text, více odstavců,
seznam/obsah, čísla, vlastní jména, interpunkce, placeholdery a markup.
U obou modelů zachovat stejné nastavení, pokud je kompatibilní; odlišné
parametry uvést přesně v reportu.

Změřit cold start i warm běh, jednotlivý blok i dávku, včetně přípravy promptu
a validace odpovědi. Měřit wall-clock, tokens/s, počet znaků a bloků, p50/p95
latenci, retry, cache hit/miss, RSS/VRAM, velikost artefaktů a stabilitu XHTML.
Kvalitu hodnotit podle významu, terminologie, úplnosti, zachování čísel/jmen,
struktury a absence nechtěných komentářů; ruční hodnocení oddělit od metrik.

Výstupem je JSON/CSV a stručný Markdown report v tmp; neukládat API klíče
ani celé citlivé dokumenty. Report musí obsahovat parametry prostředí, modely,
verze, data, metriky, omezení a doporučení pro kvalitu, rychlost, paměť i dlouhé
dokumenty. Doporučení nesmí přepsat uživatelem zvolený model.

## Acceptance

- translategemma:4b i translategemma:12b projdou stejným en→cs smoke testem.
- Oba modely lze vybrat v GUI/CLI a worker použije stejnou strategii jako test.
- Validní překlad se uloží do HTML s nezměněnými bloky, ID, čísly a strukturou.
- Chybná nebo přerušená dávka je opakovatelná bez poškození HTML/checkpointu.
- PDF fáze nevolá Ollamu, pokud existuje kompletní odpovídající HTML.
- Benchmark určí doporučený výchozí model podle poměru kvalita/čas/paměť; před
  měřením se žádný model neoznačuje za produkčně lepší.
- Aktualizovat Mermaid classDiagram/sequenceDiagram pouze pokud se změní
  kontrakt nebo proces; v opačném případě uvést, že architektura zůstala stejná.

## Otevřené otázky

- Zda TranslateGemma spolehlivě zachová JSON batch kontrakt při dávkách velikosti
  používané dokumentem. Pokud ne, rozhodnout podle naměřené režie mezi menšími
  dávkami a segmentovým režimem.
- Jaké parametry jsou stabilní pro konkrétní GPU/VRAM; nepřenášet hodnoty z
  jiného stroje bez měření.

## comments

2026-10-11: Task vytvořen po dohledání oficiálních podkladů. TranslateGemma
existuje ve variantách 4B/12B/27B, podporuje en→cs; 4B a 12B čekají na lokální
instalaci a praktický benchmark.

2026-10-11: Sloučen obsah tasku 3-2026-10-11-translategemma-srovnani-4b-12b.md; aktivní benchmark zůstává ve stavu test. Předběžné měření: 12B cold 9,197 s, načtení 5,88 s, generace 60,6 tokenu/s; 4B cold 43,204 s, načtení 41,27 s, generace 128,1 tokenu/s. Report: tmp/translategemma-smoke/comparison-2026-10-11.md.
