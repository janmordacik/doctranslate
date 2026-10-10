# Izolované pořadí tasků

Tasky jsou připravené, ale v této revizi nebyl žádný agent spuštěn.

| Pořadí | Soubor | Závislost | Rozsah |
|---:|---|---|---|
| 1 | 01-baseline-and-bootstrap.md | none | baseline, launcher, diagnostika |
| 2 | 02-xhtml-contract.md | 01 | XHTML model a validace |
| 3 | 03-translation-pipeline.md | 02 | backend a markup-safe překlad |
| 4 | 04-format-adapters.md | 02, 03 | adaptery formátů |
| 5 | 05-queue-store.md | 01 | JSON repository, lock, atomický zápis |
| 6 | 06-worker-lifecycle.md | 05 | worker, stavy, restart |
| 7 | 07-frontend-controls.md | 05, 06 | GUI/CLI ovládání |
| 8 | 08-ollama-discovery.md | 01, 07 | modely a diagnostika Ollamy |
| 9 | 09-observability-and-errors.md | 01, 05, 06 | logy, výjimky, edge cases |
| 10 | 10-integration-and-documentation.md | 02–09 | integrační testy a dokumentace |

Závislost znamená pouze doporučené pořadí. Každý task musí skutečný stav
checkoutu ověřit znovu. Pokud se ukáže, že rodičovská oblast již existuje,
task se zmenší na chybějící část a tuto odchylku zapíše do comments.
