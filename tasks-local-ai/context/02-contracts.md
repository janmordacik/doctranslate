# 02 — Datové smlouvy

## XHTML dokument

Dokument obsahuje metadata zdroje, cílový jazyk, rozměry/layout informace a
bloky v pořadí čtení. Blok nese stabilní ID, stránku, pořadí, text, případné
inline markup a bounding box. Jádro nesmí importovat PDF knihovnu.

Výsledek backendu musí mít jednoznačnou cardinalitu vůči vstupu. U textu s
inline značkami nesmí prostá textová náhrada tiše poškodit entity nebo tagy;
pro více textových uzlů použít strukturovaný výsledek, nebo operaci odmítnout
s čitelnou chybou.

## Job

~~~json
{
  "kind": "job",
  "id": "stable-id",
  "input": "source.pdf",
  "output": "translated.pdf",
  "inlang": "en",
  "outlang": "cs",
  "model": "model-name",
  "phase": "both",
  "state": "prepared",
  "progress": 0.0,
  "error": null
}
~~~

Povinná pole a povolené hodnoty validovat při načtení i zápisu. Job nesmí
zdědit model, cesty nebo rozsah předchozího jobu jen kvůli globálním stavům.

## Fronta

~~~json
{
  "schema": 1,
  "revision": 0,
  "updated_at": "ISO-8601",
  "items": [
    {
      "kind": "control",
      "id": "worker-control",
      "command": null,
      "request_id": null,
      "updated_at": null
    }
  ]
}
~~~

Control item není job. stop je jednorázový příkaz spotřebovaný workerem po
dávce. Revision slouží k odhalení přepsání novějšího snapshotu.

## Konfigurace

Konfigurace je volitelný JSON soubor s workdir, jazykem GUI a endpointem Ollamy.
Chybějící konfigurace použije bezpečné defaulty; poškozená nebo nečitelná
konfigurace musí mít jasnou chybu, ne tichou ztrátu nastavení.
