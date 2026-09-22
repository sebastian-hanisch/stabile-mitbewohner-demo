"""Vorlieben: eine einzige Gruppe von Mitbewohnern, jeder ordnet seine erreichbaren Nachbarn (die Reichweite macht die Listen
unvollständig, aber symmetrisch: j in adj[i] genau dann, wenn i in adj[j]).

Anders als in den zweiseitigen Vorgängerdemos gibt es hier **keine Seiten**. Drei Modelle, alle ganzzahlig und über einen
eigenen Zufallsgenerator (SplitMix64) statt numpy:
- `dist`: jeder ordnet nach der Fahrzeit c_ij. Alle haben dieselbe Wertung ⇒ die stabile Paarung ist eindeutig und gleich
  dem Greedy "Billigste Kante zuerst".
- `noise`: jeder schätzt die Fahrzeit selbst (Ortskenntnis, Sympathie): c_ij + Streuung in [-k, k] Minuten. k = 0 ist
  `dist`, große k nähern sich `random`.
- `random`: unabhängige Zufallsvorlieben, ohne Bezug zu den Kosten.

Tragend für das Problem: die Ziehung für "wie i über j denkt" hängt vom GEORDNETEN Paar (seed, i, j) ab, nicht von einem
ungeordneten Paar und nicht von einem Seitenbegriff (den es hier nicht gibt). Dadurch sind rank_i(j) und rank_j(i) völlig
unabhängig voneinander - genau das erlaubt zyklische Vorlieben (A vor B, B vor C, C vor A) und damit überhaupt erst die
Möglichkeit, dass keine stabile Paarung existiert. Wären beide Meinungen aneinander gekoppelt, würde das Problem
entarten (es verhielte sich dann eher wie der zweiseitige Fall). Gleichstände werden nach dem Index gebrochen, die Listen
sind also strikt.
"""

from sr_scenario import SplitMix64

MASK = (1 << 64) - 1
PREF_LABELS = {"dist": "Nur Entfernung", "noise": "Entfernung mit Streuung", "random": "Zufall"}
DEFAULT_PREF = "noise"
NOISE_MIN, NOISE_MAX, NOISE_STEP, DEFAULT_NOISE = 5, 60, 5, 20


def _draw(seed, i, j, bits):
    """Reproduzierbare Ziehung 0 .. 2^bits - 1 für das GEORDNETE Paar (i, j): unabhängig von n und Reichweite.
    Kein Seitenbegriff - (i, j) und (j, i) ziehen unabhängig voneinander, das ist hier der ganze Punkt."""
    state = seed & MASK
    for part in (i, j):
        state = (state * 1000003 + part + 1) & MASK
    return SplitMix64(state).below(1 << bits)


def _noise(seed, i, j, k):
    return ((2 * k + 1) * _draw(seed, i, j, 20) >> 20) - k


def preferences(sc, model, noise=DEFAULT_NOISE, seed=0):
    """Strikte Vorlieben: prefs[i] = erreichbare Nachbarn von i (sc.adj[i]), beste zuerst. Ganzzahlig, reproduzierbar."""
    n, c = sc.n, sc.cost
    if model == "dist":
        key = lambda i, j: int(c[i, j])
    elif model == "noise":
        key = lambda i, j: int(c[i, j]) + _noise(seed, i, j, noise)
    elif model == "random":
        key = lambda i, j: _draw(seed, i, j, 30)
    else:
        raise ValueError(model)
    return [sorted(sc.adj[i], key=lambda j: (key(i, j), j)) for i in range(n)]


def ranks(prefs):
    """Rangtabellen: ranks[a][b] = Platz von b in der (ursprünglichen) Liste von a (0 = beste)."""
    return [{x: k for k, x in enumerate(lst)} for lst in prefs]
