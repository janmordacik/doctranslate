status: created
last change: 2026-10-11
dependency: ../done/2-2026-10-10-ai-profily-a-bezpecna-autentizace.md
group: ai/providers/authentication
type: feature
description: Konfigurace cloudových AI providerů v GUI a ověření dostupnosti
Priority: 2 (high)
Created: 2026-10-11

## Důvod

OpenAI, Gemini a Claude mají základní backendy a offline testy, ale v praktickém
použití nejsou dostatečně konfigurovatelné. Uživatel nemá spolehlivou cestu, jak
nastavit autentizaci, vybrat dostupný model a ověřit připojení před spuštěním
dlouhého překladu. Chyby konfigurace se nesmí projevit až po zahájení jobu.

## Požadavky

1. Provider-specific konfigurace v GUI:
   - OpenAI: API key, endpoint podle potřeby, model.
   - Gemini: API key nebo podporovaný OAuth login, model a potřebné volby.
   - Claude: API key, endpoint podle potřeby, model.
2. API klíče nikdy neukládat do jobu, JSON profilu, logu ani diagnostického
   sidecaru; ukládat je pouze přes bezpečný credential store nebo explicitní
   environment reference.
3. Login a Configuration musí mít jasný stav:
   - podporovaná akce otevře provider-specific UI,
   - nepodporovaná akce je skrytá nebo disabled s vysvětlením,
   - selhání zobrazí lokalizovanou chybu a zapíše bezpečnou diagnostickou událost.
4. Výběr modelu:
   - načíst aktuální nabídku modelů z provider API, pokud to API umožňuje,
   - jinak umožnit ruční zadání a validovat neprázdný model,
   - oddělit dostupnost modelu od dostupnosti provideru.
5. Přidat neplacený smoke test typu ping/pong nebo provider probe:
   - ověří endpoint, autentizaci a zvolený model,
   - nepřekládá dokument a negeneruje běžný překladový obsah,
   - zobrazí latenci, HTTP/API stav a srozumitelný návod k opravě,
   - nesmí logovat API klíč, token, hlavičky ani obsah odpovědi.
6. Worker musí před prvním skutečným jobem používat stejný profil a credential
   resolver jako GUI smoke test.

## Acceptance

- Pro každý cloudový provider lze v GUI založit nebo upravit profil bez ruční
  editace JSON souboru.
- Uživatel může bezpečně zadat nebo odkázat API klíč a zvolit model.
- Smoke test rozliší alespoň: chybějící klíč, odmítnutou autentizaci, nedostupný
  endpoint, neplatný model, rate limit a úspěšnou odpověď.
- Úspěšný smoke test neprovede překlad dokumentu a neúčtuje překladový request.
- Worker po stejném profilu skutečně vytvoří backend a použije nastavenou
  autentizaci; GUI a worker nesmí mít odlišná pravidla.
- Offline unit/integration testy pokrývají GUI stav, credential store, provider
  probe, maskování tajných údajů a chybové mapování. Live smoke test je volitelný
  a vyžaduje uživatelovy credentials, síť a souhlas s případnými náklady.
- Aktualizovat autoritativní Mermaid classDiagram a sequenceDiagram procesu
  konfigurace a provider probe.

## Návrh postupu

1. Zpřesnit provider capability contract: auth methods, configuration schema,
   model discovery a probe.
2. Oddělit provider-specific konfiguraci od obecného job formuláře.
3. Implementovat bezpečné uložení credentialu a jednotný resolver pro GUI/worker.
4. Implementovat model discovery/manual model validation.
5. Implementovat probe endpoint a GUI výsledek.
6. Přidat offline testy a případně ruční live ověření.

## comments

2026-10-11: Task vytvořen na základě praktického ověření GUI. Cloudové
providery mají offline backendové testy, ale workflow Login/Configuration/model
selection/credential entry/probe není dokončené a nebylo ověřeno live.
