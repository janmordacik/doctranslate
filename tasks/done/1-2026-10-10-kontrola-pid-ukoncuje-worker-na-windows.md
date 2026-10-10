status: done
last change: 2026-10-10
dependency: none
group: runtime/process
type: bug
description:
Kontrola PID ukončuje proces na Windows
Priority: 1 (critical)
Created: 2026-10-10

queue_app.process_alive() volá os.kill(pid, 0). Na Windows nejde o čtecí kontrolu: os.kill s tímto signálem používá TerminateProcess. Kontrola GUI/CLI nebo stale locku proto může ukončit worker či jiný proces se znovu použitým PID.

Evidence:
src/doctranslate/queue_app.py: process_alive(), FileLock._stale(), WorkerController.running(). Statická kontrola a dokumentace https://docs.python.org/3/library/os.html#os.kill. Záměrně nebylo testováno na živém workeru.

Recommended change:
Na Windows použít čtecí OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION) + GetExitCodeProcess + CloseHandle; rozlišit neexistenci od access denied a při nejistotě neodstraňovat lock. Unixovou kontrolu ponechat v samostatné větvi. Nezavádět psutil jen kvůli jednomu volání.

Acceptance:
Čtecí probe vlastního izolovaného subprocessu ho neukončí; mrtvý PID vrátí false; access denied nezpůsobí stale recovery živého locku. Testy nesmí volat původní nebezpečnou funkci na cizí PID.

Implementation:
Opraveno 2026-10-10. Ověření PID používá čtecí platformní kontrolu; worker se spouští jako modul s logem; CLI add zapisuje v jedné transakci; GUI merge zachovává novější runtime stav workeru.

comments:
2026-10-10: Issue vytvořen z revize projektu; odhad priority podle dopadu a evidence. Odděleno ověřené chování od statického rizika.
2026-10-10: Doplněna metadata dependency, group a type podle projektových pravidel. Závislosti určují předpoklady implementace; stav created zachován.
2026-10-10: Oprava implementována a ověřena cílenými i celými offline testy; issue uzavřeno.
