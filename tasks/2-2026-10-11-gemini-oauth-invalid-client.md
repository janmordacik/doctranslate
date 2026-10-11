status: test
last change: 2026-10-11
dependency: 2-2026-10-11-login-chybejici-keyring.md, done/3-2026-10-10-gemini-browser-oauth.md
group: ai/providers/gemini/oauth
type: bug
estimate:
  time: 20–40 min revize a evidence; živý test navíc 10–20 min
  logical_lines: 10–50; oprava jen podle nové reprodukce
  tokens: 3k–6k pracovní odhad; vstupní kontext nejvýše 5k
  subtasks: G01, G02
description: Gemini browser OAuth vrací Google chybu 401 invalid_client, protože OAuth client nebyl nalezen.
Priority: 2 (high)
Created: 2026-10-11

## Reprodukce

Po stisknutí Login v GUI a přesměrování do Google OAuth se zobrazí:

    Access blocked: Authorization Error
    The OAuth client was not found.
    Error 401: invalid_client

Zachycený screenshot potvrzuje chybu na accounts.google.com. Parametry
authError a client_id z URL se nesmí ukládat do logu ani do tasku.

## Pravděpodobná příčina

Použitý OAuth client ID není platný, není dostupný v aktuální Google Cloud
konfiguraci, případně neodpovídá klientovi očekávanému implementací. Nejde o
chybu keyringu ani o chybu překladu.

## Požadované řešení

- Zjistit, odkud aplikace načítá Google OAuth client ID a zda je hodnota
  přítomná, nenulová a bezpečně redigovaná v diagnostice.
- Doplnit provider-specific configuration pro OAuth client ID, případně
  zdokumentovat přesné výchozí nastavení a podporované env/config reference.
- Ověřit redirect URI, OAuth consent screen, aktivní Google API projekt a typ
  OAuth klienta podle skutečného browser flow.
- Chybu invalid_client převést na srozumitelnou lokální diagnostiku s návodem,
  nikoli pouze zobrazit obecnou stránku Google.
- Přidat offline test konfigurace klienta a test redakce client ID/tokenů;
  živý smoke test musí být oddělený a nesmí zapisovat credentials.

## Acceptance

- Platný OAuth client lze načíst z podporované konfigurace a browser flow jej
  použije.
- Chybějící nebo neplatný client ID skončí před otevřením browseru
  diagnostikou, pokud je to možné, nebo se po návratu Google zobrazí
  srozumitelná náprava.
- Redirect URI a OAuth scope jsou dokumentované a ověřené proti implementaci.
- Client ID, authError, access token ani refresh token se nezapisují do
  queue.json, běžných logů, reportů ani tasků.
- Offline testy proběhnou bez připojení ke Google; živý test je volitelný.

## Zbývající plán pro implementátora (revize 2026-10-11)

Status test a uživatelem požadovaný odklad zůstávají. Placeholder klienta již
byl odstraněn; neopakovat implementaci konfigurace ani neotvírat prohlížeč
v rámci offline revize. Správný formát ID neprokazuje existenci klienta u Google.

### G01 – potvrdit implementovanou opravu offline

- Dependency: code-only kontrola může proběhnout nezávisle; k uzavření celého
  tasku je potřebné dokončení keyring issue a G02.
- Kontext: ai/oauth.py (resolve_gemini_oauth_client_id, GeminiOAuth.login,
  BrowserOAuth.login), ai/profiles.py a příslušné konfigurace v queue_app.py.
  Testy: test/test_ai_oauth.py, test/test_ai_profiles.py,
  test/test_cloud_provider_configuration.py; nečíst konfiguraci s credentials.
- Výsledek: chybějící/placeholder client ID selže před browser_open; profil
  nebo TRANSLATE_GEMINI_OAUTH_CLIENT_ID dodá ID. Do comments zapsat skutečný
  loopback redirect, scope a typ klienta podle implementace, bez konkrétního ID.
- Ověření: uvedené testovací soubory přes python -m pytest ... -q, PYTHONPATH=src.
  Rozlišení lokální syntaktické kontroly a živé registrace je povinné.
- Odhad: 20–40 min, 10–50 logických řádků případných regresí/evidence,
  3k–6k pracovních tokenů. Bez nové reprodukce měnit jen evidenci.

### G02 – živé ověření po obnovení uživatelského testování

- Dependency: G01 a K02 v keyring issue; čeká na uživatele.
- Potřebný vstup: skutečný Desktop OAuth client nakonfigurovaný lokálně,
  oprávnění k příslušnému projektu a souhlas uživatele obnovit browser test.
  Klíče ani client ID neposílat do chatu/tasku; stačí potvrdit připravenost.
- Postup: Login → autorizace → loopback callback → uložení tokenu → již
  existující negenerativní probe. Po restartu ověřit načtení/refresh, nakonec
  logout. Nespouštět dokumentový překlad ani měnit Google projekt automaticky.
- Výsledek: evidence skutečného úspěchu nebo bezpečný chybový kód a etapa,
  bez celé OAuth URL, kódu, client ID či tokenů. Pokud Google klient odmítne
  před callbackem, aplikace nemusí obdržet chybu invalid_client; neslibovat
  její automatickou lokální diagnostiku. Odlišit browser chybu a timeout.
- Ověření: ruční záznam etap a výsledků. Neúspěch → comments s reprodukcí,
  cílená opravná subúloha a test; nepřepisovat již funkční auth cestu naslepo.
- Odhad: 10–20 min aktivního ověření, 0–15 řádků evidence,
  1k–3k tokenů; externí konfigurace/čekání nemají známý časový odhad.

Restart: zaznamenat poslední G-krok a etapu; přetrvávající status test znamená
chybějící živou evidenci, nikoli potvrzenou regresi. Pro případnou změnu toku
aktualizovat A16 a P03 v doc/modularization-analysis.md. Bez změny toku se
diagramy nepřekreslují.

## comments

2026-10-11: Task založen podle manuálního GUI testu. Google OAuth odpověděl 401 invalid_client a uvedl, že OAuth client nebyl nalezen. Implementace nezahájena.
2026-10-11: Průzkum potvrdil příčinu v GeminiOAuth: výchozí client_id bylo pevně nastavené na placeholder doctranslate-desktop. Zahájena oprava: skutečný client ID lze zadat v Gemini Configuration nebo přes TRANSLATE_GEMINI_OAUTH_CLIENT_ID, před otevřením browseru se validuje formát a placeholder už se nepoužije.
2026-10-11: Doplněny offline regresní testy pro chybějící client ID, placeholder, env konfiguraci a uložení client ID v profilu. Celá sada prošla 133/133 a compileall prošel. Živý Google OAuth test s reálným client ID zatím nebyl proveden.
2026-10-11: Manuální GUI ověření potvrdilo očekávané chování: Login zobrazil lokální dialog „Gemini OAuth client ID is not configured“ s návodem pro Gemini Configuration nebo TRANSLATE_GEMINI_OAUTH_CLIENT_ID a bez otevření chybné Google autorizace. Task zůstává ve stavu test/progress do ověření s platným client ID.
2026-10-11: Doplněny G01–G02, potřebný lokální vstup, bezpečná evidence a odhady. Task zůstává test a živá autorizace je na žádost uživatele odložená. Formát ID ani offline fake exchange nejsou důkazem funkčního Google klienta. Žádný browser/provider/model se při revizi nespouštěl.
