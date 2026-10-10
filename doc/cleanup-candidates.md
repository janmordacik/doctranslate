# Kandidáti na úklid

Stav kontroly: 2026-10-10. Tři hlavní kandidáti byly odstraněny na pokyn uživatele.

## Odstraněno

| Soubor | Důvod | Riziko |
|---|---|---|
| translate_job.json | Starý ukazatel poslední legacy práce obsahuje cestu D:\\install\\doctranslate. Aktuální výchozí plán existuje přímo vedle výstupního PDF a queue workflow ho nepotřebuje. | Nízké; odstraní pouze automatický ukazatel poslední práce, ne plán ani překlady. |
| Lucio Russo – Zapomenutá revoluce-layout.ollama-error.json | Diagnostika neúspěšného historického požadavku qwen3.8:27b; překladový HTML/PDF výstup i plán jsou dokončené. | Nízké po archivaci případné diagnostiky; soubor může být užitečný jen při zpětném rozboru chyby. |
| tmp_local_agent_checkpoint.json | Checkpoint neúspěšné Qwen delegace; obsahuje pouze stav selhání workeru a starou diagnostiku Git oprávnění. | Nízké; lokální agent byl nahrazen přímou implementací. |

Doprovodné soubory stejného neúspěšného pokusu, které nejsou JSON, jsou:
- tmp/tmp_local_agent_in.md
- tmp/tmp_local_agent_out.log

## Zachovat

| Soubor | Důvod |
|---|---|
| Lucio Russo – Zapomenutá revoluce-layout.plan.json | Aktivní checkpoint a metadata dokončeného překladu; obsahuje hash zdroje, fázi, stav HTML/PDF a layout revision. |
| Lucio Russo – Zapomenutá revoluce-layout.translations.json | Překladová cache pro obnovu bez opakovaného volání Ollamy. |
| doctranslate/openapi/dist/openapi.json | Generovaný OpenAPI kontrakt v odděleném vnořeném repozitáři; nesouvisí s tímto překladačem. |
| doctranslate/workers/edge-api/package.json | Konfigurace Node/Cloudflare workeru ve vnořeném repozitáři. |
| doctranslate/workers/edge-api/package-lock.json | Zamčené závislosti vnořeného repozitáře. |

## Aktuálně nevytvořené runtime JSON

V kořeni zatím nejsou:
- queue.json
- worker-state.json

Vytvoří je až první použití nové fronty/workeru. Jsou ignorované v Gitu společně s locky a dočasnými soubory.

## Stav po úklidu

- Odstraněny byly tři hlavní kandidáty uvedené výše.
- tmp/tmp_local_agent_in.md a tmp/tmp_local_agent_out.log zůstávají jako volitelné pracovní artefakty; lze je odstranit samostatně.
- Plán a translations cache zůstávají zachovány.
