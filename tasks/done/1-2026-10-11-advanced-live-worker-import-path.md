status: done
last change: 2026-10-11
type: bug
group: testing/integration/advanced-ollama/worker
dependency: 2-2026-10-11-advanced-live-pdf-retry-test

description: >-
  Opravit první skutečný běh live testu advanced PDF překladu. Worker spuštěný
  přes WorkerController skončil před zpracováním jobu, protože subprocess
  nedostal importní kořen src. Test nesmí zůstat viset do celkového timeoutu,
  pokud worker neočekávaně skončí; musí připojit relevantní konec worker logu.

observed_failure:
- Příkaz: python test/live_advanced_pdf.py --input test/mock/sample-en.pdf
  --run-dir tmp/advanced-live --model translategemma:4b
  --ollama-url http://127.0.0.1:11434 --timeout-seconds 1800
- Konfigurace: advanced, Ollama, translategemma:4b, phase=both,
  manage_ollama=false.
- Job: job-63ff02446561, zůstal ve stavu prepared.
- worker.log:
  C:\Python314\python.exe: No module named doctranslate.queue_worker
- Příčina: queue_app.py počítal PYTHONPATH z parents[2], tedy z kořene
  projektu; balíček je v parents[1] / src.

plan and estimates:
- S01: Opravit importní kořen worker subprocessu a doplnit regresní assertion.
  Estimate: 5 minut, 15 logických řádků, 200 tokenů. Dependencies: none.
- S02: Zrychlit diagnostiku live testu při předčasném ukončení workeru včetně
  konce worker.log. Estimate: 5 minut, 25 logických řádků, 300 tokenů.
  Dependencies: S01.
- S03: Zopakovat live test, analyzovat logy a uzavřít task pouze po ověřeném
  výsledném XHTML a PDF. Estimate: 10 minut aktivní práce, 20 logických řádků,
  250 tokenů. Dependencies: S01, S02.

acceptance:
- Worker spuštěný přes WorkerController načte doctranslate.queue_worker z
  projektového src bez závislosti na instalaci balíčku.
- Regresní test ověřuje příkaz i PYTHONPATH subprocessu.
- Live test při předčasném ukončení workeru skončí diagnostickou chybou,
  nikoli čekáním celého timeoutu.
- Opakovaný live test s dostupným Ollama API dokončí job done a vytvoří
  čitelné XHTML i PDF.

comments:
- 2026-10-11: První live běh přerušil supervisor po zjištění, že worker skončil
  na ModuleNotFoundError; výstup a worker log zůstaly v tmp/advanced-live.
- 2026-10-11: Oprava a opakovaný běh jsou připravené; task zůstává progress do
  ověření výsledného PDF.
- 2026-10-11: Druhý běh už spustil worker i model, ale skončil na `backend_error:
  Contextual provider response must contain a segments list`. Queue log potvrdil
  `supported_context=131072`, `runtime_context=131072`, `runtime_size_vram=3280952360`.
  Přidává se bounded response preview, velikost odpovědi, doba requestu a
  diagnostika parse/validation chyby, aby bylo možné určit skutečný formát
  odpovědi translategemma:4b.
- 2026-10-11: Diagnostika ukázala validní JSON s vrácenou obálkou `source` a
  pouze částečně přeloženým obsahem. Plain-text požadavek stejného modelu
  funguje. Prompt pro structured režim byl proto zpřesněn na přesný top-level
  kontrakt `segments`; parser nebude tiše přijímat vrácený zdrojový dokument.
- 2026-10-11: Třetí běh přeložil všech 10 segmentů a skončil až při přechodu
  do PDF na `AttributeError: module 'doctranslate.translate' has no attribute
  'set_activity'`. Ve stejném běhu retention cleanup ohlásil
  `descriptor 'casefold' for 'str' objects doesn't apply to a 'WindowsPath' object`.
  Obě chyby jsou opraveny v rámci tohoto tasku; live ověření ještě pokračuje.
- 2026-10-11: Opraven importní kořen workeru (`src`), předčasné ukončení workeru
  je nyní v live testu diagnostikováno okamžitě, structured prompt TranslateGemma
  vyžaduje top-level `segments`, loguje se tvar/velikost/náhled odpovědi a
  latence. Opraven přechod do PDF přes `worker.set_activity` a řazení Windows
  `Path` objektů v retention cleanup.
- 2026-10-11: Cílené testy prošly (63), live test skončil `done`, HTML/PDF byly
  vytvořeny a všechny tři stránky byly vizuálně zkontrolovány. Task uzavřen.
