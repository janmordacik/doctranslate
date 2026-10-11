# Modularizace dokumentů a AI poskytovatelů — implementační analýza

Datum: 2026-10-10.
Stav: M01–M14 implementováno a offline ověřeno; živé cloud/OAuth a vizuální PDF ověření nebylo spuštěno.
Rozsah: formátové adaptéry, XHTML, AI backendy, profily, autentizace, CLI/GUI a worker.
Autorita: schválené požadavky uživatele v chatu. Níže uvedená technická rozhodnutí konkretizují implementaci.

## A01 Scope a pravidla implementace

- PDF input: cesta → XHTML s metadaty; output: XHTML s metadaty + cesta → soubor.
- Samostatný překlad: text + vstupní/výstupní jazyk → přeložený text.
- První poskytovatelé: Ollama, OpenAI API, Gemini API, Anthropic Claude API; další přidáním modulu.
- GUI: výběr poskytovatele/profilu a modelu, jednotné Konfigurace… / Configuration…, specifický dialog a případně Login.
- API klíč a podporované OAuth; browser login není povinná schopnost každého poskytovatele.
- Fronta/konfigurace zůstávají JSON s krátkými zámky; žádná DB, nový daemon nebo trvalé IPC.
- Zachovat translate.cmd, src/doctranslate, test/mock, workdir, lokalizaci cs/en a JSONL logování.
- Zachovat prepared, in_progress, paused, failed, done. auth_required je diagnostický kód, nikoli nový job state.
- GUI job editace až po Update; CLI automaticky publikuje změny. Start pouze startuje worker. Update může nastartovat worker a zrušit čekající stop.
- Stop/pause jsou kooperativní na bezpečné hranici; během AI překladu se stop/pause pokusí okamžitě zrušit aktuální požadavek a job zůstane in_progress nebo paused. Failed uživatel ručně přepíná na prepared.
- Tato analýza neopravňuje sama spustit implementaci, lokálního agenta, instalaci modelů, cloud smoke, plnou sazbu knihy, commit nebo push.
- Implementovat po odpovědnostech; zachovat ruční HTML editace, TOC regrese, staré checkpointy a artefakty.
- Povinné Mermaid UML: high-level struktura jako classDiagram, všechny dokumentované high-level procesy jako sequenceDiagram. Index procesů A13 definuje pokrytí.
- Globální SW pravidlo je v ~/.codex/AGENTS.md, sekce Software architecture documentation; projektový AGENTS.md je jeho explicitní fallback. [Projektové pravidlo](../AGENTS.md), [uzavřený provozní task M15](../tasks/done/4-2026-10-10-globalni-uml-pravidlo-zapis.md). Projektový formát tasků: [project-structure-and-tasks.md](project-structure-and-tasks.md).

### Implementovaný stav po M01–M14

2026-10-10: Byly implementovány kanonické XHTML contracts/codec, format registry, PDF resource boundary, provider-neutral AI contracts, profily a CredentialStore hranice, Ollama/OpenAI/Gemini/Claude HTTP backendy, loopback OAuth, JobRunner, provider-aware queue joby a GUI konfigurace. Legacy PDF překladový běh zůstává kompatibilní bridge; plná migrace historických sazebních heuristik do nového PDF pluginu je záměrně ponechána za veřejnou hranicí rendereru.

Offline evidence:

- pytest test -q: 81 passed.
- python -m compileall -q src: passed.
- git diff --check: passed.
- Žádný live Ollama/cloud request, skutečný OAuth login ani sazba knihy nebyly spuštěny.

Zbývající provozní omezení jsou runtime závislost PyMuPDF pro PDF, volitelný keyring pro API/OAuth credentials, dostupnost Ollamy/modelu a ruční vizuální kontrola PDF. Tato omezení nejsou důvodem k označení offline implementace za nehotovou; ověření je součástí ručního checklistu M14.

## A02 Ověřený aktuální stav

Statická revize souborů 2026-10-10, bez nového běhu překladu nebo sazby.

| Oblast | Aktuální implementace | Migrační potřeba |
|---|---|---|
| Production | Worker.run_job nastavuje translate.py globály a main | JobRunner + immutable JobSpec/RunContext |
| PDF input | PdfInputAdapter používá get_text("blocks"), text/bbox | Převést propracované extract_blocks/make_block, styly, TOC, prostředky |
| PDF output | Adapter vyžaduje injected renderer; sazba v translate.py | Samostatně sestavený PDF modul |
| XHTML | html, blocks[].markup a blocks[].text mohou být nezávislé | Jeden autoritativní obsah, codec a odvozené views |
| Backend | Sequence[str] vstup; MarkupTranslation výstup, bez markup kontextu | Jednotextové API + volitelný segmentový batch |
| Formátování | prepare_text_translation/restore_text_translation chrání spany/literals | Přesun neutrální ochrany do core |
| Config | save_config zapisuje jen schema/workdir/language | Zachovat a verzovat ne-tajné AI profily |
| GUI | Pevné Ollama discovery a model combo | Provider registry a asynchronní discovery |
| Cache | MODEL/jazyky/markup, ne provider | Provider/endpoint/model/prompt/segment policy identity |
| PDF-only | Znovu čte originál a ověřuje geometrii | Explicitní source-template resource, bez AI objektů |

Dřívější done tasky řešily dílčí text/markup konzistenci a izolaci JobOptions. Nové tasky jsou navazující rozšíření, nikoli opětovné otevření uzavřených oprav.

<a id="a03-cilove-vrstvy"></a>

## A03 Cílové vrstvy

Adapter: formáty/poskytovatelé. Strategy: překlad. Repository: fronta/profily. Composition root: explicitní sestavení registrů. Bez DI frameworku a automatické instalace pluginů.

~~~text
src/doctranslate/
  __main__.py, config.py, observability.py
  queue_app.py, queue_worker.py
  job_runner.py                    fáze, immutable kontext, checkpointy
  translate_core/
    contracts.py                   dokument a segmenty
    xhtml_codec.py                 load/dump a legacy HTML migrace
    pipeline.py                    segmentace, validace, aplikace textů
    adapters.py                    formátové protokoly bez PDF imports
  formats/
    registry.py                    descriptor, factory, availability, resolver
    pdf/input.py                   extrakce a metadata
    pdf/output.py                  veřejný writer
    pdf/layout.py                  fonty, TOC, sazba, atomické uložení
  ai/
    contracts.py, registry.py       backend, capabilities, discovery
    profiles.py                    ne-tajné verzované profily
    auth.py                        AuthProvider a CredentialStore
    prompts.py                     sdílené instrukce a segmentové JSON
    ollama.py, openai.py, gemini.py, claude.py
  gui/provider_dialogs.py           UI factory a specifické konfigurace
test/test_*; test/mock/               offline testy a trvalé malé podklady
~~~

Jde o cílové členění; malé sousední moduly lze sloučit při zachování hranic. Backend neimportuje tkinter; core neimportuje PyMuPDF ani provider SDK. translate.py během migrace interní bridge, nakonec tenká facade. V rootu nevytvářet Python wrappery.

~~~mermaid
classDiagram
    class JobRunner {
        +run(spec, context) JobResult
    }
    class FormatRegistry {
        +resolve(direction, path, explicit_format) Descriptor
    }
    class DocumentInputAdapter {
        <<interface>>
        +read(source) XhtmlDocument
    }
    class DocumentOutputAdapter {
        <<interface>>
        +write(document, target) Path
    }
    class XhtmlDocument {
        +schema
        +source_metadata
        +resources
        +body
        +blocks() ReadOnlyView
    }
    class XhtmlCodec {
        +load(path) XhtmlDocument
        +dump(document, path)
    }
    class TranslationPipeline {
        +translate(document, context) XhtmlDocument
    }
    class AiTextBackend {
        <<interface>>
        +translate(text, source_language, target_language) str
    }
    class ProviderRegistry {
        +get(provider_id) ProviderDescriptor
    }
    class ProfileStore {
        +resolve(id, revision) AiProfile
    }
    class AuthProvider {
        <<interface>>
        +get_credentials(interactive) Credentials
    }
    class CredentialStore {
        <<interface>>
        +get(reference)
        +set(reference, secret)
    }
    class PdfInputAdapter
    class PdfOutputAdapter
    class OllamaBackend
    class OpenAIBackend
    class GeminiBackend
    class ClaudeBackend
    JobRunner --> FormatRegistry
    JobRunner --> ProfileStore
    JobRunner --> ProviderRegistry
    JobRunner --> DocumentInputAdapter
    JobRunner --> DocumentOutputAdapter
    JobRunner --> XhtmlCodec
    JobRunner --> TranslationPipeline
    DocumentInputAdapter <|.. PdfInputAdapter
    DocumentOutputAdapter <|.. PdfOutputAdapter
    DocumentInputAdapter --> XhtmlDocument
    DocumentOutputAdapter --> XhtmlDocument
    XhtmlCodec --> XhtmlDocument
    TranslationPipeline --> AiTextBackend
    AiTextBackend <|.. OllamaBackend
    AiTextBackend <|.. OpenAIBackend
    AiTextBackend <|.. GeminiBackend
    AiTextBackend <|.. ClaudeBackend
    OpenAIBackend --> AuthProvider
    GeminiBackend --> AuthProvider
    ClaudeBackend --> AuthProvider
    AuthProvider --> CredentialStore
~~~

## A04 XHTML a prostředky

~~~python
class DocumentInputAdapter(Protocol):
    def read(self, source: Path) -> XhtmlDocument: ...

class DocumentOutputAdapter(Protocol):
    def write(self, document: XhtmlDocument, target: Path) -> Path: ...
~~~

XhtmlDocument je v paměti XHTML model s metadaty; XhtmlCodec jej ukládá do editovatelného .html s XHTML obsahem.

Rozhodnutí: autoritativní body strom XHTML. Bloky/prostý text jsou read-only odvozené pohledy. Mutace přes replace_segments() vrací nový validovaný dokument. Žádný nezávislý writable html/text/markup. Originál pro audit je označený source snapshot, ne druhá aktuální verze obsahu.

| Data | Pravidlo |
|---|---|
| Schema | Explicitní integer verze, odmítnout neznámou novější |
| Source | Formát, SHA-256, title, source language; zdrojová fakta immutable |
| Translation | Target language, dokončenost po segmentech, segment policy; bez přihlašovacích údajů/provider options |
| Content | Stabilní block/fragment IDs, pořadí, entity, inline styly, hard breaks, odkazy |
| Layout | Volitelné stránky/rotation/bbox/line metrics/fonts/TOC; core pouze přenáší |
| Resources | resource_id, role, media_type, cesta, SHA-256 |
| Extensions | Namespaced PDF metadata validovaná PDF modulem |

Formáty bez stránek mohou mít page_number=None; pořadí vždy existuje. PDF jednotky/souřadnice nejsou univerzálně povinné.

První PDF writer vyžaduje source-template resource s referencí na originál. Input ji dodá; output použije ResourceResolver při sestavení, bez třetího veřejného parametru. Relativní reference se řeší vůči umístění XHTML, ne cwd. Explicitní --infile nebo GUI remap může změnit cestu, ale SHA-256 musí souhlasit. Dokument zatím není samostatně přenositelný bez původního PDF. PDF metadata zůstávají popisná; skutečné fonty/geometrii ověřit proti originálu jako dosud.

Codec požadavky:
1. XHTML namespace, escapované texty/atributy, inertní JSON metadata bez možnosti předčasně ukončit element.
2. Parser bez externích entit/DTD, načítání vzdálených resources a spuštění skriptů; zvolit bezpečný parser a uvést dependency.
3. Cílený tolerantní migrátor pro legacy br/span/data-block/data-span. Nejasná ID/schéma neopravovat odhadem.
4. Editovaný body text má přednost před cache/source_markup. Zachovat ruční editace.
5. Validovat ID, styly a strukturální invarianty; complete=true samo nestačí.
6. Atomické uložení; chyba nemění poslední validní checkpoint.

## A05 Výběr a dostupnost formátů

Oddělené input/output registry. Descriptor: id, label_key, media_type, extensions, factory, check_availability. Explicitní registrace v composition root; descriptor neimportuje PDF runtime.

| Situace | Rozhodnutí |
|---|---|
| Explicitní format ID | Daný registrovaný adaptér |
| Auto a známá přípona | Case-insensitive mapování přípony |
| Bez přípony/známého formátu a bez volby | Vyžádat formát; výstup nehádat podle input metadata |
| Explicitní formát odporuje známé příponě | format_conflict |
| Neznámá nebo chybějící přípona + explicitní volba | Respektovat volbu, input ověří obsah |
| Duplicitní registrace pro stejný směr/formát | duplicate_registration, žádné tiché přepsání |
| Poškozený/jiný obsah pod .pdf | Input odmítne |
| Bez outfile | Legacy PDF job výchozí PDF; jiná explicitní volba určí příponu |

Availability(available, code, reason, remedy) zkoumá runtime závislosti, ne konkrétní job. Job preflight odděleně validuje vstup/resources/cíl. Nic neinstalovat ani nesázet během probe. Nedostupný modul v GUI viditelný s důvodem, nepoužitelný; worker recheck před jobem. Chybějící PDF knihovna nesmí blokovat startup GUI/CLI, textový backend nebo XHTML.

## A06 Textové API a formátování

~~~python
class AiTextBackend(Protocol):
    def translate(
        self, text: str, source_language: str, target_language: str
    ) -> str: ...
~~~

Profil/model/options/auth při konstrukci instance. Obsah dokumentu jsou data, ne instrukce. Sdílená normalizace jazyků; und/auto jen podporuje-li provider detekci. Prázdný/whitespace text vrátit beze změny bez requestu.

Volitelná batch capability:

~~~python
@dataclass(frozen=True)
class TranslationSegment:
    id: str
    text: str

@dataclass(frozen=True)
class SegmentRequest:
    segments: tuple[TranslationSegment, ...]
    source_language: str
    target_language: str
    context: str | None = None

class BatchTranslationBackend(Protocol):
    def translate_segments(self, request: SegmentRequest) -> SegmentResult: ...
~~~

SegmentResult: mapa ID→text a explicitní chyby segmentů. Core mapuje segmenty na XHTML; provider zná pouze text/ID/jazyky/kontext, žádné PDF ani XHTML style typy. Backend bez batch capability lze volat po jednom textu; jednotka checkpoint/control je dokončené volání. Core může předat sousední textový kontext pro terminologii.

Převzít prepare_text_translation/restore_text_translation invarianty:
- Stabilní IDs, font span pořadí, hard breaks, kapitolové číslo, mezery na hranách, rovnice/URL/literals.
- Společný PromptBuilder: jen datový překlad, text/JSON bez vysvětlení. Structured mode jen pokud ho provider/model podporuje.
- Žádný regex jako HTML parser, poměrové rozdělování překladu ani vrácené HTML od modelu.
- Text vložit jako escapované textové uzly; model nesmí vložit skript či změnit strukturu.
- Ověřit missing/duplicate/extra IDs, string types, placeholders/číslování a completion.
- Partial odpověď: přijmout pouze samostatně validované segmenty; blok dokončen až jsou validní všechny; opakovat jen chybějící.
- Refusal/safety blocking/truncation/prázdný překlad není úspěch.

## A07 AI registry a provider options

ProviderDescriptor: id, label_key, factory, auth_methods, capabilities, check_local_availability. Oddělený UI registr obsahuje dialog_factory podle stejného ID. Dva profily téhož poskytovatele jsou samostatná nastavení.

| Provider | První auth | Specifická pole |
|---|---|---|
| ollama | none | base_url, model, dosavadní num_ctx/keep_alive/think/options |
| openai | api_key | model, endpoint, případně organization/project a podporované parametry |
| gemini | api_key, oauth | model, OAuth client setup, projekt podle režimu |
| claude | api_key | model, output token limit a podporované parametry |

Ollama options se neposílají automaticky do cloudů. Každý provider má whitelist/schema options a capability; neznámé hodnoty jsou chyba. Nekódovat „nejnovější“ modely ani benchmarkové domněnky.

Local availability oddělit od vzdálených stavů missing_dependency, not_configured, auth_required, checking, available, unavailable, no_models, forbidden, invalid_response. Jde o diagnostiku, ne job states.

Discovery asynchronní/on-demand, timeout a krátká cache; výsledek musí odpovídat provider/profile/revision/request_generation. Starý výsledek zahodit. Empty list ≠ výpadek/401. Pokud provider nemá úplný model list, umožnit explicitní model ID podle capability. Nezobrazovat počet modelů. Nový kompatibilní lokální server přidat explicitním modulem; obecný OpenAI-compatible adaptér až jako další task, bez předpokladu shodných auth/discovery/structured režimů.

## A08 Profily a autentizace

Návrh schema 2; schema 1 zachová workdir/language a vytvoří legacy Ollama profil podle dosavadních CLI/env/default pravidel. Žádný automatický cloud default.

~~~json
{
  "schema": 2,
  "workdir": "C:/data/doctranslate",
  "language": "cs",
  "default_profile_id": "local-ollama",
  "ai_profiles": [
    {
      "id": "local-ollama", "revision": 1, "label": "Lokální Ollama",
      "provider": "ollama", "model": "configured-model-id",
      "base_url": "http://127.0.0.1:11434",
      "auth": {"method": "none"}, "options": {}
    },
    {
      "id": "cloud-openai", "revision": 1, "label": "OpenAI",
      "provider": "openai", "model": "configured-model-id",
      "auth": {"method": "api_key", "credential_ref": "doctranslate/cloud-openai"},
      "options": {}
    }
  ]
}
~~~

JSON nemá api_key/password/access_token/refresh_token/OAuth secret/Authorization. credential_ref odkazuje na systémové úložiště. OAuth client údaje dle citlivosti mimo projekt; nikdy je nepřibalovat do tasků/logů.

CredentialStore get/set/delete: Windows Credential Manager přes vhodný OS adapter/knihovnu, testy in-memory. Další OS přes bezpečný keyring. Nedostupný store hlásí remedy; žádný tichý plaintext fallback. Explicitní env reference pro CLI/CI povolena, hodnotu neukládat.

AuthProvider none/api_key/oauth:
- Worker používá pouze noninteractive credentials/refresh, nikdy neotevírá browser.
- Login/save/test connection jsou oddělené; probe nepřekládá dokument ani negeneruje placený text.
- Secret zadat maskovaně, již uložený nevypisovat. Store ověřit před změnou. Config commit až po staged secret; při selhání zachovat starý profil a odstranit pouze nový orphan.
- Logout odstraní lokální credentials; remote revoke jen dle podpory a explicitního úkonu.
- Refresh rotace GUI/worker chráněna krátkým credential lockem; nikdy queue.lock při síti/login.
- Redakce zahrnuje exception chain/traceback/HTTP debug/payload a queue error. Raw SDK exception nelogovat.

OAuth:
- Gemini dokumentuje desktop flow; ověřit aktuální SDK/scopes/API projekt/účtování.
- OpenAI/Claude první etapa api_key; browser login nabízet až pro doloženou podporovanou integraci.
- System browser + loopback localhost, náhodný state, PKCE dle podpory/požadavků, timeout/cancel cleanup.
- Nepoužívat cookies nebo tokeny web chatů, Codexu/Claude Code. Chat subscription není automatická API autorizace.
- Enterprise federation/proxy auth broker není součást první implementace.

## A09 JobRunner, cache a restart

Job fields: profile_id, profile_revision, volitelný model override, input_format/output_format (auto nebo ID). Konkrétní model vyřešit před requestem do immutable run identity. Job/plan může nést provider ID/fingerprint, ne credentials ani credential_ref. Config path workeru předat explicitně při startu; jiné cwd nesmí najít jiný config.

Profily verzované: Save nová immutable revize; ponechat staré revize odkazované joby. GUI nový výběr revize publikuje až Update, CLI ji připne při add. Samotné Save nemění běžící/připravené joby. Resolve: explicitní profile_id/revision, pak job.model override nad profile.model. Legacy job bez profilu vždy Ollama. Neznámý explicitní profil/revize je chyba, ne fallback.

JobRunner:
1. JobSpec/format preflight bez AI importu.
2. Input read nebo codec load hotového XHTML.
3. Backend vytvořit jen pro chybějící překlady.
4. Bounded dávka → validovaný XHTML/cache checkpoint → worker callback.
5. Complete/resource validace → offline output adapter.
6. RunContext: logger, control/cancel, ResourceResolver, storage/checkpoint služby; core/provider/formát neimportují queue_app.

| Změna | Resume |
|---|---|
| Stop/vypnutí a stejná identita | Jen nezapsané/nevalidní jednotky |
| Rotace klíče/token refresh | Pokračovat, secret není content identity |
| Provider/model/endpoint/jazyk/prompt policy | Řízený konflikt, nový job/výstup; nesmíchat machine cache |
| Ruční XHTML editace | Zachovat, export identita podle aktuálního XHTML |
| Změněné XHTML/layout revision | Nový export bez překladu |
| Přesun source se stejným SHA-256 | Explicitní remap |
| Změněný source SHA-256/novější schema | Odmítnout bez přepsání |

Machine cache key: SHA-256 kanonické serializace provider_id, endpoint identity bez secret/query credentials, model ID a známý digest, jazyky, source fragment/hash, source fingerprint, segmenter/prompt revision, output-affecting options. Timeout/retry/auth nepatří do key.

Legacy import je explicitní: provider=ollama, doložit endpoint/policy, validovat všechny přijaté bloky. Neznámá identita nesmí přenést cache na jinou službu; hotové editované XHTML zůstává čitelné. Nic hromadně nemazat.

Update změn input/output/provider/model/range aktivního jobu je konflikt; nejdříve pause, pak změna prepared jobu a checkpoint compatibility kontrola. Stop/pause jsou povolené control změny. auth_required v noninteractive workeru nebo identity konflikt → zachovat checkpoint, failed s remedy; další joby podle dosavadní smyčky.

## A10 Chyby, retry, logování a výkon

BackendError: code, bezpečný message/remedy, retryable a případný request_id/retry_after. Provider výjimky mapovat/redigovat před logováním. UI lokalizuje známé code.

| Podmínka | Chování |
|---|---|
| Chybí Python | Srozumitelná launcher chyba, bez instalace |
| Chybí SDK/PDF knihovna | Nedostupný jen konkrétní modul |
| Chybí klíč/OAuth odvolán | auth_required bez nekonečného retry/browseru workeru |
| 401/403 | Auth vs permission; nanejvýš jeden dokumentovaný refresh pokus |
| 429 rate limit | Retry-After, bounded backoff+jitter |
| Quota/billing limit | Nonretryable, neměnit účet/službu |
| 5xx/connect timeout | Bounded retry |
| Timeout po odeslání | Mohlo dojít k účtování; retry není exactly-once |
| Model nenalezen/nepodporovaný | Konkrétní chyba, bez auto-download/fallback |
| Refusal/truncation/invalid IDs | Není úspěch, validní partial výsledky zachovat |
| Disk full/readonly/locked | Poslední validní výstup zůstane, další neuložitelný překlad nepokračuje |
| Poškozený queue/config JSON | Řízená chyba, nepřepsat defaulty |
| Missing/changed source | Resource error/remedy před exportem |
| Stop při dlouhém requestu | Dokončit jednotku; další request/retry až po control kontrole |

Návrh: maximálně 2 retry (=3 pokusy), konečný configurable timeout per attempt. Nekombinovat neomezeně SDK a aplikační retry; vypnout SDK retry nebo doložit společný budget. Backoff je bezpečná hranice pro stop/pause, když request už neběží.

JSONL přes observability: adapter.selected/unavailable, provider.probe, auth.login.started/completed/failed, auth.refresh, translation.batch.started/completed/retry/failed, checkpoint.saved, export.started/completed. Pole job_id/provider_id/model/stage/duration_ms/attempt/segment counts/usage/request_id. Žádné dokumentové texty nebo secrets/headers/raw body; trace nikdy neodmaskuje credentials. Logger failure neskrývá původní chybu.

Výkon: lazy imports, bounded batching podle provider/model limits, checkpoint před další dávkou, žádné network probe při každém GUI pollu. Text length ≠ token count; konzervativní budget a provider capability. První implementace sekvenční; paralelismus až s vlastním ověřením cache/rate-limit/cancellation.

## A11 GUI a CLI

Zachovat skupiny Worker, Job, General a status bar. Job editor: provider/profil/model + Konfigurace…, input/output format odděleně od AI. Model patří konkrétnímu jobu/profilu.

Dialog:
- Společný label/profil, specifická pole z UI factory provideru.
- Uložit/Zrušit, explicitní Test připojení a Obnovit modely.
- API key/OAuth jen z auth_methods; Přihlásit/Odhlásit jen podporované OAuth.
- Save vytvoří profile revision a změní lokální přiřazení jobu; Update teprve publikuje. Cancel zachová profil/job; login credentials v otevřeném dialogu staged až do Save.
- Při zavření upozornit na dirty joby; Start je nepublikuje.
- Discovery mimo GUI thread, guard proti stale result.
- Při switch provideru neplatný model vynutit nový výběr; nic tiše nepřepisovat.
- Poll zachová selection/scroll/dirty editace. Worker stopping mimo job list; Stop disabled, Start/Update mohou zrušit stop.
- Remedy bez secrets ve status bar; všechny nové texty cs/en.

Plánované CLI, ne současně implementované příkazy:

~~~text
translate.cmd add book.pdf --profile local-ollama --model MODEL --input-format pdf --output-format pdf
translate.cmd --phase html --infile book.pdf --outfile book-cs.pdf --profile cloud-openai
translate.cmd --phase pdf --htmlfile book-cs.html --infile book.pdf --outfile book-cs.pdf
translate.cmd providers
translate.cmd profiles
translate.cmd login PROFILE_ID
translate.cmd configuration PROFILE_ID
~~~

Zachovat --phase html/pdf/both, --model a Ollama --ollama-url význam. configuration v CLI má textový editor/maskovaný prompt bez tkinter. login explicitní supported browser flow. Žádný --api-key VALUE v argv; pro automation explicitní env reference. Cloud access se nevyvolá jen list/GUI startem.

<a id="a12-tasky-poradi-a-dokonceni"></a>

## A12 Tasky, pořadí a dokončení

Všechny nové implementační tasky created; analýza není implementace. Dependency je skutečný předpoklad, nikoli související téma.

| ID | P | Task | Dependency |
|---|---|---|---|
| M01 | 3 | [Kanonické XHTML, metadata, resources a bezpečný codec](../tasks/done/3-2026-10-10-kanonicke-xhtml-a-codec.md) | none |
| M02 | 3 | [Oddělené read/write registry, výběr formátu a lazy dostupnost](../tasks/done/3-2026-10-10-registr-formatu-a-dostupnost.md) | none |
| M03 | 3 | [Produkční PDF input/output a resource validace](../tasks/done/3-2026-10-10-pdf-vstup-a-vystup-jako-moduly.md) | M01, M02 |
| M04 | 3 | [Samostatné textové API a neutrální segmentová pipeline](../tasks/done/3-2026-10-10-ai-kontrakt-a-segmentovy-preklad.md) | M01 |
| M05 | 2 | [Verzované profily, CredentialStore a společná autentizační hranice](../tasks/done/2-2026-10-10-ai-profily-a-bezpecna-autentizace.md) | none |
| M06 | 3 | [Převést dosavadní OllamaClient na samostatný AI provider](../tasks/done/3-2026-10-10-ollama-provider-a-migrace.md) | M04, M05 |
| M07 | 3 | [OpenAI API backend s API klíčem](../tasks/done/3-2026-10-10-openai-api-provider.md) | M04, M05 |
| M08 | 3 | [Gemini API backend s klíčem a přípravou OAuth](../tasks/done/3-2026-10-10-gemini-api-provider.md) | M04, M05 |
| M09 | 3 | [Anthropic Claude API backend s API klíčem](../tasks/done/3-2026-10-10-claude-api-provider.md) | M04, M05 |
| M10 | 3 | [Oficiální Gemini desktop OAuth a obnovování tokenů](../tasks/done/3-2026-10-10-gemini-browser-oauth.md) | M05, M08 |
| M11 | 3 | [JobRunner, neutrální fáze, cache identity a legacy migrace](../tasks/done/3-2026-10-10-jobrunner-a-identita-checkpointu.md) | M01, M02, M03, M04, M05, M06 |
| M12 | 3 | [Napojit CLI/worker, profilové joby a formátové volby](../tasks/done/3-2026-10-10-cli-worker-a-profily-jobu.md) | M11 |
| M13 | 3 | [Výběr provider/profil/model a specifické konfigurační dialogy](../tasks/done/3-2026-10-10-gui-provider-konfigurace-a-modely.md) | M02, M07, M08, M09, M10, M12 |
| M14 | 3 | [Integrační regrese, dokumentace a ruční ověření modulárního toku](../tasks/done/3-2026-10-10-integrace-modulu-a-regresni-checklist.md) | M03, M07, M08, M09, M10, M12, M13 |

Doporučené pořadí: M05 (P2 bezpečné profily), M01 + M02, M04 + M03, M06, M11, M12, M07/M08/M09, M10, M13, M14. + označuje nezávislé větve, ne povolení dvou agentů současně editovat repozitář. Cloud moduly lze zpracovat dříve po jejich dependency.

Každý task obsahuje vlastní offline regresi, průběh v comments a update dotčeného diagramu. M14 ověřuje celek, neodkládá testy rodičů.

Definition of done:
1. Jediný JobRunner pro CLI/worker; XHTML roundtrip zachová obsah/layout/ruční editace.
2. Production PDF input/output přes registry; core bez PyMuPDF/SDK/tkinter.
3. Každý backend podporuje samostatné translate(text, inlang, outlang); fake backend nahradí Ollamu bez změny formátů.
4. PDF-only nevytváří AI/AuthProvider, nedělá discovery ani síť.
5. Bez jednoho SDK funguje zbytek aplikace; unavailable má remedy.
6. Secrets nejsou config/job/HTML/cache/plan/log/stdout/traceback.
7. Stop/pause/restart/Update zachovávají současnou smlouvu a validované checkpointy.
8. Legacy migrace deterministická; poškozená/neznámá data se neignorují/nepřepisují.
9. Unit/offline integration prochází; live API/OAuth/vizuální PDF je zvláštní evidence, ne domněnka.
10. Class a sequence diagramy odpovídají kódu; všechny procesy A13 pokryté.

<a id="a13-uml-procesy"></a>

## A13 UML procesy

P00 popisuje aktuální produkční implementaci. P01–P07 jsou cílové procesy nové architektury; jejich zavedení a ověření se sleduje v M01–M14.

### P00 Aktuální produkční tok

~~~mermaid
sequenceDiagram
    actor User as Uživatel
    participant UI as CLI nebo GUI
    participant Q as QueueStore
    participant W as Worker
    participant L as translate.py
    participant PDF as PyMuPDF
    participant O as Ollama
    User->>UI: Update nebo CLI add
    UI->>Q: Atomicky uložit joby
    UI->>W: Start pokud neběží
    W->>Q: Vybrat in_progress, pak prepared
    W->>L: Nastavit globály a main
    L->>PDF: Extrakce vstupu
    loop Chybějící dávky
        L->>O: Překlad
        O-->>L: Odpověď
        L->>L: Validace a HTML/cache checkpoint
        L->>W: QUEUE_HOOK
        W->>Q: Poll stop/pause
    end
    opt Fáze PDF
        L->>PDF: Originál a sazba HTML
    end
    L-->>W: Výsledek
    W->>Q: Stav jobu
    Note over L,PDF: Nové adaptery nejsou hlavní produkční cestou
~~~

### P01 Start, registry a discovery

~~~mermaid
sequenceDiagram
    participant UI as CLI nebo GUI
    participant Config as ProfileStore
    participant FR as FormatRegistry
    participant PR as ProviderRegistry
    UI->>Config: Načíst config a migraci
    Config-->>UI: Profily bez secretů
    UI->>FR: Descriptors a lokální availability
    FR-->>UI: Formáty a nedostupnost
    UI->>PR: Descriptors a lokální availability
    PR-->>UI: Poskytovatelé a auth možnosti
    opt Explicitní vzdálené ověření
        UI->>PR: Async probe profilu
        PR-->>UI: Stav/modely s revision a request ID
        UI->>UI: Zahodit stale výsledek
    end
    Note over FR,PR: Bez importu všech SDK a bez generace textu
~~~

### P02 Konfigurace a API key

~~~mermaid
sequenceDiagram
    actor User as Uživatel
    participant UI as Frontend
    participant D as Specifický editor
    participant S as CredentialStore
    participant P as ProfileStore
    User->>UI: Konfigurace
    UI->>D: Pole podle provideru
    User->>D: Nastavení a maskovaný klíč
    alt Zrušit
        D-->>UI: Beze změny
    else Uložit
        D->>D: Validace
        D->>S: Staged secret
        S-->>D: Reference
        D->>P: Atomicky uložit novou revizi
        P-->>UI: ID a revision
        UI->>UI: Job přiřazení dirty
    end
    Note over UI,P: Job až Update; CLI publikuje dokončením příkazu
~~~

### P03 Browser login, refresh a logout

~~~mermaid
sequenceDiagram
    actor User as Uživatel
    participant UI as Frontend
    participant A as AuthProvider
    participant B as Prohlížeč
    participant IdP as Identity provider
    participant S as CredentialStore
    User->>UI: Přihlásit podporovaný profil
    UI->>A: login interactive
    A->>A: Loopback, state a PKCE dle podpory
    A->>B: Otevřít autorizační URL
    B->>IdP: Přihlášení a souhlas
    alt Cancel, timeout nebo chyba
        A-->>UI: Chyba a cleanup
    else Schválení
        IdP-->>A: Callback code a state
        A->>A: Ověřit state
        A->>IdP: Výměna code za tokeny
        IdP-->>A: Credentials
        A->>S: Staged secure uložení
        A-->>UI: Přihlášeno
    end
    opt Expirace tokenu
        A->>S: Refresh credentials pod credential lockem
        A->>IdP: Refresh bez browseru
        IdP-->>A: Nové tokeny nebo auth_required
        A->>S: Uložit úspěšnou rotaci
    end
    opt Odhlášení
        User->>UI: Odhlásit
        UI->>A: logout
        A->>S: Odstranit lokální credentials
        A-->>UI: Odhlášeno
    end
~~~

### P04 Překlad a export; samotná sazba

~~~mermaid
sequenceDiagram
    participant Caller as CLI nebo Worker
    participant J as JobRunner
    participant F as FormatRegistry
    participant I as Vstupní adaptér
    participant C as XhtmlCodec
    participant P as Pipeline
    participant B as AI backend
    participant O as Výstupní adaptér
    Caller->>J: JobSpec a RunContext
    J->>F: Formáty a availability
    alt Nový dokument
        J->>I: read source
        I-->>J: XHTML, metadata, resources
    else Existující XHTML
        J->>C: load XHTML
        C-->>J: Validovaný dokument
    end
    opt Chybějící překlady a překladová fáze
        J->>J: Pinned profil a backend
        loop Omezené překladové jednotky
            J->>P: Přeložit segmenty jednotky
            P->>B: Text nebo SegmentRequest a jazyky
            B-->>P: Texty s ID
            P->>P: Ověřit a aplikovat
            P-->>J: Validovaný dokument
            J->>C: Atomický checkpoint
            J->>Caller: Kontrolní callback
        end
    end
    opt Export
        J->>J: Complete/resources validace
        J->>O: write document a target
        O-->>J: Cesta
    end
    J-->>Caller: JobResult
    Note over J,B: PDF-only vůbec nevytvoří AI/auth
~~~

### P05 Request, retry a auth chyba

~~~mermaid
sequenceDiagram
    participant Core as Pipeline
    participant B as Backend
    participant A as AuthProvider
    participant API as AI služba
    participant J as JobRunner
    Core->>B: Překlad jednotky
    B->>A: Noninteractive credentials
    alt Potřebné přihlášení
        A-->>B: auth_required
        B-->>J: Nonretryable chyba
        J->>J: Checkpoint zachovat, failed a remedy
    else Credentials
        A-->>B: Credentials v paměti
        B->>API: Request s timeoutem
        alt Úspěch
            API-->>B: Odpověď a usage
            B-->>Core: Texty
        else Retryable chyba
            API-->>B: Chyba a Retry-After
            B->>J: Kontrolní hranice
            J-->>B: Pokračovat nebo Stop
            opt Pokračovat a zbývá budget
                B->>API: Retry po backoff
            end
        else Auth, quota, refusal nebo invalid response
            API-->>B: Chyba
            B-->>J: Redigovaný BackendError
        end
    end
~~~

### P06 Update, stop, pause a restart

~~~mermaid
sequenceDiagram
    actor User as Uživatel
    participant UI as GUI nebo CLI
    participant Q as JSON fronta
    participant W as Worker
    participant J as JobRunner
    User->>UI: Editovat profil nebo job
    UI->>UI: GUI lokální job změny
    User->>UI: Update
    UI->>Q: Lock, merge, atomický zápis
    UI->>W: Start pokud neběží; Update neukončuje worker preventivně
    W->>Q: in_progress před prepared
    W->>J: Pinned JobSpec
    User->>UI: Stop nebo pause
    UI->>Q: Control nebo paused
    UI->>UI: Při Stop indikovat stopping a disabled Stop
    J->>J: Dokončit jednotku a checkpoint nebo reagovat na invalidaci
    J->>W: Callback
    W->>Q: Poll
    alt Stop
        W->>Q: Zjistit command=stop a consume stop
        W->>J: cancel_event; zrušit AI požadavek
        W->>Q: Zachovat in_progress
        W-->>UI: Worker stopped
    else Invalidace právě běžícího jobu
        W->>Q: Zjistit job missing nebo state != in_progress
        W->>J: cancel_event; zrušit AI požadavek
        W->>Q: Zachovat paused/prepared nebo job odstraněný
        W-->>UI: Worker stopped
    else Pause
        W->>Q: Zachovat paused
    else Pokračovat
        W-->>J: Další jednotka
    end
    opt Start po stopu/vypnutí
        User->>UI: Start
        UI->>W: Bez publikace dirty změn
        W->>J: Resume stejná identita
        J->>J: Vynechat validní jednotky
    end
~~~

### P07 Přesunuté zdroje a obnova exportu

~~~mermaid
sequenceDiagram
    participant J as JobRunner
    participant C as XhtmlCodec
    participant R as ResourceResolver
    participant O as PDF writer
    J->>C: load XHTML
    C-->>J: Resource reference a SHA-256
    J->>R: Resolve nebo explicitní remap
    alt Chybí nebo hash mismatch
        R-->>J: Resource chyba
        J->>J: Zachovat XHTML a poslední PDF
    else Ověřeno
        R-->>J: Source-template
        J->>O: write document a target
        O->>O: Ověřit geometrii proti source
        O->>O: Atomicky uložit PDF/checkpoint
        O-->>J: Výsledek
    end
~~~

## A14 Testování a chybějící vstupy

Podklady v test/mock, scratch v TemporaryDirectory; bez závislosti na celé knize/aktuálním model listu.
- XHTML roundtrip, legacy HTML, ruční editace, inline styles/hard breaks, TOC čísla/řádky, IDs, schema, DTD/resources.
- Format auto/explicit/konflikty, read/write registrace, lazy availability.
- Plain-text/batch, partial/refusal/truncation, markers, čísla a entity.
- Config 1→2, workdir save zachová profily, revize, secret-store failures/concurrency.
- Provider fake transport: payload/auth/text extraction/capabilities/401/403/429/5xx/timeouts/retry budget.
- OAuth fake auth server: callback/state mismatch/cancel/timeout/refresh/revoke/rotace bez skutečného účtu.
- Worker last batch/stop/pause/restart, GUI dirty/Update/selection/stale discovery a pinned config.
- Bez SDK/serveru/modelu/credentials, PDF-only bez sítě, disk full/readonly/locked output.
- Sentinel secret v fake exception/payload/traceback: nesmí být v žádném artefaktu/stdout.
- Dva joby různé profily/modely bez sdílení mutable context/cache.

Dokumentační validace: relative links, task metadata/dependency bez cyklů, Mermaid fences a diagram types. Je-li lokální renderer, vykreslit; textová kontrola není důkaz vizuálního renderu.

Při implementaci znovu ověřit oficiální API/SDK/auth. Live smoke potřebuje uživatelovy credentials, síť a souhlas s případnými náklady. Chybějící setup/API projekt/účtování/uživatelská volba se zapíše do comments příslušného tasku; neblokuje další offline práci.

Oficiální zdroje ověřené při návrhu 2026-10-10:
- [OpenAI API autentizace](https://developers.openai.com/api/reference/overview).
- [Gemini desktop OAuth](https://ai.google.dev/gemini-api/docs/oauth).
- [Claude autentizace](https://platform.claude.com/docs/en/manage-claude/authentication).

## A15 Evidence a restart práce

2026-10-10: Analýza založena statickou revizí core, PDF adapteru, configu, queue_app/worker a legacy extraction/translation/typesetting/cache. Produkční kód v rámci zadání nezměněn.
2026-10-10: Požadavek uživatele: provider-specific Configuration, API key i podporovaný browser login; povinné high-level Mermaid UML také jako globální SW pravidlo. Projektové pravidlo zapsáno, globální zápis byl v předchozí relaci nedostupný; patch a M15 evidovaly dořešení.
2026-10-10: Nové tasky created. Při restartu načíst AGENTS.md, doc/tools.md, analýzu a nejbližší připravený task. Skutečný stav vede status/comments, pořadí dependency.
2026-10-10: Dokumentační kontrola: 14 implementačních tasků + M15 provozní překážka, 1 class diagram a 8 sequence diagramů. Dependency jsou acyklické a existují. Kontrolována textová struktura Mermaid; lokální mmdc není dostupné, grafický render nebyl proveden. git diff --check prošel.
2026-10-10: Implementace M01–M14 dokončena v jednom průchodu. Po jednotlivých fázích proběhly cílené testy; závěrečný offline běh \`python -m pytest test -q\` skončil \`81 passed\`, \`compileall\` i \`git diff --check\` prošly. Tasky byly přesunuty do \`tasks/done/\`; M15 a task lokálního agenta zůstaly záměrně otevřené.
2026-10-11: Ověřeno, že globální ~/.codex/AGENTS.md již obsahuje sekci Software architecture documentation s povinnými Mermaid UML pravidly. M15 byl uzavřen a projektové odkazy aktualizovány; historické záznamy výše zůstávají beze změny.

## A16 Implementovaná konfigurace cloud providerů a smoke test (2026-10-11)

Cloud workflow je nyní oddělen od překladu dokumentu. GUI ukládá pouze profil a credential reference; API klíč jde do keyringu, případně lze použít explicitní env:NAME reference. Worker používá stejný resolver profilu a credential store jako GUI. Smoke test pouze načte seznam modelů a ověří endpoint, autentizaci a model; neposílá text dokumentu a negeneruje placený výstup.

~~~mermaid
classDiagram
    class QueueGui
    class ProviderDialog
    class ProfileStore
    class CredentialStore
    class ProviderRegistry
    class HttpAiBackend
    class ProbeResult
    class QueueWorker
    QueueGui --> ProviderDialog : configure/test
    ProviderDialog --> ProfileStore : save revision
    ProviderDialog --> CredentialStore : store API key
    QueueWorker --> ProfileStore : resolve profile
    QueueWorker --> ProviderRegistry : create backend
    ProviderRegistry --> HttpAiBackend : provider adapter
    HttpAiBackend --> CredentialStore : resolve secret
    HttpAiBackend --> ProbeResult : return safe status
~~~

~~~mermaid
sequenceDiagram
    participant UI as GUI
    participant D as ProviderDialog
    participant P as ProfileStore
    participant C as CredentialStore
    participant R as ProviderRegistry
    participant B as ProviderBackend
    UI->>D: Open Configuration
    D->>D: Edit endpoint/model/reference/API key
    opt API key entered
        D->>C: Securely store key
    end
    UI->>D: Test connection
    D->>R: Create backend from staged profile
    R->>B: Provider-specific model discovery
    B-->>D: status, latency, remedy, model IDs
    alt Save
        D->>P: Save non-secret profile revision
        D-->>UI: Apply selected profile/model
    else Cancel
        D-->>UI: Discard staged values
    end
~~~

Process index: provider configuration and smoke test = A16 sequence diagram above. Current implementation supports API-key configuration for OpenAI, Gemini and Claude, optional Gemini browser OAuth, provider-specific model discovery and offline fake-transport tests. Live cloud smoke was not run because credentials, network and possible provider charges require explicit user setup.

### A16 acceptance evidence

- test/test_cloud_provider_configuration.py: secure profile save, model discovery, missing model, authentication failure and registry capabilities.
- python -m pytest test -q: 126 passed.
- python -m compileall -q src and git diff --check: passed.
- python -m pytest -q from repository root is not the project command: it also collects unrelated nested doctranslate/ tests and fails on external package/cache setup. The scoped command is python -m pytest test -q.

## A17 Stylové profily a benchmark – aktuální implementace

Stylový katalog je provider-neutrální vstup do prompt composeru. Auto je implicitní a explicitní profil má validovanou politiku, ukázky, slovník a fingerprint. Queue job, worker, checkpoint, cache a XHTML metadata přenášejí target_variant a revizi. Benchmark používá stejný prompt boundary a ukládá text i měření.

~~~mermaid
classDiagram
    class StyleLibrary {
        +list(language)
        +load(id)
        +fingerprint(id)
        +resolve_variant(value, language)
    }
    class JobSpec {
        +target_variant
        +style_revision
        +prompt_revision
    }
    class QueueWorker {
        +from_job(job)
        +run_job(job)
    }
    class PromptBuilder {
        +build(request)
    }
    class BenchmarkRunner {
        +run(models, fixture, variant)
    }
    StyleLibrary --> JobSpec : validates
    JobSpec --> QueueWorker : runtime contract
    StyleLibrary --> PromptBuilder : trusted policy
    BenchmarkRunner --> PromptBuilder : same policy boundary
~~~

~~~mermaid
sequenceDiagram
    actor User
    participant GUI_or_CLI
    participant StyleLibrary
    participant Queue
    participant Worker
    participant Prompt
    participant Provider
    User->>GUI_or_CLI: choose variant or auto
    GUI_or_CLI->>StyleLibrary: resolve and fingerprint
    GUI_or_CLI->>Queue: publish job after OK/Update
    Worker->>Queue: read target_variant
    Worker->>Prompt: compose policy + document data
    Prompt->>Provider: one provider request
    Provider-->>Worker: translation
    Worker->>Queue: checkpoint and state
    alt PDF-only
        Worker->>Worker: typeset existing HTML; no Provider call
    end
~~~

Implementation is offline tested. The GUI target-language selector is implemented; manual GUI smoke, live Ollama benchmark and visual PDF verification are deliberately user-run operations.
