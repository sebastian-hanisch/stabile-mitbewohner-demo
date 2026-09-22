# Stabile Mitbewohner – wenn Stabilität nicht immer möglich ist – Streamlit-Demo

Zehntes Stück der **Matching-Linie** der "Konzepte"-Reihe für die Website "Sebastian Hanisch – Operations Research und Machine Learning", erste von vier Erweiterungen des Gale-Shapley-Asts (inspiriert von Alvin Roths Arbeiten zu Marktdesign ohne Geld – als Nächstes folgen Krankenhaus-Zulassung, Top Trading Cycles und Nierentausch).

**Gale-Shapley** ([gale-shapley-demo](https://github.com/sebastian-hanisch/gale-shapley-demo)) findet immer eine stabile Paarung – solange es **zwei getrennte Seiten** gibt (Fahrzeuge und Aufträge). Hier gibt es nur **eine einzige Gruppe**: jeder Mitbewohner ordnet jeden anderen erreichbaren Mitbewohner. **Irvings Algorithmus** (1985) findet trotzdem eine stabile Paarung, wenn es eine gibt – aber anders als im zweiseitigen Fall **muss es keine geben**. Das ist der zentrale Unterschied dieses Stücks: nicht ein neues Ziel, sondern eine neue, härtere Frage – existiert überhaupt eine Lösung?
```
greedy-matching-demo (Wurzel: eine gewählte Zuordnung bleibt)                     [gebaut]
  ├─ augmenting-path-demo (Verbesserungswege: Paare optimal, Kosten blind)        [gebaut]
  │    ├─ hopcroft-karp-demo (viele kürzeste Wege je Phase)                       [gebaut]
  │    ├─ hungarian-demo (Ungarische Methode: Paare zuerst, dann Kosten)           [gebaut]
  │    │    └─ auction-algorithm-demo (Auktionsalgorithmus: dezentral)             [gebaut]
  │    └─ blossom-demo (allgemeine Graphen: ungerade Kreise, Kontraktion)          [gebaut]
  │        └─ weighted-blossom-demo (Ungarisch + Blossom, Konvergenz)              [gebaut]
  ├─ gale-shapley-demo (Vorlieben statt Kosten, stabil)                            [gebaut]
  │    ├─ stabile-mitbewohner-demo (eine Gruppe statt zwei Seiten)                 [dieses Stück]
  │    ├─ Krankenhaus-Zulassung (many-to-one, Kapazitäten)                        [geplant]
  │    └─ Top Trading Cycles → Nierentausch (Tausch ohne Geld)                    [geplant]
  └─ online-matching-demo (Aufträge kommen nacheinander)                          [gebaut]
```

## Ergebnis (Zahlen aus den Tests)

Jede hier genannte Zahl ist in `tests/test_claims.py` über die 100 festen Karten (Seeds 100000–100099, wo nicht anders angegeben über die 40 festen Sweep-Karten) belegt: 20 Mitbewohner, Reichweite 20 (mittlerer Grad 1,92), Vorlieben "Entfernung mit Streuung ±20 min". Aufwand = **Vorschläge**, nie Sekunden. Mittel und Median stehen zusammen.

| Frage | Ergebnis |
|---|---|
| Existiert überhaupt eine Lösung? | ⚠️ Nur auf **61 von 100** Karten. Wenn ja: im Mittel **7,21** Paare (Median 7, 5 bis 9), im Mittel 5,36 Personen harmlos unversorgt (Median 5,5). |
| Reichweite senkt die Lösbarkeit | ⚠️ Gegenintuitiv: Reichweite 10 / 15 / 20 / 25 / 30 / 40 / 60 / 100 (Grad 0,51 / 1,09 / 1,96 / 2,90 / 3,95 / 6,48 / 11,44 / 18,43) → lösbar auf **92,5 / 90 / 70 / 65 / 62,5 / 60 / 57,5 / 57,5 %** – streng fallend über den ganzen Sweep, mehr Kandidaten bedeuten mehr Gelegenheit für einen Kreis. |
| Streuung macht Vorlieben zyklisch genug | ✅ Reine Entfernung (k = 0) ist **immer** lösbar (100 %, 0 Rotationen); schon k = 5 senkt die Lösbarkeit auf 95 %, ab k ≈ 20 pendelt sie sich bei ~68–70 % ein – ein glatter Übergang, kein Sprung. |
| `dist`-Vorlieben sind ein Sonderfall | ✅ Immer eindeutig und exakt gleich der billigsten-Kante-zuerst-Paarung – auf allen 60 getesteten Karten 0 Rotationen (wie im zweiseitigen Fall bei `gale-shapley-demo`). |
| Rotationen mitten im Suchlauf | ⚠️ Auf **41 von 100** Karten mindestens eine (Mittel 0,43, Median 0, höchstens 2). |
| Naives Vorgehen gegen Irving | ⚠️ Auf **87 %** der lösbaren Karten hat naives Vorgehen (der Reihe nach den besten freien Nachbarn nehmen) mindestens ein blockierendes Paar (Mittel 2,08, Median 2, höchstens 5); der erreichte Rang ist durchgehend schlechter (Ø 0,376 gegen 0,219) – aber die Paarzahl stimmt auf 72 % der Karten trotzdem überein. |
| Eindeutigkeit, wenn lösbar | ✅ Anders als im zweiseitigen Fall (34 % mehrdeutig bei Gale-Shapley mit Streuung ±20) ist eine lösbare Karte hier meist eindeutig: 87–97 % je nach Größe (n = 8 bis 16, Brute-Force, 40 Karten je Größe), höchste beobachtete Anzahl stabiler Paarungen: 2. |
| Aufwand gegen Größe | ✅ Grad ≈ 3 konstant, n = 10 / 20 / 40 / 80 / 160 / 320: **10,7 / 20,1 / 45,0 / 90,4 / 177,6 / 375,8** Vorschläge – knapp über linear, weit unter dem O(n²)-Worst-Case. |

## Was nicht funktioniert hat / widerlegte Vorab-Hypothesen

- **Ein erster Port des Algorithmus lieferte ein falsches Ergebnis – gefangen erst durch eigene Nachrechnung, nicht durch den Bericht des bauenden Agenten.** Ein symmetrisches "wer hält wen"-Feld mit Rang-Vergleich je Bewerbung (naheliegend, analog zum zweiseitigen Gale-Shapley) bestand Hunderte Zufallstests, scheiterte aber am klassischen n=3-Lehrbuchbeispiel für Nichtexistenz (zyklische Vorlieben): es lieferte eine Paarung, die – von Hand nachgerechnet und per Brute-Force bestätigt – tatsächlich instabil war. Die Korrektur (Bewerbung immer beim eigenen Favoriten, bedingungslose, aber durch sofortige Kürzung abgesicherte Annahme) wurde an einer zweiten, unabhängigen Fehlerquelle für "no complete list required" nachgebessert: die erste Fassung der Fehlerbehandlung verwechselte "eine Liste war schon in Phase 1 harmlos leer" mit "eine Liste läuft gerade in Phase 2 leer" und erklärte dadurch jede ungerade oder dünn besetzte Karte fälschlich für unlösbar.
- **"Phase 1 leer = Phase 2 leer" wäre viel einfacher gewesen.** Nein: die Unterscheidung ist die konzeptionell wichtigste Stelle im ganzen Algorithmus – wer in Phase 1 von allen abgelehnt wird, bleibt beweisbar frei, ohne dass die restliche Karte davon betroffen ist; nur eine erst in Phase 2 (Rotationsbeseitigung) leerlaufende Liste beweist echte Unlösbarkeit.
- **Größere Reichweite sollte eine Lösung wahrscheinlicher machen.** Falsch: sie macht sie seltener (siehe Tabelle oben) – mehr Kandidaten heißt mehr Gelegenheit für einen Kreis in den Vorlieben, nicht weniger.
- **Mehrdeutigkeit sollte ähnlich häufig sein wie bei Gale-Shapley.** Nein: dort waren 34 % der Karten (Streuung ±20, n = 20) mehrdeutig, hier nur 3–13 % (n = 8 bis 16) – eine lösbare Karte ist im einseitigen Fall viel öfter lokal eindeutig.
- **Für "keine stabile Paarung existiert" bräuchte es eine eigene, künstlich konstruierte Karte.** Nicht nötig: die echte Fahrgemeinschaften-Geometrie (dieselbe wie `blossom-demo`) liefert das klassische n=3-Nichtexistenz-Muster direkt bei n = 4, Reichweite 20, Seed 18 (ein vierter, isolierter Mitbewohner nebenbei).
- **Ein PyPI-Referenzpaket (`matching`) hätte als alleiniges Orakel gereicht.** Verworfen: es verlangt vollständige Listen (unvereinbar mit unserem reichweitenbasierten Szenario) und hat zwei eigene, dokumentierte Fehler (liefert bei manchen unlösbaren Instanzen still eine instabile Teilpaarung statt "keine Lösung"). Primäres Orakel ist stattdessen ein eigener, unabhängiger Brute-Force-Prüfer; das Paket dient nur als sekundärer, klar kommentierter Smoke-Test.

## Was die Demo zeigt

- **Suche und Ablauf:** Schritt-Slider und ▶️ über die Ereignisse (Bewerbung, Annahme, Verdrängung, Kürzung, Rotation gefunden/beseitigt, harmlos unversorgt, Unlösbarkeit bewiesen): die Karte mit dem Status jeder Person (entschieden/offen/ausgeschlossen), das jeweils letzte Ereignis farbig hervorgehoben, die feststehende Paarung am letzten Schritt; daneben der Verlauf (wie viele Listen schon entschieden bzw. ausgeschlossen sind); am Ende entweder der **Beweis** (Gültigkeit, keine blockierende Paarung, Maximalität, tatsächlich mögliche Kanten) oder die konkrete Person, an der die Unlösbarkeit bewiesen wurde.
- **Wie gut?** Lösbarkeit, Paarzahl, unversorgte Personen, Rotationen, Aufwand; Vergleich naives Vorgehen gegen Irving (blockierende Paare); Verteilung über 100 feste Karten.
- **Wovon hängt es ab?** Reichweiten-Sweep, Streuung-Sweep, Aufwand gegen Größe (n = 10 bis 320), Eindeutigkeit gegen Größe (Brute-Force, n = 8 bis 16).
- **Feste Presets:** Kein stabiler Weg · Mehrere Rotationen · Nur Entfernung · Mittlere Karte · Große Reichweite · Zufällige Vorlieben · Ungerade Gruppe · Naives Vorgehen scheitert; **Wo die Annahmen enden.**

## Modell und Verfahren

- **Graph:** dieselbe Fahrgemeinschaften-Karte wie `blossom-demo`/`weighted-blossom-demo` (eine Gruppe, `SplitMix64`-Zufallsgenerator, Kante bei Fahrzeit ≤ Reichweite) – `sr_scenario.py` ist eine unveränderte Kopie. **Neu:** `sr_preferences.py` – drei Modelle (`dist`/`noise`/`random`), die Ziehung für "wie i über j denkt" ist an das **geordnete** Paar `(seed, i, j)` gekoppelt statt an einen Seitenbegriff – das macht `rank_i(j)` und `rank_j(i)` unabhängig voneinander und ist die Voraussetzung für zyklische Vorlieben.
- **Irvings Algorithmus (`sr_irving.py`):** Phase 1 – jeder bewirbt sich beim eigenen Favoriten, der bedingungslos annimmt (verdrängt den bisherigen Halt) und sofort alle schlechteren Einträge aus der eigenen Liste streicht; nur dadurch ist die bedingungslose Annahme korrekt. Eine dabei leerlaufende Liste ist harmlos. Phase 2 – Rotationen (Ketten sich gegenseitig blockierender zweiter Wahlen) werden gefunden und symmetrisch beseitigt (inklusive aller schlechteren Folgeeinträge, nicht nur der Rotation selbst – sonst bliebe nur ein Teilstück entfernt); läuft dabei eine vorher noch volle Liste leer, beweist das Nichtexistenz.
- **Zertifikat:** unabhängig von der Bewerbung – Gültigkeit, keine blockierende Paarung (Doppelschleife über alle Personenpaare), Maximalität, tatsächlich mögliche Kanten.
- **Aufwand:** Vorschläge, Kürzungen je Phase, Rotationen – nie Sekunden.

## Dateien

| Datei | Inhalt |
|---|---|
| `app.py` | Streamlit-Oberfläche |
| `sr_constants.py` | Regler-Grenzen, Presets und Hilfetexte, feste Seed-Mengen |
| `sr_presets.py` | Permalink-, Preset- und Zufalls-Seed-Logik (Standardmuster des Portfolios, ohne feste Kartenformen) |
| `sr_scenario.py` | Fahrgemeinschaften-Karte (aus `blossom-demo` unverändert übernommen) |
| `sr_preferences.py` | **Neu:** Vorlieben (nur Entfernung / Streuung / Zufall), einseitig |
| `sr_irving.py` | **Neu:** Irvings Algorithmus (zwei Phasen, Ereignisprotokoll mit Schnappschüssen, Zertifikat) |
| `sr_oracle.py` | **Neu:** Brute Force (eine stabile Paarung oder alle, für Tests) |
| `sr_evaluation.py` | Einordnung, Vergleich mit naivem Vorgehen, Verteilung, Sweeps, Aufwand, Eindeutigkeit |
| `sr_visualization.py` | Plotly-Abbildungen (Achsen gesperrt, keine Legende auf der Karte) |
| `tests/` | Algorithmus (Kreuzprüfung gegen Brute Force auf 1000+ Instanzen inkl. unvollständiger Listen, Lehrbuchbeispiele, Negativkontrollen für die beim Portieren gefundenen Fehlerklassen, sekundärer Smoke-Test gegen das Paket `matching`), Auswertung, Presets, belegte Zahlen, AppTest-Rauchtests |

Die kopierten Bausteine werden durch Tests bewacht (Zufallsgenerator-Vektor, eine festgeschriebene Punktliste). Alle Daten sind synthetisch; die Laufzeit braucht nur numpy, pandas, plotly und streamlit (das Paket `matching` ist reines Testorakel, nie zur Laufzeit importiert).

## Lokal starten

```bash
python -m venv venv
venv\Scripts\pip install -r requirements.txt
venv\Scripts\streamlit run app.py
```

## Tests ausführen

```bash
venv\Scripts\pip install -r requirements-dev.txt
venv\Scripts\python -m pytest tests -v
```

Die Logik rechnet ausschließlich mit ganzen Zahlen; die im Text genannten Anteile und Mittelwerte sind deshalb auf jeder Plattform identisch.
Die CI (`.github/workflows/tests.yml`) läuft auf Ubuntu mit Python 3.12, bei jedem Push und wöchentlich mit den jeweils neuesten Bibliotheksversionen.
