DOCTRANSLATE
============

Nástroj překládá dokumenty přes lokální Ollamu a snaží se zachovat jejich
strukturu a rozložení. Aktuální produkční cesta je:

    vstupní dokument -> HTML/XHTML -> výstupní dokument

Nejlépe podporovaným formátem je PDF. Překladová data se ukládají průběžně,
takže lze po přerušení pokračovat od posledního checkpointu.

RYCHLÉ SPUŠTĚNÍ
---------------

1. Nainstalujte Python 3.11 nebo novější.
2. Nainstalujte projektové závislosti podle pyproject.toml.
3. Pro překlad spusťte Ollamu a stáhněte model, například:

       ollama pull translategemma:12b

4. V kořeni projektu spusťte:

       translate.cmd

   Bez parametrů se otevře GUI. V něm nastavte pracovní adresář, přidejte
   úlohu a stiskněte Aktualizovat úlohy.

PŘÍMÉ PŘÍKAZY
-------------

Překlad i sazba v jednom běhu:

    translate.cmd --infile "book.pdf" --outfile "book-cs.pdf" --phase both

Pouze překlad do HTML:

    translate.cmd --infile "book.pdf" --outfile "book-cs.pdf" --phase html

Pouze vytvoření výstupu z hotového HTML:

    translate.cmd --phase pdf --infile "book.pdf" --htmlfile "book-cs.html" --outfile "book-cs.pdf"

Další možnosti a řešení chyb jsou v doc/user-manual.md.

ÚKLID PRACOVNÍCH ARTEFAKTŮ
--------------------------

Náhled úklidu bez mazání:

    translate.cmd cleanup --dry-run

Worker úklid po ukončení provádí automaticky. Ručně ho lze spustit příkazem
`translate.cmd cleanup`; nemaže vstupní PDF, výstupní PDF ani HTML.
Výchozí limit je 50 MiB na jeden sidecar a 250 MiB souhrnně.

Poznámka: vstupní názvy mohou obsahovat běžné znaky. Automaticky vytvářené
názvy výstupů jsou normalizované bez diakritiky; mezery a spojovníky zůstávají.
