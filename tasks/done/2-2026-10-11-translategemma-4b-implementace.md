status: done
last change: 2026-10-11
dependency: 2-2026-10-11-translategemma-12b-implementace.md
group: ai/ollama/translation-models
type: feature
description: Implementovat podporu TranslateGemma 4B pro překlad en → cs v Ollama workeru
Priority: 2 (high)
Created: 2026-10-11

## Cíl

Po dokončení a otestování 12B integrovat `translategemma:4b` jako druhou
modelovou volbu stejného Ollama provideru. Cílem je nabídnout rychlejší a méně
náročnou variantu bez kopírování logiky workeru nebo zavedení zvláštního
formátu dokumentu.

## Implementace

1. Ověřit dostupnost modelu přes Ollama `/api/tags`; automatické stahování
   se neprovádí. Při nedostupnosti zobrazit `ollama pull translategemma:4b`.
2. Znovu použít strategii TranslateGemma z tasku 12B. Odchylku zavést pouze
   tam, kde ji prokáže test (prompt, kontext, velikost dávky nebo výstupní limit).
3. Zachovat obecný `AiBackend` kontrakt, JSON/ID validaci, placeholdery,
   checkpointy, cancel, restart a oddělení HTML od PDF.
4. Nastavit a zdokumentovat bezpečné výchozí parametry pro 4B. Konfigurace
   musí umožnit experiment s context window, batch size, num_predict,
   temperature a keep-alive bez změny zdrojového kódu.
5. Při nestabilním JSON výstupu použít stejný omezený fallback jako u 12B:
   menší dávka nebo segmentový režim, nikdy tiché posunutí bloků.

## Testy

- Offline regresní testy sdílené s 12B doplněné o volbu 4B a jeho parametry.
- Volitelný Ollama smoke test s totožným en → cs vzorkem jako u 12B.
- Worker test nad stejným XHTML fixture; ověřit strukturu, ID, checkpoint,
  cancel a bezpečné zotavení po neúplné odpovědi.
- Zaznamenat cold/warm latenci, tokens/s, retry, RSS/VRAM a velikost výstupu.

## Acceptance

- `translategemma:4b` lze vybrat v GUI i CLI a jeho stav je správně
  odlišen od nedostupného modelu.
- 4B projde stejným kontraktním testem jako 12B bez poškození XHTML.
- Rozdílné parametry jsou konfigurovatelné a bezpečně logované.
- PDF fáze funguje bez Ollamy při použití kompletního HTML.
- Dokumentace označí, zda se změnil kontrakt; při nezměněném kontraktu se
  pouze odkáže na autoritativní architekturu.

## comments

2026-10-11: Task je záměrně závislý na 12B. Nejprve se ověří společná strategie,
aby 4B nebyl implementován jako paralelní jednorázová větev.
2026-10-11: Implementace 12B používá rodinnou detekci translategemma:* a stejnou
verzovanou strategii proto automaticky pokrývá i 4B bez duplicitního kódu.
Přidán regresní test pro translategemma:4b; offline testy prošly. Live smoke
čeká na instalaci modelu 4B.
2026-10-11: Model translategemma:4b je nainstalovaný. Živý smoke test prošel:
offline 16/16, jeden živý požadavek, PDF výstup vytvořen; celkový čas 43,204 s,
načtení 41,27 s, prompt processing 0,11 s, generace 1,17 s (128,1 tokenu/s).
Úplné kvalitativní srovnání zůstává v navazujícím benchmarku.
Poznámka: předchozí věta o čekajícím smoke testu zachycuje stav před
dokončením instalace; aktuální výsledek je uveden v tomto posledním záznamu.

