status: done
last change: 2026-10-10
dependency: ../done/1-2026-10-10-kontrola-pid-ukoncuje-worker-na-windows.md, ../done/2-2026-10-10-worker-se-nespusti-pres-balicek.md, ../done/2-2026-10-10-lock-recovery-a-selhani-zapisu.md, ../done/2-2026-10-10-update-fronty-prepisuje-novejsi-stavy.md, ../done/2-2026-10-10-heartbeat-stop-pause-a-zmeny-aktivniho-jobu.md, ../done/3-2026-10-10-bootstrap-zavislosti-a-jednotne-chyby-cli.md
group: quality/tests/integration
type: test
description:
Zelené testy nepokrývají skutečný start a provozní selhání
Priority: 3 (normal)
Created: 2026-10-10

16 stávajících testů prochází, ale worker se v nich skutečně nespouští a nevolá run_job. Proto neodhalily importy, Windows PID kontrolu, heartbeat ani lost updates. Regresní archiv není automaticky důkaz vizuální shody PDF.

Evidence:
python s PYTHONPATH src + pytest test -q -> 16 passed in 4.36 s. test_queue_app kontroluje store, lock reuse a choose_job; chybí start/subprocess a backend boundary.

Recommended change:
Ke konkrétním opravám přidat malé regresní testy: module smoke bez práce, fake backend worker lifecycle, Windows liveness s vlastním childem až po opravě, konflikty revision a fault injection ENOSPC/EACCES/replace. Neinstalovat/zapínat živou Ollamu a negenerovat knižní PDF v běžném suite.

Acceptance:
Testy odhalí uvedené regresní scénáře a běží offline; manuální PDF sazba zůstává na uživateli. Screenshot/visual QA a benchmarky vést jako samostatné volitelné ověření.

Implementation:
Regresní suite pokrývá module launch, bezpečnou kontrolu PID, stale lock/recovery, lost update, stop/pause po dávce, fault injection storage, bootstrap bez PyMuPDF a offline fake-backend průchod Worker.run_job. Živá Ollama, modely a vizuální PDF QA zůstávají mimo běžný suite.

comments:
2026-10-10: Issue vytvořen z revize projektu; odhad priority podle dopadu a evidence. Odděleno ověřené chování od statického rizika.
2026-10-10: Doplněna metadata dependency, group a type podle projektových pravidel. Závislosti určují předpoklady implementace; stav created zachován. Jednotlivé regresní testy jsou součástí rodičovských oprav; tento task zastřešuje integrační ověření.
2026-10-10: Doplněno 11 offline regresních testů pro PID, lock, queue merge, worker module launch, Start a XHTML.
2026-10-10: Doplněn fake-backend test skutečného Worker.run_job; kombinovaná queue suite má nyní 24 testů a prochází. Offline pokrytí je dostatečné pro good-enough uzavření; živá Ollama a vizuální PDF kontrola zůstávají manuální.
