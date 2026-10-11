# Styly a uživatelský benchmark – implementační plán

Parent issue: [stylové profily a benchmark](../tasks/3-2026-10-11-stylove-profily-a-benchmark.md).
Revize proti zdrojům: 2026-10-11. Stav: návrh, implementace B01–B08 nezahájena.
Tento plán nahrazuje starší mikroplán S01–S56 v parent issue.

## Pracovní režim a minimální kontext

Zpracovat jeden B-krok nebo jeho podkrok v jednom běhu; obsahuje implementaci i své
testy a musí zanechat funkční checkout. Nejprve načíst AGENTS.md, doc/tools.md,
tento úvod a pouze zadání aktuálního B-kroku. Potom načíst dotčené symboly
a jejich přímé call sites pomocí rg. Celý translate.py nebo historii chatu
načítat jen pokud je to nutné. Pro neznámý kontrakt přiznat chybějící vstup,
zapsat jej do parent comments a nepředpokládat existenci jiné implementace.

Každý předávací záznam obsahuje: B-ID, dokončené chování, změněné soubory,
testovací příkaz/výsledek, zbývající mezery a další připravený B-krok.
Po změně provést diff review; agent nesmí commitovat/pushovat.
Lokální Qwen/Continue je pro projekt vypnutý; plán jej nespouští.
Needitovat autentizaci, PDF layout, retenční politiku ani izolovaný
tasks-local-ai balíček při implementaci stylů.

Příkazy běží z kořene projektu. Nastavit PYTHONPATH na absolutní src a použít
stejný Python, který spouští aplikaci. Zde je ověřený C:/Python314/python.exe;
pokud není dostupný, nalézt skutečný interpreter, nezapisovat jeho cestu do
aplikačního kódu. Obecné ověření: python -m pytest test -q.
Offline testy používají fake transport/backend; nespouštějí síť ani model.
Generované reporty patří do zvoleného workdir, testy do test, stálé fixture
do test/mock. Runtime fixture určené instalované aplikaci patří do balíčku.

## Ověřená místa rozšíření a nálezy

| Oblast | Existující symboly | Důsledek pro implementaci |
|---|---|---|
| Skutečný worker | queue_worker.JobOptions.from_job, Worker.run_job → translate.configure/main | Styl se musí přenést do této cesty; samotný JobRunner nestačí. |
| Produkční prompty | translate.translate_batch, ProviderBatchClient.translate, build_translation_client | Legacy Ollama a cloudový bridge musí dostat stejnou politiku bez dvojitého překládání promptu. |
| Obecné core | ai.contracts.SegmentRequest, ai.translation.PromptBuilder, ai.providers.HttpAiBackend.translate_segments | PromptBuilder nyní není volán HttpAiBackend.translate_segments; nutné otestovat skutečně odeslaný payload. |
| TranslateGemma | ai.ollama.OllamaPromptStrategy.build, OllamaBackend._call_text | Zachovat modelovou strategii; instrukce stylu se nesmí stát překládanými daty. |
| Cache/obnova | translate.cache_key, job_identity, restore_work_plan, reuse_legacy_translation, recover_saved_response | Styl ani verze katalogu nyní nejsou součástí identity; hrozí znovupoužití jiného stylu. |
| Obecná obnova | job_runner.JobSpec, JobRunner.identity/run | Rozšířit kontrakt i identitu, aniž se přepojí celá produkční architektura. |
| Metriky | translate.OllamaClient.record_stats/request/translate; performance.PerformanceRecorder | Časy Ollamy se nyní hlavně vypisují; obecný backend vrací text, ne metriky. |
| CLI | translate.cli_parser/entrypoint; queue_app.cli_main/make_job | --inlang/--outlang již existují; nepřidávat je znovu. Benchmark dispatch musí předcházet obnovení dokumentového jobu. |
| GUI | QueueGui.add/copy_selected_job/select_job/commit_job_form/cancel_job_form | Varianty musí fungovat pro nový job, kopii, read-only detail a Cancel, ne pouze pro combobox. |
| Providerové profily | ai.profiles.AiProfile/ProfileStore | Providerový profile je konfigurace credentials/modelu; styl má vlastní katalog a pole. |

Jde o statickou revizi, nikoli novou reprodukci nebo živý benchmark.

## Rozhodnutí pro první verzi

1. Kanonické pole target_variant s výchozí hodnotou auto. --style je CLI alias;
   dvě explicitní odlišné hodnoty jsou chyba. style_id se neukládá jako druhá
   nezávislá hodnota. Budoucí/importované starší style_id lze normalizovat na
   target_variant; při konfliktu nehádat. source_variant není nyní nutné.
2. Varianta platí jen pro jazyk katalogu (první sada cs). Neznámé ID nebo cs
   varianta s cílovým jazykem de selže před voláním providera.
3. source=target a auto znamená zachovat vstup bez AI přepisu; explicitní
   varianta aktivuje přepis. Rozpor původního zadání „auto zakázat“ vs. „auto
   zachovat“ se tím řeší bez nevyžádané změny stylu. Identická jazyková dvojice
   pro explicitní variantu není chybou.
4. JSON katalog přes importlib.resources; nepřidávat YAML dependency.
   Verze a hash vycházejí z kanonického obsahu profilu, ne cesty nebo mtime.
   Zahrnout JSON do setuptools package-data a otestovat instalovaný balíček.
5. Auto nemá ukázky stylu ani požadavek na moderní spisovnou češtinu.
   Výchozí politika zachová autorův registr a intenzitu vulgarity. Explicitní
   regionální profil smí přidat charakteristický lexikální marker pouze podle
   lexical_expansion; nesmí přidat událost/fakt ani svévolně zvýšit expresivitu.
   avoid + preserve bez výslovného soften je neplatná konfliktní politika.
6. Žádný automatický judge, přepis „polských“ slov ani jediná známka kvality.
   První verze nabízí strukturální kontroly, referenční text a ruční rubriku.
   Jazykový detektor a vědecké skóre jsou navazující rozšíření.
7. Benchmark jen Ollama; cloudové styly ověřit fake transportem.
   Bez seznamu objevit všechny lokální tagy. Vision + text model není automaticky
   SKIP: přeskočit jen prokazatelně netextové/embedding modely. Pokud schopnost
   není známá, zkusit běh a případnou chybu zaznamenat, ne hádat podle jména.
8. Jeden měřený první požadavek a tři opakované běhy na fixture/model.
   First-request čas není garantovaný cold start; skutečné load_duration
   reportovat samostatně, bez automatického násilného unload jiných úloh.
   Warm p50/p95 doplnit počtem vzorků; tři běhy nejsou statistická studie.
   Chybějící počitadla/durations mají null, ne nulu. Ollama durations převést
   z ns; tokens/s počítat eval_count / eval_duration_seconds, ne z wall času.
9. Prompt stylu je pouze pro obsah, nikoli překlad názvu souboru/modelový
   výběr formátu. Fáze html → out nepoužívá AI a nesmí změnit překlad při změně
   comboboxu; styl hotového HTML je metadata původu.
10. Vlastní referenční fixture mohou být dokončeny bez cizích právních podkladů.
    Tradiční publikovaný překlad přidat až s doloženým zdrojem/translator/právy.
    Neoznačovat vlastní nový překlad za tradiční.

## Pořadí, odhady a evidence

| Krok | Dependency | Samostatně reviewovatelný výsledek | Práce | Logické řádky | Pracovní tokeny / max vstupní kontext |
|---|---|---|---:|---:|---:|
| B01 | none | Katalog, validace, všech 11 profilů, instalace dat | 40–70 min | 220–400 | 6k–10k / 5k |
| B02 | B01 | Jednotná promptová politika v reálných provider cestách | 60–100 min | 200–350 | 8k–14k / 7k |
| B03 | B02 | Job/worker, cache a bezpečná obnova | 50–90 min | 170–280 | 7k–12k / 6k |
| B04 | none | Vlastní benchmark fixture a ruční rubrika | 20–40 min | 80–140 | 3k–6k / 3k |
| B05 | B02, B04 | Sekvenční měření, chyby a přerušení | 40–70 min | 120–220 | 5k–10k / 5k |
| B06 | B03, B05 | CLI, konzole, log a report | 40–70 min | 140–240 | 6k–10k / 5k |
| B07 | B03 | GUI varianty, kopie, Cancel, lokalizace | 40–70 min | 140–240 | 6k–10k / 6k |
| B08 | B06, B07 | Regrese, instalace, UML a manuál | 30–50 min | 60–120 | 3k–6k / 4k |
| Celkem | | Včetně lokálních testů a dokumentace | 5 h 20–9 h 20 | 1 130–1 990 | 44k–78k; orientace |

Řádky zahrnují kód/testy/data/dokumentaci; opakované datové definice katalogu
tvoří cca 100–200 řádků B01. Odhady nejsou měřením rychlosti modelu, tokeny
nejsou pevný budget ani příslib ceny. Kontext se čte po symbolech; velikost
celých souborů nesmí automaticky určit velikost zadání. Živé běhy a čekání na
uživatele se měří zvlášť. Použít původní kritéria 40 řádků na interaktivní
review a 200–400 na soudržný task jako orientaci; menší ucelený krok nenafukovat.
Větší B-krok lze reviewovat po invariantu, ne rozdělit kontrakt od jeho testu.

Výchozí doporučené pořadí: B01 → B02 → B03 → B04 → B05 → B06 → B07 → B08.
B04 je nezávislý a může být připraven dříve; souběžné editace stejného repa
nejsou povoleny. B-ID jsou reviewovatelné celky; B02/B03 mají menší jednotky předání níže.
S01–S56 jsou jen historická evidence, nikoli aktuální pořadí.

## Předání pro Codex 5.6 Luna

Implementátora určil uživatel jako Codex 5.6 Luna. Jde o plánovací předpoklad,
nikoli naměřenou schopnost modelu. Qwen/Continue omezení zůstává platné;
tato specifikace žádného agenta nespouští ani nezakládá nový chat.

B02 a B03 předávat po níže uvedených krocích; pro ostatní B-kroky platí
stávající zadání. Jeden krok = jedna změna s testy a review. Po dokončení
zapsat jeho ID do parent comments; nevydávat dokončení B02.1 za celé B02.
Rozhraní níže jsou cílová, v současném checkoutu dosud neexistují.

### Pevné kontrakty

- SegmentRequest dostane poslední nepovinné pole target_variant: str = "auto",
  aby se nezměnil význam stávajících pozičních argumentů.
- Prompt zůstane v ai/translation.py a zachová první pole system a user.
  Přidat source_language: str = "", target_language: str = "" a
  structured: bool = False jako poslední nepovinná pole. PromptBuilder vždy
  vyplní jazyky; stará dvouargumentová konstrukce zůstane použitelná.
- StyleLibrary.resolve_variant(value: str | None, target_language: str) -> str
  vrací kanonické ID nebo "auto", nikoli směs stringu a objektu.
  Profil se získává samostatně StyleLibrary.load(id) -> StyleProfile.
- compose_policy(source_language: str, target_language: str,
  target_variant: str = "auto", *, library: StyleLibrary | None = None) -> str
  patří do ai/styles.py. Vrátí důvěryhodné instrukce; neobsahuje zdrojový text.
  Normalizuje jazyky a variantu, nesahá do souborů dokumentu ani na síť.
- style_identity(target_variant: str, *, library: StyleLibrary | None = None)
  -> dict[str, str] vrátí přesně target_variant, style_revision, style_hash.
  Hash je SHA-256 kanonického JSON profilu (sort_keys=True, ensure_ascii=False,
  separators=(",", ":")), UTF-8; změna verze/politiky/ukázky změní hash.
  Pro auto je style_revision identifikátor verze zachování původního stylu
  a style_hash hash této konstantní politiky. Auto nikdy nenačítá profil.
- AiBackend a HttpAiBackend dostanou translate_prompt(prompt: Prompt) -> str.
  HttpAiBackend používá _call_prompt(prompt: Prompt) -> str v konkrétním
  provideru a stejnou validaci neprázdného výsledku jako translate.
  Nepředávat instrukce zpět do translate(text, source, target).
  Import typu Prompt do contracts.py pouze přes TYPE_CHECKING.
- OllamaPromptStrategy.build zachová dosavadní argumenty a přidá poslední
  keyword-only instructions: str = "". Instrukce vloží do instrukční části
  před dokumentová data. Je-li instructions prázdné, staré volání se nezmění.
- JobSpec dostane poslední pole target_variant: str = "auto".
  JobOptions.from_job a make_job přijímají stejné pole/default.
  Produkční modul vede TARGET_VARIANT = "auto"; Worker.run_job jej nastavuje
  z každého jobu včetně auto. Katalog/resolver nepatří do plánování workeru.
- Identita překladu používá target_variant + style_revision + style_hash
  a prompt_revision. Přidat je do legacy job/cache i JobRunner.identity.
  PDF-only čte tato pole jako původ hotového HTML, ne požadavek na nový překlad.

Mapování hotového Prompt na HTTP request:

| Provider | Instrukce | Data | Zachovat |
|---|---|---|---|
| OpenAI | messages role=system, content=prompt.system | role=user, content=prompt.user | endpoint, auth, parser odpovědi |
| Gemini | systemInstruction.parts[0].text | contents[0].parts[0].text | auth, endpoint, parser odpovědi |
| Claude | system=prompt.system | messages role=user | max_tokens, auth, parser odpovědi |
| Běžná Ollama | system message | user message | stávající model/options/rušení |
| TranslateGemma | modelová strategie, instructions=prompt.system | text=prompt.user, jazyky z Prompt | structured režim a validace ID |

Nepřidávat SDK ani měnit provider endpointy. U TranslateGemma smí transport
sloučit instrukce a data do jednoho user message podle modelové strategie;
musí zachovat jednoznačnou datovou hranici a nesmí styl vydávat za zdroj.
Offline payload testy ověřují mapování, nikoli podporu živého cloudu.

### Uzavřené integrační kroky

Odhady zahrnují implementaci i cílené testy. Součty odpovídají B02/B03
v hlavní tabulce; nepočítat podkroky podruhé do odhadu celku.

| ID | Dependency | Výsledek | Čas | Řádky | Pracovní tokeny |
|---|---|---|---:|---:|---:|
| B02.1 | B01 | Pevný promptový kontrakt a společná politika | 20–30 min | 60–100 | 2k–4k |
| B02.2 | B02.1 | Skutečné requesty všech providerů | 20–35 min | 70–125 | 3k–5k |
| B02.3 | B02.2 | Produkční batch a cloudový bridge | 20–35 min | 70–125 | 3k–5k |
| B03.1 | B02.3 | Job, worker a předání varianty | 15–25 min | 40–70 | 2k–3k |
| B03.2 | B03.1 | Cache/checkpoint identita a odmítnutí jiné varianty | 20–40 min | 80–120 | 3k–5k |
| B03.3 | B03.2 | HTML provenance, discovery a PDF-only | 15–25 min | 50–90 | 2k–4k |

B02.1: číst jen SegmentRequest, Prompt/PromptBuilder a katalog z B01.
Povolené změny: ai/contracts.py, ai/translation.py, ai/styles.py a
test/test_ai_translation.py/test_ai_styles.py. Přidat kontrakty, variantovou
politiku a style_identity. Stávající volající zachovají default auto; zatím
nepřepojovat provider dispatch. Ověřit auto, cs profil s de cílem, konflikt
politiky, stabilní hash a změnu hash po změně obsahu. Prompt user nesmí přenést
zdrojovou instrukci do system. Testy: test_ai_styles.py a test_ai_translation.py.

B02.2: číst HttpAiBackend.translate/translate_segments a pouze request/response
metody ollama/openai/gemini/claude. Povolené změny: tyto provider moduly,
ai/contracts.py pro protokol a test/test_ai_providers.py/test_ai_translation.py.
Implementovat přesně translate_prompt a _call_prompt z kontraktů výše.
translate(text, source, target) je kompatibilní wrapper pro auto; segmenty
použijí PromptBuilder s variantou. Same-language auto vrátí text beze změny
bez HTTP, explicitní variantu skutečně odešle. Fake transport ověří payload
každého providera, návrat textu a chybu empty_output. Žádný cloudový request.

B02.3: číst translate.translate_batch, ProviderBatchClient.translate a pouze
související testy v test_layout_and_models.py. Povolené změny: translate.py,
ai/ollama.py pro strategii a test/test_layout_and_models.py.
Batch sestavit jako Prompt: system obsahuje existující pravidla JSON fragmentů
a compose_policy, user obsahuje pouze serializovaná originals. Legacy Ollama
payload vytvořit z Prompt s modelovou strategií; ProviderBatchClient z
system/user messages sestaví Prompt a zavolá backend.translate_prompt.
Nezískávat důvěryhodná pravidla parsováním JSON dokumentu. Zachovat přípravu
a obnovu [[KEEP...]], ID, schéma a diagnostiku. Ověřit zachycením payloadu:
styl jednou, původní data beze změny, cloud bez dvojitého překladu instrukcí.
TARGET_VARIANT v této fázi může být jen interní default auto; CLI až B06.
Pokud IN_LANG=OUT_LANG a varianta=auto, vrátit připravená data přes stávající
lokální obnovu/validaci bez client.translate. Test musí zachytit nulový počet
AI requestů i v produkční batch cestě, nikoli pouze v HttpAiBackend.

B03.1: číst make_job, normalizaci fronty, JobOptions.from_job/Worker.run_job,
JobSpec a konstrukci SegmentRequest v JobRunner.run. Povolené změny:
queue_app.py, queue_worker.py, job_runner.py, translate.py a test_style_jobs.py.
Přidat pole/defaulty a předat variantu do requestu. Explicitní variantu
validovat před AI; ve fázi pdf pouze převzít metadata bez potřeby katalogu.
Ověřit starý JSON bez pole a dva po sobě běžící joby: explicitní → auto.
V tomto mezikroku neprovádět explicitní styl nad starou cache: před zpracováním
takového jobu jej řízeně odmítnout jasnou chybou, dokud B03.2 nezavede úplnou
identitu. Auto a PDF-only dál fungují. Testovat přenos hodnot odděleně od
spuštění jobu; žádná nechráněná explicitní varianta nesmí být zpracována.

B03.2: číst cache_key, job_identity/matching_plan, save/restore_work_plan,
reuse_legacy_translation/recover_saved_response a JobRunner.identity.
Povolené změny: translate.py, job_runner.py a test_style_jobs.py.
Přidat style_identity i prompt_revision. Všechny cesty reuse musí ověřit
kompatibilitu, žádná nesmí variantu obejít. Pokud existující plan patří jiné
variantě/politice, zachovat dosavadní bezpečné odmítnutí matching_plan a
doporučit jiný outfile; starý HTML/PDF/JSON nepřepsat ani nemazat.
Pro nový outfile odlišné cache klíče zajistí nový překlad. Starý checkpoint
bez style identity řízeně odmítnout, pokud kompatibilitu nelze prokázat.
Teprve s těmito kontrolami odstranit dočasné odmítnutí z B03.1 a jeho test
nahradit regresí správného explicitního překladu s novou identitou.
Ověřit: stejné ID + jiná pravidla, auto vs. explicitní, správný restart,
legacy fallback a beze změny zachované původní soubory.

B03.3: číst build_html_metadata, validate_html_against_source,
configure_from_html/use_html_job_metadata, discover_translation_html a
run_html_typesetting. Povolené změny: translate.py, queue_app.py a
test_style_jobs.py/test_cli_input.py. Zapsat a obnovit provenance identity.
Discovery pro nový překlad musí odlišit varianty; PDF-only přijme hotové HTML
i bez nainstalovaného původního stylu a použije jeho metadata.
Fake backend musí selhat, pokud se během PDF-only zavolá byť jednou.
Ověřit hotové i starší HTML bez nových polí; styl nesmí změnit jeho obsah.

Každý podkrok spustí výše jmenované cílené soubory přes python -m pytest
s PYTHONPATH=src. Po B02.3 a B03.3 spustit celou offline sadu.
U metod, které v checkoutu nesou jiné jméno nebo změnily kontrakt, zapsat
konkrétní rozdíl a před přepojením sjednotit zadání; neprovádět velký refaktor
jen kvůli podobnosti názvů.

### Pevný sběr benchmarkových metrik B05

Zvoleno: volitelný stats_callback: Callable[[dict[str, object]], None] | None
jako keyword-only argument OllamaClient.__init__, default None. record_stats
předá callbacku kopii raw stats pro každý dokončený request; dosavadní tisk
i návrat str z translate(payload) zachová. Žádná druhá transport implementace.
Výjimka callbacku není chyba modelu; runner ji zachytí jako chybu sběru/reportu.

Runner resetuje zachycené stats před každým requestem. Nezamění partial stats
předchozího požadavku za současný; nekompletní odpověď označí fail a zachová
dostupné metriky jako partial. Každý vzorek má wall čas, generovaný text a
metadata uvedená v B05. Percentily použijí jen úspěšné opakované vzorky
shodné kombinace model + fixture + varianta; first request se nezapočítá.
Benchmarkový writer ani tokenové odhady nepatří do ai providers.

Před zahájením Luny stačí předat: kořen repozitáře, parent issue,
aktuální B/podkrok a příslušný úsek tohoto plánu. Žádné další modelové
nastavení nebo zvláštní právní/agentní workflow toto zadání nezavádí.

## B01 – katalog použitelný i po instalaci

Kontext: ai/contracts.py pro konvence, pyproject.toml, test/test_ai_profiles.py
jako vzor testů; ai/profiles.py pouze pro ověření odlišné odpovědnosti.
Povolené nové soubory: ai/styles.py, ai/data/styles.json, test/test_ai_styles.py.
Povolená integrace: package-data v pyproject.toml, veřejné AI exporty dle potřeby.

API: StyleLibrary.list(language) vrátí stabilní pořadí; load(id) vrátí
neměnný StyleProfile; validate_all ověří duplicitní ID a politiku. auto není
profil. resolve_variant(value, target_language) vrátí kanonické ID nebo auto;
load(id) vrátí profil samostatně. Pevné podpisy určuje zadání pro Lunu výše.
Profil má ID/jazyk/verzi, prompt must/should/avoid/forbidden, politiku
vulgarity/fidelity/caricature/transformation/lexical_expansion a ukázky,
lexikon, transformace a provenance. Žádné libovolné spuštění kódu z JSON.

Postup: nejprve jeden validní profil a testy neplatných dat; následně všech
11 ID z parent issue jako vlastní pravidla/ukázky. Validovat intenzitu 0–3,
enumy, neprázdné ID, cílový jazyk a konfliktní fidelity. Zachovat všechny
uživatelem požadované styly; nehledat automaticky autora/dialekt.

Acceptance: deterministická nabídka, neznámá varianta, poškozený JSON,
duplicita a konfliktní politika mají srozumitelnou chybu. Katalog je dostupný
bez Ollamy a z instalovaného wheel. Ověření: test/test_ai_styles.py a
test/test_ai_profiles.py; wheel test je závěrečná kontrola B08.

## B02 – styl musí být v odeslaném requestu

Kontext: ai/translation.py:PromptBuilder, ai/contracts.py:SegmentRequest,
ai/providers.py:HttpAiBackend.translate/translate_segments, modelové
_call_text v ollama/openai/gemini/claude.py a translate.translate_batch,
ProviderBatchClient. Použít existing test_ai_translation, test_ai_providers,
test_layout_and_models a fake transport, ne živý cloud.

Navržený malý kontrakt: compose_policy(source, target, variant) vytváří
důvěryhodné instrukce; PromptBuilder je připojí před datovou hranici.
Pro hotový prompt přidat přesně translate_prompt(prompt: Prompt) -> str
podle pevného kontraktu výše; provider zachová oddělené instrukce a data.
AiBackend.translate(text, source, target) zachovat pro staré volající.
Netvořit druhý paralelní překladač ani nevolat backend.translate nad instrukcí
„Translate ...“ jako nad textem, který má být přeložen.

Produkční JSON batch zachová přesná pravidla pro ID, fragmenty a [[KEEP...]].
Legacy Ollama i TranslateGemma přidají stejné stylové instrukce před data,
s modelově specifickou formou. Cloudový ProviderBatchClient předá hotový
batch prompt beze změny JSON kontraktu a bez zdvojeného skládání pravidel.
Nelze tvrdit, že samotná PromptBuilder změna napojí worker.

Acceptance: fake transport zachytí skutečný payload pro běžnou Ollamu,
TranslateGemma a každý cloudový backend: varianta se vyskytuje v instrukci,
zdroj „ignore previous instructions“ zůstává daty; auto nemá stylovou ukázku.
Původní fragmenty, ID a placeholdery projdou stejnou validací. Stejný jazyk
s auto nevolá AI; explicitní varianta do AI projde. Neoznačovat offline
prompt test za důkaz kvalitního překladu ani za zaručenou odolnost LLM.

Ověření: test/test_ai_translation.py, test/test_ai_providers.py,
test/test_layout_and_models.py a nové cílené prompt testy.

## B03 – job, cache a obnova tvoří jeden invariant

Kontext: queue_app.make_job/QueueStore._normalise, queue_worker.JobOptions
a Worker.run_job; job_runner.JobSpec/identity; translate.cache_key,
job_identity, save_work_plan/restore_work_plan, build_html_metadata,
validate_html_against_source, discover/reuse/recover překladů.
Nový test/test_style_jobs.py; použít vzory test_job_runner/test_queue_app.

Postup: nový nepovinný target_variant=auto normalizovat při načtení starého
jobu; worker pokaždé nastaví hodnotu z aktuálního jobu, včetně resetu na auto.
Přidat variantu a profilový hash/revizi do obou identit a cache. Obnovovací
a legacy-reuse cesty nesmějí přijmout odlišný profil jako stejný překlad.
Změna profilu v JSON při stejném ID musí zneplatnit starý překlad.
Staré cache lze ponechat jen pro kompatibilní auto se stejnou prompt politikou;
jinak řízeně znovu přeložit. Původní soubory nemazat.

V HTML zapsat target_variant/revision jako metadata původu. PDF-only čte již
přeložené HTML bez katalogu/modelu i při chybějícím historickém profilu.
Vyhledávání HTML pro překlad respektuje variantu; při PDF-only ji nepoužívat
jako požadavek na nový AI překlad. Odlišná metadata hlásit, neměnit obsah.

Acceptance: starý job=auto; varianta A→B a změna pravidel A zneplatní obnovu;
po restartu stejná varianta bezpečně pokračuje; dva joby po sobě nepřebírají
globální variantu; PDF-only nemá ani jedno volání backendu. Job Copy zachová
variantu (GUI doplní B07). Ověření: nové testy + test_job_runner.py,
test_queue_app.py a příslušné testy HTML/layoutu.

## B04 – pevné texty a poctivá reference

Kontext: existující test/mock a benchmarkové příklady v tasks/done; nepřebírat
celou knihu ani neověřený cizí překlad. Nové runtime data ai/data/benchmark.json,
test/test_benchmark_fixtures.py. Nevázat nainstalovaný benchmark na test/mock.

Výstup: vlastní en→cs text o cca 120–180 slovech, kde se zvyšuje obtížnost:
polysemie bank/interest, zájmena, past perfect, inverze „Had ...“, idiom,
zápor, relativní věta a přesné 42/3.14/{{name}}. Přidat krátký cs→cs přepis.
U každé fixture ID, verze/hash, jazyky, zdroj/práva a jeden nebo více vlastních
referenčních překladů; reference je kontrolní návrh, nikoli jediná správná věta.

Acceptance: stejné vstupy pro všechny modely, profil nepřepisuje fixture,
reference není vložena do překladového promptu. Rubrika pro ruční význam,
plynulost, terminologii, styl a nepřidaný obsah; pouze placeholdery/čísla/ID
a neprázdný výstup hodnotit automaticky. Testy validují data/provenance.
Tradiční úryvek/český publikovaný překlad není blokátor; chybějící práva
zapsat jako navazující rozšíření.
## B05 – sekvenční benchmark se skutečnými metrikami

Kontext: OllamaClient.request/translate/record_stats/abort/close v translate.py,
PerformanceRecorder, ai/transport.py. Nový benchmark.py a test/test_benchmark.py.
Nepoužívat obecný backend pouze vracející str k odhadování tokenů z délky textu.

Navržený výsledek BenchmarkSample: model, fixture_id/hash, target_variant/hash,
prompt_revision, run_index, status, text, wall_ms, load_ms, prompt_eval_ms,
eval_ms, prompt_tokens, eval_tokens, tokens_per_second, error_code a skip_reason.
Převzetí raw stats udělat stats_callback podle pevného kontraktu výše bez změny
stávajícího textového návratu. PerformanceRecorder použít pro časové souhrny,
samostatnou výsledkovou obálku pro texty a tokenová pole; není to obecná DB.

Model discovery použije existující endpoint/transport; kompatibilitu ověřit
explicitními schopnostmi, pokud jsou dostupné. Seznam deduplikovat se zachováním
pořadí; embedding-only je SKIP, text+vision je způsobilý. Nedostupná Ollama/
prázdný seznam vytvoří srozumitelnou chybu/report, nic se nestahuje.
Pro každý model jedna první a tři opakované generace stejných fixture,
temperature=0; think=false pouze tam, kde to model podporuje.
Výchozí vzorek en→cs auto; cs→cs vyžaduje explicitně zvolenou variantu.

Acceptance: fake transport ověří pořadí volání, ns→ms, null chybějící metriky,
nulový eval_duration bez dělení nulou, SKIP, chybu modelu a pokračování dalších.
Ctrl+C/cancel ukončí aktuální request přes existující mechanismus, zapíše
dokončené výsledky a interrupted; další model se nespustí. Nenásobit retry
běhy v percentilu bez označení. Změny globálů translate vrátit v finally;
benchmark nesmí poškodit konfiguraci následného jobu.

Ověření: nové testy benchmarku, test_performance.py a příslušné transport/
Ollama testy. Živé requesty až v samostatném uživatelsky spuštěném smoke.

## B06 – CLI a výsledky bez otevírání dokumentu

Kontext: translate.cli_parser/entrypoint, queue_app.cli_main pro add,
observability.py, filename_policy.py (skutečný název modulu ověřit rg),
PerformanceRecorder.write_json/write_markdown; test_cli_input/test_bootstrap.
Povolené nové testy test/test_benchmark_cli.py, test/test_benchmark_report.py.

CLI: --benchmark s nargs=*; None znamená běžný režim, [] discovery všech
modelů, neprázdný seznam pouze dané modely. Spustit před infile preflight,
work-plan discovery, GUI a PDF. --target-variant/--style mají shodnou
normalizaci pro přímý překlad i add. --style all nyní nepodporovat, vypsat
jasnou chybu a doporučit jednotlivé běhy. Konflikt benchmark + --phase pdf,
--compact nebo dokumentové soubory je chyba před requestem.

Konzole vypisuje každý překlad a MODEL | VARIANT | STATUS | FIRST_REQUEST |
WARM_P50 | TOKENS/S. Report JSON/Markdown i JSONL zachovají plný benchmarkový
text, reference, parametry, vzorky, chyby a SKIP důvody. Výchozí reporty:
workdir/benchmark-<ASCII UTC timestamp>-<run id>.*; použít existující normalizaci
názvů a žádné přepsání původních souborů. Logovat pevné benchmark fixture,
nikoli svévolně obsah uživatelských dokumentů nebo credentials.

Navržené exit codes: 0 pokud alespoň jeden model prošel a žádný neselhal
(SKIP není fail); 1 při fail/nedostupnosti/žádném použitelném výsledku;
2 chyba parametrů; 130 přerušení. Logovací/write chyba musí být viditelná,
dokončené překlady ještě vypsat do konzole a pokud lze zachránit partial report.
Nepřidávat automatický cloud benchmark ani instalaci modelů.

Acceptance: test argparse rozliší absent/empty/nonempty seznam, chybějící
infile neblokuje benchmark, auto není vnucený styl, chybné ID selže včas.
Fake writer ověří translations/timings v konzoli i reportu, escaping Markdown
a zachování JSON textu, chybu zápisu a částečné výsledky při přerušení.
Testy nevyžadují Ollamu.

## B07 – GUI varianty v současném formuláři

Kontext: QueueGui.__init__, _set_job_form_state, _clear_job_detail, select_job,
add, copy_selected_job, commit_job_form, cancel_job_form, render/poll,
refresh_labels a lokalizační slovníky; existující test_gui_providers/test_queue_app.
Načíst jen tyto úseky a jejich přímé testy, ne celý 2000řádkový soubor.

Přidat zdrojový/cílový jazyk a Cílovou variantu do hlavní skupiny Job, bez
nového modálního dialogu. Jedna nabídka z StyleLibrary, první Auto – zachovat
styl originálu. Provider/Profile/Configuration nadále ovládají AI službu.
Mimo Add/Copy jsou hodnoty read-only; OK uloží do lokálního formuláře/fronty,
Cancel vše obnoví, Update jobs je teprve odešle workeru. Při změně cílového
jazyka nekompatibilní variantu resetovat na auto a viditelně oznámit důvod.
PDF-only variantu pouze ukazuje jako původ překladu, nic nepřekládá.

Acceptance: Copy kopíruje variantu, polling zachová výběr i editovaný formulář,
Cancel nepublikuje změny, starý job ukazuje auto. Testy sdílených helperů/fake
widgetů ověří chování bez grafického desktopu; ruční EN/CZ GUI smoke je
samostatná evidence. Nenaprogramovat druhý katalog do widgetu.

## B08 – závěrečné ověření a dokumentace

Kontext: výsledky B01–B07, doc/user-manual.md, doc/translate.md, readme.txt,
tento plán a procesní index A13 v doc/modularization-analysis.md.
Ověření: celá offline sada test -q, compileall src/doctranslate.
Wheel vytvořit v tmp a instalaci ověřit v izolovaném prostředí; testovat katalog
a benchmark --help z cwd mimo checkout bez PYTHONPATH. Pokud build nástroje/
dependency chybí, zapsat přesný blocker, neinstalovat do globálního Pythonu.
Zkontrolovat absenci běžícího modelu/network requestu během PDF-only testu.

Uživatel může samostatně spustit krátký živý benchmark translategemma:4b,
translategemma:12b a qwen3.8:27b: uložit příkaz, fixture hash, skutečný model
digest/parametry a report. Běžící model/čas/dostupnost se předem neodhaduje.
Jazykový review Auto, literární, argot a regionální varianta je ruční;
nenahrazovat jej „všechny tokeny/placeholdery souhlasí“.

Aktualizovat UML podle skutečné implementace, označit co zůstalo cílové.
Parent status test po implementaci a offline validaci; done až po splnění
dohodnutých acceptance včetně evidence neprovedeného/odloženého smoke.
Commit je samostatně autorizovaný krok a není podmínkou správnosti testu.

## UML a index procesů

Aktuální produkční architektura: [P00](modularization-analysis.md#p00-aktualni-produkcni-tok).
Následující diagramy jsou cílové; katalog ani benchmark dosud neexistují.
Autoritativní struktura této změny a procesy jsou zde; parent je referencuje.

| ID | High-level proces | Diagram |
|---|---|---|
| V01 | Výběr/uložení varianty, produkční překlad, obnova, PDF-only | [V01](#v01-varianta-job-a-obnova) |
| V02 | Benchmark discovery, měření, SKIP/fail/cancel a report | [V02](#v02-uzivatelsky-benchmark) |

~~~mermaid
classDiagram
    class StyleLibrary {
        +list(language)
        +load(id)
        +resolve_variant(value, language)
    }
    class StyleProfile {
        +id
        +version
        +content_hash
        +policy
        +samples
    }
    class JobSpec {
        +target_variant
    }
    class PromptBuilder {
        +build(request)
    }
    class ProductionBatch {
        +translate_batch(items, client)
    }
    class Provider {
        +translate_prompt(prompt)
    }
    class BenchmarkRunner {
        +run(models, fixture, variant)
    }
    class BenchmarkReport {
        +samples
        +write()
    }
    StyleLibrary o-- StyleProfile
    JobSpec --> StyleLibrary : validates
    PromptBuilder --> StyleLibrary : policy
    ProductionBatch --> StyleLibrary : same policy
    PromptBuilder --> Provider
    ProductionBatch --> Provider
    BenchmarkRunner --> PromptBuilder
    BenchmarkRunner --> BenchmarkReport
~~~

### V01 – varianta, job a obnova

~~~mermaid
sequenceDiagram
    actor User
    participant UI as GUI or CLI
    participant Styles as StyleLibrary
    participant Queue as QueueStore
    participant Worker
    participant Run as Production translate
    participant Cache
    participant AI as Provider
    User->>UI: Add or Copy, choose variant, OK
    UI->>Styles: resolve language and variant
    alt invalid variant or conflict
        Styles-->>UI: validation error
    else valid
        UI->>Queue: CLI publish or GUI Update jobs
        Worker->>Queue: read eligible job
        Worker->>Run: configure including variant
        alt PDF-only
            Run->>Run: typeset existing HTML, no AI
        else translation or rewrite
            Run->>Cache: source + model + variant hash + policy revision
            alt compatible checkpoint
                Cache-->>Run: completed translations
            else missing or changed policy
                Run->>Styles: compose trusted policy
                Run->>AI: policy + separate document data
                alt cancelled or paused
                    AI-->>Run: interrupted
                    Run->>Cache: preserve completed compatible blocks
                else valid result
                    AI-->>Run: translated fragments
                    Run->>Cache: checkpoint with identity
                else invalid response
                    Run-->>Worker: bounded error, no corrupt cache
                end
            end
        end
    end
~~~

### V02 – uživatelský benchmark

~~~mermaid
sequenceDiagram
    actor User
    participant CLI
    participant Runner as BenchmarkRunner
    participant Ollama
    participant Report
    User->>CLI: --benchmark models and variant
    CLI->>Runner: validated fixture and policy
    opt no explicit model list
        Runner->>Ollama: discover tags
        alt unavailable or empty
            Runner->>Report: run error
        else models
            Ollama-->>Runner: tags
        end
    end
    loop each selected model sequentially
        alt known non-text capability
            Runner->>Report: SKIP with reason
        else text or unknown capability
            loop first request and three repeated requests
                Runner->>Ollama: translation prompt, fixed parameters
                alt cancellation
                    Runner->>Ollama: abort active request
                    Runner->>Report: partial results, interrupted
                    Note over Runner,Report: No further requests after cancellation
                else error
                    Ollama-->>Runner: failure
                    Runner->>Report: failed sample, continue next model
                else result
                    Ollama-->>Runner: translation and raw timings
                    Runner->>Report: text, null-aware metrics, checks
                    Report-->>CLI: print translation and timing
                end
            end
        end
    end
    Runner->>Report: final or partial report
    alt cannot write
        Report-->>CLI: visible write error, keep console results
    else saved
        Report-->>CLI: JSON, Markdown, JSONL paths
    end
~~~

Mermaid zde prošel pouze textovou kontrolou, nikoli renderem. Implementátor
ověří render, pokud má dostupný nástroj; jinak to výslovně zaznamená.

## Zbývající vstupy a navazující rozšíření

MVP nemá nevyřešenou uživatelskou volbu. Práva k tradičním překladům,
automated judge/dialektový detektor a stylový smoke na konkrétním modelu
nejsou předpokladem kódových kroků. Označit je v evidenci jako odložené či
neověřené, ne jako hotové. Další task vytvářet až pro skutečně zvolený rozsah.
