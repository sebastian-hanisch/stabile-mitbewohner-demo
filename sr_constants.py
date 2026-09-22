"""Konstanten, Regler-Grenzen, Presets und feste Seed-Mengen der Demo "Stabile Mitbewohner".

Anders als in `blossom-demo`/`weighted-blossom-demo` gibt es hier KEINE festen, von Hand gezeichneten Kartenformen
(kein `net_select`): jede der acht Presets unten ist ein konkretes, gesuchtes (n, Reichweite, Vorliebenmodell, Streuung,
Seed) - das genuegt vollstaendig, um jedes gewuenschte Phaenomen (Nichtexistenz, mehrere Rotationen, ...) zu zeigen, und
eine eigene Graphform bringt hier keinen zusaetzlichen Lehrwert (anders als bei Blossom, wo die Form selbst - Dreieck,
verschachtelte Bluete, Windmuehle - der Punkt war)."""

from sr_preferences import DEFAULT_NOISE, DEFAULT_PREF, NOISE_MAX, NOISE_MIN, NOISE_STEP, PREF_LABELS  # noqa: F401 (Wiederverwendung, keine Dopplung)

N_MIN, N_MAX, DEFAULT_N = 4, 40, 20          # Mitbewohner
REACH_MIN, REACH_MAX, DEFAULT_REACH = 10, 150, 20   # Reichweite in Minuten
BALLUNG_MIN, BALLUNG_MAX, DEFAULT_BALLUNG = 0, 100, 0   # ganze Prozent, Schritt 25
DEFAULT_SEED = 20
SEED_MAX = 2_000_000_000

# --- feste Seed-Mengen (wie in den Vorgängerdemos; unabhängig vom Nutzer-Seed) --------------------------------------
DIST_SEEDS = tuple(range(100000, 100100))
SWEEP_SEEDS = DIST_SEEDS[:40]
SCALE_NS = (10, 20, 40, 80, 160, 320)
SCALE_SEEDS = DIST_SEEDS[:10]
SCALE_DEGREE_AREA = 12000                   # reach = isqrt(SCALE_DEGREE_AREA // n): mittlerer Grad bleibt ungefähr konstant
REACH_SWEEP = (10, 15, 20, 25, 30, 40, 60, 100)
NOISE_SWEEP = (0, 2, 5, 10, 20, 30, 45, 60)
UNIQUE_MAX_N = 16                           # Brute-Force-Grenze für die Eindeutigkeitsmessung (eigene, kleinere Karten)
UNIQUE_NS = (8, 10, 12, 14, 16)
UNIQUE_SEEDS = tuple(range(40))

COLORS = {"matched": "#1f77b4", "even": "#2ca02c", "propose": "#2ca02c", "displace": "#d62728", "trim": "#c8c8c8",
          "free": "#c8c8c8", "rotation": "#9467bd", "naive": "#8c564b", "stable": "#1f77b4"}

# --- Presets --------------------------------------------------------------------------------------------------------
_BASE = dict(pref=DEFAULT_PREF, noise=DEFAULT_NOISE, n=DEFAULT_N, reach=DEFAULT_REACH, ballung=DEFAULT_BALLUNG, seed=DEFAULT_SEED)
PRESETS = {
    "🔁 Kein stabiler Weg": {**_BASE, "n": 4, "reach": 20, "seed": 18},
    "🧩 Mehrere Rotationen": {**_BASE, "pref": "random", "n": 10, "reach": 60, "seed": 365},
    "📏 Nur Entfernung": {**_BASE, "pref": "dist"},
    "🗺️ Mittlere Karte": {**_BASE},
    "📉 Große Reichweite": {**_BASE, "reach": 100, "seed": 8},
    "🎲 Zufällige Vorlieben": {**_BASE, "pref": "random", "seed": 8},
    "➗ Ungerade Gruppe": {**_BASE, "n": 21, "seed": 0},
    "⚠️ Naives Vorgehen scheitert": {**_BASE, "seed": 7},
}
# Jede Zahl in diesen Texten ist in tests/test_claims.py und tests/test_presets.py belegt
PRESET_HELP = {
    "🔁 Kein stabiler Weg": "Vier Mitbewohner (einer davon isoliert, unerreichbar): die restlichen drei bilden eine einzige Rotation - und die beseitigt den ganzen Rest, am Ende hat jede Liste 0 Eintraege. Ein Brute-Force-Beweis (alle 3 moeglichen Einzelpaarungen unter den dreien haben ein blockierendes Paar) bestaetigt es unabhaengig. Anders als bei Gale-Shapley (dort gibt es IMMER eine stabile Paarung) ist das hier keine Ausnahme, sondern der Kern der Verallgemeinerung.",
    "🧩 Mehrere Rotationen": "Zehn Mitbewohner, Zufallsvorlieben: 4 Rotationen hintereinander, bevor die Paarung {(0,2),(1,6),(3,5),(4,8),(7,9)} feststeht - und genau diese Karte hat, unabhaengig geprueft per Brute Force, exakt 4 verschiedene stabile Paarungen insgesamt.",
    "📏 Nur Entfernung": "Wenn alle nach derselben Fahrzeit ordnen, ist die stabile Paarung immer eindeutig und exakt gleich der billigsten-Kante-zuerst-Paarung - auf allen 60 getesteten Karten (n = 20) keine einzige Rotation. Genau wie im zweiseitigen Fall (`gale-shapley-demo`) macht erst eigenstaendige Einschaetzung (Streuung oder Zufall) die Vorlieben zyklisch genug fuer Rotationen oder Nichtexistenz.",
    "🗺️ Mittlere Karte": "20 Mitbewohner, Reichweite 20: 7 Paare, 6 bleiben schon in Phase 1 unversorgt (harmlos, keine Rotation noetig). Auf den 100 festen Karten ist eine solche Karte zu 61 % ueberhaupt loesbar (Median 7 Paare).",
    "📉 Große Reichweite": "Dieselbe Vorlieben-Ziehung wie eine Karte mit Reichweite 20 (dort waere sie mit 8 Paaren loesbar) - bei Reichweite 100 dagegen unloesbar: mehr erreichbare Kandidaten bedeuten mehr Gelegenheit fuer einen Kreis, nicht weniger. Genau dieser Trend zeigt sich auf den 100 festen Karten: die Loesbarkeit sinkt von 92,5 % (Reichweite 10) auf 70 % (Reichweite 20).",
    "🎲 Zufällige Vorlieben": "Ohne jeden Bezug zu Fahrzeiten: 2 Rotationen hintereinander, am Ende trotzdem keine stabile Paarung - reiner Zufall macht Kreise nicht seltener als geschaetzte Fahrzeiten mit Streuung.",
    "➗ Ungerade Gruppe": "21 Mitbewohner (ungerade): 9 Paare, 3 bleiben garantiert frei - schon rein rechnerisch kann nie jeder gepaart werden, aber das ist harmlos, keine Unloesbarkeit.",
    "⚠️ Naives Vorgehen scheitert": "Wer einfach der Reihe nach den besten noch freien Nachbarn nimmt, endet hier mit 6 blockierenden Paaren; Irvings Verfahren findet auf derselben Karte 8 Paare ganz ohne ein einziges.",
}
