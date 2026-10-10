status: done
last change: 2026-10-10
dependency: ../done/1-2026-10-10-kontrola-pid-ukoncuje-worker-na-windows.md
group: runtime/worker/startup
type: bug
description:
Worker nelze spustit současným launcherem
Priority: 2 (high)
Created: 2026-10-10

WorkerController.start() spouští cestu queue_worker.py, který má relativní import .queue_app. Worker.run_job() má navíc import translate a __import__('queue_app') ze starých cest. Výstup procesu je přesměrován do DEVNULL; GUI tak může oznámit start bez skutečně běžícího workeru. Explicitní -gui má stejný starý import.

Evidence:
Reprodukováno: python src/doctranslate/queue_worker.py --help -> ImportError. Izolované volání Worker.run_job(None,{}) -> ModuleNotFoundError: translate před jakoukoli prací. translate.py entrypoint(): from queue_app import gui_main.

Recommended change:
Spouštět sys.executable -m doctranslate.queue_worker s dostupným balíčkem; opravit relativní importy, použít již importovaný utc_now. Uložit stderr do worker logu a potvrdit start existencí stavu, ne jen návratem Popen. Neobnovovat staré wrappery v kořeni.

Acceptance:
Modulový --help a start prázdné izolované fronty proběhnou bez Ollamy/PDF. Test fake backend jobu projde až do done. Chyba startu má srozumitelné hlášení a log.

Implementation:
Opraveno 2026-10-10. Ověření PID používá čtecí platformní kontrolu; worker se spouští jako modul s logem; CLI add zapisuje v jedné transakci; GUI merge zachovává novější runtime stav workeru.

comments:
2026-10-10: Issue vytvořen z revize projektu; odhad priority podle dopadu a evidence. Odděleno ověřené chování od statického rizika.
2026-10-10: Doplněna metadata dependency, group a type podle projektových pravidel. Závislosti určují předpoklady implementace; stav created zachován.
2026-10-10: Oprava implementována a ověřena cílenými i celými offline testy; issue uzavřeno.
