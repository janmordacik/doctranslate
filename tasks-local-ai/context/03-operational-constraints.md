# 03 — Provozní omezení

Každý task musí navrhnout chování pro níže uvedené situace. Pokud je daná
situace mimo jeho rozsah, přidej testovací bod nebo explicitní poznámku místo
skrytého předpokladu.

| Situace | Požadované chování |
|---|---|
| Chybí Python nebo není v PATH | launcher vypíše instalační/diagnostickou chybu a vrátí nenulový kód |
| Python je příliš starý | ověřit minimální verzi před importem aplikace |
| Chybí volitelná PDF knihovna | CLI/GUI základní funkce mohou fungovat; PDF akce vrátí návod |
| Chybí Tk nebo desktop | GUI vrátí čitelnou chybu; CLI nesmí padat tracebackem |
| Ollama neběží | discovery označí offline; aplikace nesmí zaměnit stav za prázdný seznam modelů |
| Ollama běží bez modelů | označit empty a neprovádět automatickou instalaci |
| Vybraný model neexistuje | zachovat volbu, ale před překladem vrátit čitelnou chybu |
| Model odpovídá pomalu nebo timeoutuje | respektovat timeout/retry a zachovat checkpoint |
| Disk je plný nebo adresář readonly | nezničit platný JSON; vrátit konkrétní I/O chybu |
| Fronta je poškozená | zkusit pouze validní zálohu a oznámit, že byla použita |
| Vstup neexistuje nebo je šifrovaný | skončit před voláním backendu s přesnou cestou a důvodem |
| PDF nemá extrahovatelný text | odmítnout textovou fázi a uvést, že OCR není součástí |
| Worker už běží | druhá instance nesmí zpracovávat stejné joby |
| Worker spadne nebo je vypnut počítač | aktuální job zůstane in_progress a pokračuje z checkpointu |
| Stop/pause během dávky | změna se uplatní po dokončení právě běžící dávky |
