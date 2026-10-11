status: test
last change: 2026-10-11
dependency: done/2-2026-10-11-konfigurace-cloud-provideru-a-smoke-test.md
group: ai/providers/authentication
type: bug
estimate:
  time: 30–60 min zbývající práce; ruční ověření navíc 5–10 min
  logical_lines: 40–90 včetně případné opravy a testů
  tokens: 4k–8k pracovní odhad; vstupní kontext nejvýše 5k
  subtasks: K01, K02
description: Login cloud providera selže bez použitelné nápovědy, pokud není nainstalována volitelná závislost keyring.
Priority: 2 (high)
Created: 2026-10-11

## Pozorování

V GUI při volbě cloud providera a stisknutí tlačítka Login vznikne dialog:

    Secure credential storage requires the optional keyring dependency

Uživatel nemá možnost pokračovat, zjistit přesný postup instalace, použít
alternativní úložiště ani provést bezpečný smoke test. Chování je matoucí
zejména proto, že keyring je označen jako volitelná závislost.

## Požadované řešení

- Login musí zobrazit srozumitelný stav a přesný instalační/configurační
  postup pro chybějící keyring.
- Ověřit, zda projekt má podporovat bezpečnou fallback konfiguraci přes
  environment variable nebo explicitní konfiguraci bez ukládání tajného klíče
  do queue/config JSON.
- Configuration a Login musí být konzistentní pro OpenAI, Gemini a Claude.
- Přidat smoke test, který ověří dostupnost credential storage bez odeslání
  skutečného překladového požadavku.
- Nezapisovat API klíče ani jejich plné hodnoty do logu, chybových dialogů,
  tasků nebo reportů.

## Acceptance

- Bez keyring aplikace zobrazí konkrétní návod a neselže pouze obecnou
  výjimkou.
- S nainstalovaným keyring lze credential uložit/načíst nebo je jasně
  oznámeno, že backend úložiště není dostupný.
- API klíč lze bezpečně předat přes podporovanou alternativu bez zápisu do
  queue.json.
- GUI stav Login/Configuration odpovídá skutečné dostupnosti konfigurace.
- Offline testy pokryjí chybějící keyring, dostupný keyring, odmítnuté
  credentials a redakci tajných hodnot.
- Smoke test je deterministický, nevolá překlad a nezávisí na živém cloudu.

## Zbývající plán pro implementátora (revize 2026-10-11)

Status test se zachovává. Neimplementovat znovu již hotový login, env fallback
ani instalační extra secure. Gemini OAuth je samostatná chyba; není podmínkou
ověření úložiště. Uživatel cloudové ruční testování odložil.

### K01 – ověřit skutečnou dostupnost keyring backendu

- Dependency: none; jde o cílenou kontrolu již implementované opravy.
- Kontext: src/doctranslate/ai/auth.py, provider_runtime.py a
  test/test_ai_profiles.py. Načíst pouze CredentialStoreUnavailable,
  KeyringCredentialStore a credential_storage_status plus příslušné testy.
- Statický nález: credential_storage_status vrací writable=True po importu
  keyring; označení backend=keyring:module nevypovídá o použitelnosti skutečného
  backendu OS. Import knihovny sám nestačí jako doklad funkčního úložiště.
- Postup: nejprve ověřit existující testy. Doplnit rozlišení chybějící knihovny
  a nepoužitelného backendu pomocí fake backendu. Zpřesnit diagnostiku pouze
  pokud se mezera potvrdí; bez ukládání skutečného tajného klíče v automatickém
  testu. OS round-trip patří až do explicitního ručního ověření K02.
- Výsledek: dostupnost není odvozena pouze z úspěšného importu; neznámá
  zapisovatelnost se nevydává za ověřenou. Zachovat typovanou chybu/remedy
  i read-only env fallback a nezapisovat credentials do profilu/fronty/logu.
- Ověření: python -m pytest test/test_ai_profiles.py
  test/test_cloud_provider_configuration.py test/test_gui_providers.py -q
  s PYTHONPATH nastaveným na src; vše offline, bez prohlížeče.
- Odhad: 25–50 min, 40–80 logických řádků, 3k–6k pracovních tokenů.

### K02 – samostatně uzavřít test úložiště

- Dependency: K01. Kontext: tento task a bezpečná diagnostika z K01.
- Výsledek: uživatel v GUI ověří nápovědu při nedostupnosti úložiště a uloží,
  načte a odstraní jednorázový testovací credential. Zapsat jen backend,
  stav a datum. Žádný cloudový překlad ani Gemini OAuth nejsou potřeba.
- Ověření: chybějící knihovna/backend a env alternativa mají offline regresi;
  ruční test má vlastní evidenci. Pokud jej uživatel zatím nechce provést,
  ponechat status test a uvést konkrétně, co nebylo ověřeno.
- Odhad: 5–10 min práce, 0–10 řádků evidence, 1k–2k tokenů;
  čekání na uživatele není součástí pracovního odhadu.

Restart: v comments zapsat poslední dokončený K-krok, příkaz a výsledek testů.
Neměnit OAuth ani globální konfiguraci. Po dokončení přesunout issue do done;
samotná revize plánu není důvodem k uzavření.

## comments

2026-10-11: Bug zaznamenán podle GUI pozorování. Dialog při Login pouze hlásí chybějící volitelnou závislost keyring; další postup pro uživatele není dostupný. Implementace zatím nebyla zahájena.
2026-10-11: Kontrola aktuálních logů: queue.events.log obsahuje akce GUI/workeru a změny fronty, ale žádný strukturovaný event pro selhání Login, provider konfiguraci nebo chybějící keyring. worker.log obsahuje pouze průběh sazby PDF. Chyba proto není z běžících logů zpětně diagnostikovatelná; task má doplnit bezpečné logování typu provider.login.failed/provider.credentials.unavailable bez tajných hodnot a bez obsahu credentialů.
2026-10-11: Zahájena implementace. Přidána typovaná výjimka CredentialStoreUnavailable, diagnostika dostupnosti secure storage, konkrétní instalační návod a strukturované GUI eventy pro nedostupné credentials/Login failure. Configuration nyní zobrazuje stejný návod a posílá strukturovaný failure event. Přidány změny do auth, provider_runtime, veřejných AI exportů a login flow.
2026-10-11: Cílené offline testy po opravě prošly 23/23. Doplněny testy chybějícího keyringu, bezpečného env fallbacku a typované chyby s instalačním návodem. Celá sada a revize diffu ještě čekají.
2026-10-11: Aktuální prostředí bylo ověřeno bez síťového/cloudového volání: credential_storage_status() vrací backend=unavailable, available=False, writable=False a bezpečný návod k instalaci keyring. Přidán také fake-keyring test dostupného úložiště a typed error pro pokus zapisovat do env reference. GUI manuální klikací test po změně nebyl proveden; task je připraven k uživatelskému ověření v běžícím GUI.
2026-10-11: Manuální GUI ověření po překonání keyring vrstvy otevřelo Google OAuth, ale autorizace skončila chybou 401 invalid_client: OAuth client was not found. Tato chyba patří do samostatného Gemini OAuth/configuration tasku a blokuje potvrzení Login flow; citlivý authError/client parametr nebyl uložen.
2026-10-11: Uživatel nainstaloval keyring 25.7.0 v projektovém Pythonu. Ověření C:\Python314\python.exe potvrdilo backend=keyring:module, available=True a writable=True. Do pyproject.toml přidán volitelný extra secure=keyring>=25.0; Login dál provádí preflight před použitím. Původní keyring bug je tímto připraven k uzavření po opakování GUI testu; OAuth invalid_client zůstává samostatný blocker.
2026-10-11: Revize plánu oddělila ověření keyring od Gemini OAuth, opravila cestu dependency a přidala K01–K02 s odhady. Staticky nalezena mezera: dostupnost/writable se odvozuje jen z importu modulu; skutečný backend zatím není tímto ověřen. Implementace se při revizi neměnila. Cloudové ruční ověření zůstává odložené podle pokynu uživatele.
