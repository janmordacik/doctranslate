# Offline kalibrační scénáře

Scénáře jsou připravené, ale v této revizi se nespouštějí.

| Level | Scénář | Očekávané ověření |
|---|---|---|
| 1 | Najdi definici QueueStore a vypiš její veřejné metody. | Read-only, bez změn. |
| 2 | Přidej jeden izolovaný test pro existující validátor. | Malý diff a cílený test. |
| 4 | Oprav jednu chybu v queue_app.py a doplň regresní test. | Review diffu a offline suite. |
| 8 | Změň jednu hranici worker lifecycle ve dvou souborech. | Test, status, žádné nesouvisející změny. |
| 16 | Malá více-souborová změna podle existujícího tasku. | Nezávislá validace Codexem; bez delegace nad neověřený level. |

Každý probe musí mít čerstvý projektový kontext, jasný acceptance test,
časový údaj, fingerprint backendu a výsledek pass/fail. Probe nesmí sahat na
živou Ollamu, modely, PDF výstupy ani globální konfiguraci.
