status: test
last change: 2026-10-11
dependency: 2-2026-10-11-login-chybejici-keyring.md, done/3-2026-10-10-gemini-browser-oauth.md
group: ai/providers/gemini/oauth
type: bug
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

## comments

2026-10-11: Task založen podle manuálního GUI testu. Google OAuth odpověděl 401 invalid_client a uvedl, že OAuth client nebyl nalezen. Implementace nezahájena.
2026-10-11: Průzkum potvrdil příčinu v GeminiOAuth: výchozí client_id bylo pevně nastavené na placeholder doctranslate-desktop. Zahájena oprava: skutečný client ID lze zadat v Gemini Configuration nebo přes TRANSLATE_GEMINI_OAUTH_CLIENT_ID, před otevřením browseru se validuje formát a placeholder už se nepoužije.
2026-10-11: Doplněny offline regresní testy pro chybějící client ID, placeholder, env konfiguraci a uložení client ID v profilu. Celá sada prošla 133/133 a compileall prošel. Živý Google OAuth test s reálným client ID zatím nebyl proveden.
2026-10-11: Manuální GUI ověření potvrdilo očekávané chování: Login zobrazil lokální dialog „Gemini OAuth client ID is not configured“ s návodem pro Gemini Configuration nebo TRANSLATE_GEMINI_OAUTH_CLIENT_ID a bez otevření chybné Google autorizace. Task zůstává ve stavu test/progress do ověření s platným client ID.
