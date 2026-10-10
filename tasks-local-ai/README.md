# Izolovaný balíček úloh pro lokálního agenta

Tento adresář je samostatný pracovní balíček. Úlohy v něm nesmějí předpokládat,
že byla dokončena některá úloha z hlavního adresáře tasks/, že existuje
konkrétní implementace, ani že lokální agent zná historii projektu. Agent musí
vždy nejdříve prozkoumat aktuální checkout a teprve potom měnit kód.

V této revizi se agent nespouští. Soubory jsou pouze připravené instrukce pro
budoucí explicitní delegaci. Samy neautorizují spuštění agenta, změnu Continue,
změnu globální konfigurace, instalaci modelu, síťové operace ani commit.

## Jak balíček používat

1. Načti tento soubor a pouze kontext potřebný pro právě delegovaný task.
2. Zkontroluj aktuální checkout; nepřebírej tvrzení o hotových funkcích z jiné
   dokumentace.
3. Zpracuj tasky v pořadí uvedeném v tasks/INDEX.md.
4. V jednom běhu řeš pouze jeden task. Závislosti jsou pořadí práce, nikoli
   povolení přeskočit kontrolu skutečného stavu kódu.
5. Před změnou zkontroluj git status --short. Neměň nesouvisející soubory.
6. Po změně spusť jen testy, které jsou dostupné; chybějící Python, závislosti,
   Ollama nebo model zaznamenej jako blokaci s přesným příkazem a výstupem.
7. Agent nesmí commitovat ani pushovat. Po dokončení uveď změněné soubory,
   testy, známé limity a případné další potřebné informace.

## Vrstvy kontextu

- context/00-scope.md — účel, hranice a neměnné požadavky.
- context/01-architecture.md — cílové komponenty a životní cyklus.
- context/02-contracts.md — datové smlouvy XHTML, jobu a fronty.
- context/03-operational-constraints.md — chování bez Pythonu, Ollamy,
  modelu, místa na disku nebo zapisovatelného adresáře.
- context/04-quality.md — minimální testovací a dokumentační pravidla.
- context/05-tools-cookbook.md — kopie obecných osvědčených postupů pro
  práci s nástroji v izolovaném balíčku.

## Tasky

Tasky jsou záměrně malé a izolované. Každý obsahuje vlastní popis, závislosti,
akceptační kritéria a požadované ověření. Pokud kontrola checkoutu ukáže, že
něco už existuje, task se nemá slepě přepisovat: agent popíše stav, doplní nebo
opraví jen chybějící část a zachová minimální diff.
