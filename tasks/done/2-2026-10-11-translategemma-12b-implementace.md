status: done
last change: 2026-10-11
dependency: ../done/3-2026-10-10-ollama-provider-a-migrace.md
group: ai/ollama/translation-models
type: feature
description: Implementovat podporu TranslateGemma 12B pro překlad en → cs v Ollama workeru
Priority: 2 (high)
Created: 2026-10-11

## Cíl

Jako první samostatně integrovat a ověřit model `translategemma:12b`
v existujícím Ollama provideru. Model nesmí vytvořit nový provider ani změnit
veřejný kontrakt `AiBackend`; má být dostupný jako běžná volba modelu pro
CLI, GUI a worker.

## Implementace

1. Ověřit dostupnost modelu přes Ollama `/api/tags`. Automatické stahování
   se neprovádí; při nedostupnosti zobrazit přesný návod `ollama pull
   translategemma:12b`.
2. Přidat explicitně rozpoznatelnou strategii pro TranslateGemma, pokud se
   liší od obecného Ollama promptu. Strategie musí mít verzovaný prompt,
   zdrojový jazyk, cílový jazyk a jednoznačný kontrakt výstupu.
3. Použít doporučený překladový prompt TranslateGemma pro en → cs a zabránit
   tomu, aby text dokumentu mohl být interpretován jako instrukce.
4. Zachovat batchování, stabilní ID bloků, pořadí, placeholdery, čísla,
   checkpointy, cancel a restart workeru. JSON batch použít pouze po validaci
   odpovědi; při poškozené odpovědi opakovat jen chybnou dávku nebo použít
   menší dávku.
5. Oddělit změny modelové strategie od PDF sazby. PDF fáze nesmí volat Ollamu,
   pokud je k dispozici kompletní XHTML/HTML.
6. Parametry modelu držet explicitně a logovat bezpečné metriky: cold/warm
   latence, počet znaků/bloků, počet retry, tokens/s, RSS/VRAM, pokud jsou
   dostupné. Do logu nepatří credentials ani celý prompt s citlivým obsahem.

## Testy

- Offline unit testy pro výběr strategie, prompt, validaci ID/order,
  placeholderů, malformed/truncated JSON, retry, cancel a checkpoint resume.
- Volitelný Ollama smoke test s krátkým en → cs vzorkem.
- Stejný malý XHTML fixture projde workerem s modelem `translategemma:12b`;
  ověřit neprázdný překlad, zachování struktury a absenci komentářů modelu.
- Zaznamenat výsledek do bezpečného benchmark artefaktu v `tmp`; do Gitu
  přidat jen malé anonymizované fixtures nebo agregované výsledky.

## Acceptance

- Model lze vybrat v GUI i CLI a worker použije stejnou strategii jako test.
- Nedostupný model skončí srozumitelnou chybou a návodem, nikoli pádem GUI.
- Překlad en → cs zachová ID, pořadí, markup, placeholdery a checkpoint.
- Přerušený běh lze obnovit bez opakování již potvrzených bloků.
- PDF sazba z hotového HTML neaktivuje AI backend.
- Aktualizovány jsou relevantní dokumentace a Mermaid diagramy pouze tehdy,
  pokud se změnil veřejný kontrakt nebo high-level proces.

## comments

2026-10-11: Task oddělen z původního společného TranslateGemma plánu. Jde
o první implementační krok; lokální dostupnost modelu a parametry čekají na
instalaci uživatelem. Oficiální podklady: https://blog.google/innovation-and-ai/technology/developers-tools/translategemma/
2026-10-11: Implementována verzovaná strategie ollama-translategemma/translategemma-prompt-v1
pro translategemma:*. Legacy PDF/XHTML bridge používá strukturovanou variantu
promptu s lokální validací JSON/ID; běžný AI backend používá oficiální textovou
variantu. Ověřeno cílenými testy 8/8, compileall a offline regresí 16/16.
Živý smoke test čeká na dokončení instalace modelu.
2026-10-11: Po nastavení PYTHONPATH na src a omezení sběru na projektový
adresář test/ prošla celá sada 113/113 testů. Živý Ollama smoke test zůstává
neprovedený, protože by vyžadoval dokončenou instalaci a běžící model.
2026-10-11: Model translategemma:12b je nainstalovaný. Živý smoke test prošel:
offline 16/16, jeden živý požadavek, PDF výstup vytvořen; celkový čas 9,197 s,
načtení 5,88 s, prompt processing 0,21 s, generace 2,41 s (60,6 tokenu/s).
Úplné kvalitativní srovnání zůstává v navazujícím benchmarku.
Poznámka: předchozí věta o neprovedeném smoke testu zachycuje stav před
dokončením instalace; aktuální výsledek je uveden v tomto posledním záznamu.

