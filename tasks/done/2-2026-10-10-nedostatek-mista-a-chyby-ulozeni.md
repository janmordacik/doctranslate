status: done
last change: 2026-10-10
dependency: ../done/2-2026-10-10-lock-recovery-a-selhani-zapisu.md
group: persistence/storage
type: bug
description:
Chybí včasná kontrola prostoru a řízené chyby ukládání
Priority: 2 (high)
Created: 2026-10-10

Atomické zápisy většinou chrání předchozí soubor, ale neexistuje preflight prostoru a zapisovatelnosti. ENOSPC v označení jobu nebo worker-state mimo try může shodit celý worker bez dohledatelného výsledku. Queue backup se zapisuje přímo; chyba je ignorována. JSON tmp/config tmp nemusí být uklizené. PDF vyžaduje místo i na celý dočasný výstup, fonty a checkpointy.

Evidence:
Mock ENOSPC při atomic_write fronty: errno 28, původní queue.json zůstane byte-for-byte stejný. queue_worker.mark_job/write_state před try; config.save_config, atomic_json, QueueStore.transaction a save_pdf_atomic.

Recommended change:
Preflight existujícího cílového volume a temp volume: dostupný prostor + krátký write probe s úklidem. Odhad je varování, nikoli záruka. OSError zachytit i při startu/mark_job/stavu; původní chybu vždy vypsat do fallback stderr. Zálohu vytvořit atomicky z validního snapshotu; selhání pojmenovat. Neopakovat AI požadavek kvůli chybě zápisu.

Acceptance:
Simulovat ENOSPC, EACCES a selhání replace v jednotlivých artefaktech. Poslední potvrzené soubory zůstanou použitelné, chybu zápisu lze dohledat i bez možnosti logování na zaplněném disku.

Implementation:
Přidán storage_preflight s kontrolou volného místa na cílovém svazku a atomický JSON zápis nyní převádí chyby do StorageError, uklízí dočasný soubor a zachovává předchozí cíl. Worker zapisuje diagnostický stav best-effort a při chybě zpracování vypíše čitelnou chybu; selhání aktualizace backupu fronty se loguje na stderr. Sazbu PDF provádí uživatel sám.

comments:
2026-10-10: Issue vytvořen z revize projektu; odhad priority podle dopadu a evidence. Odděleno ověřené chování od statického rizika.
2026-10-10: Doplněna metadata dependency, group a type podle projektových pravidel. Závislosti určují předpoklady implementace; stav created zachován.
2026-10-10: Implementováno přímo v queue_app.py a queue_worker.py; bez použití lokálního agenta podle projektového AGENTS.md.
2026-10-10: Ověřeno 20 testy fronty. Fault injection pokrývá nedostatek místa, EACCES/selhání replace, zachování původního souboru a úklid .tmp. PDF/temp svazek mimo JSON frontu zůstává mimo rozsah.
