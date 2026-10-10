# 04 — Kvalita, testy a evidence

## Povinné minimum každého tasku

- nejprve inspekuj relevantní současný kód a testy;
- změň jen vymezenou oblast;
- přidej regresní test pro novou chybu nebo pravidlo;
- spusť cílené testy a uveď přesný příkaz a výsledek;
- pokud je možné, spusť i celou offline suite;
- zkontroluj diff a stav repozitáře;
- nedělej vizuální PDF sazbu ani živý překlad bez explicitního zadání;
- při chybě prostředí zapiš reprodukci, dopad a workaround; nevyráběj falešný
  úspěch pomocí přeskočení testu.

## Akceptace balíčku

Hotový task má:

1. jasně vymezené změněné soubory;
2. test, který selže před opravou nebo ověřuje nový kontrakt;
3. čitelnou chybu pro očekávané provozní selhání;
4. zachování veřejného CLI/API, pokud task výslovně nemění kontrakt;
5. komentář s datem, stavem a známými limity.

Pro PDF layout je offline test autoritativní pro strukturu XHTML a metadata;
vzhled PDF se považuje za ověřený až po ručním renderu a vizuální kontrole.
