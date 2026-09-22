"""Auswertung: eine Karte (`analyse`, `verdict`, `compare_table`), viele Karten (`distribution`: Loesbarkeit, Aufwand,
Preis des Ignorierens), Rauschen-/Reichweiten-Sweep, Aufwand gegen Groesse, Eindeutigkeit (kleine n, Brute-Force).
Alles ganzzahlig und deterministisch; nur die Anzeige-Statistiken (Anteile, Mittel, Mediane) sind Gleitkomma.

Anders als bei Gale-Shapley gibt es hier kein "Preis der Stabilitaet" (Kosten gegen das Optimum): `random`/`noise`-
Vorlieben haben keinen zugrunde liegenden Kostenwert, auf den sich eine Prozent-Praemie beziehen liesse. Der Vergleich
ist stattdessen RANGBASIERT: naives Vorgehen (der Reihe nach den besten noch freien Nachbarn nehmen) gegen Irvings
bewiesen stabiles Ergebnis, gemessen in blockierenden Paaren und im erreichten Rang.
"""

from dataclasses import dataclass
from functools import lru_cache

import numpy as np

import sr_constants as C
from sr_irving import certificate, solve
from sr_oracle import all_stable_roommates_matchings
from sr_preferences import DEFAULT_NOISE, preferences
from sr_scenario import generate

SOLVED, UNSOLVABLE, NONE = "solved", "unsolvable", "none"


def naive_pairing(prefs):
    """Der Reihe nach (aufsteigender Index): wer noch frei ist, nimmt seinen besten noch freien erreichbaren Nachbarn -
    KEINE Stabilitaetspruefung, reiner Vergleichsmassstab."""
    n = len(prefs)
    free = set(range(n))
    pairs = []
    for i in range(n):
        if i not in free:
            continue
        for j in prefs[i]:
            if j in free:
                free.discard(i)
                free.discard(j)
                pairs.append((min(i, j), max(i, j)))
                break
    return tuple(sorted(pairs))


def blocking_pairs(prefs, pairs):
    """Unabhaengige Doppelschleife (nicht aus `sr_irving.certificate` wiederverwendet): alle blockierenden Paare."""
    rnk = [{x: k for k, x in enumerate(p)} for p in prefs]
    matched = {}
    for i, j in pairs:
        matched[i] = j
        matched[j] = i
    n = len(prefs)
    out = []
    for a in range(n):
        for b in range(a + 1, n):
            if b not in rnk[a] or matched.get(a) == b:
                continue
            pa, pb = matched.get(a), matched.get(b)
            a_pref = pa is None or rnk[a][b] < rnk[a][pa]
            b_pref = pb is None or rnk[b][a] < rnk[b][pb]
            if a_pref and b_pref:
                out.append((a, b))
    return out


def _mean_rank(pairs, rnk):
    if not pairs:
        return 0.0, 0
    vals = []
    for i, j in pairs:
        vals.append(rnk[i][j])
        vals.append(rnk[j][i])
    return sum(vals), len(vals)


@dataclass
class Analysis:
    scenario: object
    pref: str
    noise: int
    seed: int
    n: int
    prefs: list
    result: object          # sr_irving.Result
    cert: dict
    naive: tuple             # Paarung des naiven Vorgehens


def analyse(sc, pref=C.DEFAULT_PREF, noise=DEFAULT_NOISE, seed=0):
    prefs = preferences(sc, pref, noise, seed)
    res = solve(prefs, record=True)
    cert = certificate(prefs, res.pairs, res.n) if res.solvable else None
    return Analysis(sc, pref, noise, seed, sc.n, prefs, res, cert, naive_pairing(prefs))


def verdict(a):
    """(Stufe, Code, Zahlen) fuer die Anzeige; `Zahlen` enthaelt jede Zahl, die der Text nennt."""
    sc, r = a.scenario, a.result
    feasible = any(sc.adj[i] for i in range(sc.n))
    if not feasible:
        code = NONE
    elif not r.solvable:
        code = UNSOLVABLE
    else:
        code = SOLVED
    naive_blocking = blocking_pairs(a.prefs, a.naive)
    data = {"n": sc.n, "solvable": r.solvable, "count": len(r.pairs),
            "phase1_unmatched": len(r.phase1_unmatched), "unsolvable_agent": r.unsolvable_agent,
            "proposals": r.proposals, "rejections1": r.rejections1, "rejections2": r.rejections2, "rotations": r.rotations,
            "cert_ok": a.cert["all_ok"] if a.cert else None, "naive_count": len(a.naive), "naive_blocking": len(naive_blocking),
            "isolated": sum(1 for i in range(sc.n) if not sc.adj[i])}
    level = {NONE: "info", SOLVED: "success", UNSOLVABLE: "error"}[code]
    return level, code, data


def compare_table(a):
    r = a.result
    naive_blocking = blocking_pairs(a.prefs, a.naive)
    stable_blocking = blocking_pairs(a.prefs, r.pairs) if r.solvable else []
    return [
        {"label": "Naives Vorgehen (bester freier Nachbar)", "count": len(a.naive), "blocking": len(naive_blocking)},
        {"label": "Irvings Algorithmus (bewiesen stabil)", "count": len(r.pairs) if r.solvable else 0, "blocking": len(stable_blocking) if r.solvable else None},
    ]


# --- viele Karten -----------------------------------------------------------------------------------------------

def _row(sc, pref, noise, seed):
    prefs = preferences(sc, pref, noise, seed)
    res = solve(prefs, record=False)
    rnk = [{x: k for k, x in enumerate(p)} for p in prefs]
    naive = naive_pairing(prefs)
    naive_block = blocking_pairs(prefs, naive)
    row = {"solvable": res.solvable, "n": sc.n, "degree": sum(len(a) for a in sc.adj) / max(sc.n, 1),
           "proposals": res.proposals, "rejections1": res.rejections1, "rejections2": res.rejections2, "rotations": res.rotations,
           "phase1_unmatched": len(res.phase1_unmatched), "naive_count": len(naive), "naive_blocking": len(naive_block)}
    if res.solvable:
        rank_sum, rank_n = _mean_rank(res.pairs, rnk)
        naive_rank_sum, naive_rank_n = _mean_rank(naive, rnk)
        row.update({"count": len(res.pairs), "rank_sum": rank_sum, "rank_n": rank_n,
                    "naive_rank_sum": naive_rank_sum, "naive_rank_n": naive_rank_n, "same_count": len(naive) == len(res.pairs)})
    return row


@lru_cache(maxsize=256)
def cell_rows(n, reach, ballung, pref, noise, seeds):
    return tuple(_row(generate(n, reach, ballung, sd), pref, noise, sd) for sd in seeds)


def _mean(v):
    return float(np.mean(v)) if len(v) else None


def _med(v):
    return float(np.median(v)) if len(v) else None


def _stat(values):
    return {"mean": _mean(values), "median": _med(values), "min": min(values) if len(values) else None, "max": max(values) if len(values) else None}


def distribution(n, reach, ballung, pref=C.DEFAULT_PREF, noise=DEFAULT_NOISE, seeds=C.DIST_SEEDS):
    """Verteilung ueber viele Karten: Loesbarkeit, Paarzahl, unversorgte Personen, Aufwand, Vergleich mit naivem Vorgehen."""
    rows = list(cell_rows(n, reach, ballung, pref, noise, tuple(seeds)))
    n_valid = len(rows)
    solved = [r for r in rows if r["solvable"]]
    return {
        "n_seeds": len(seeds), "n_valid": n_valid,
        "solvable_share": _mean([r["solvable"] for r in rows]),
        "count": _stat([r["count"] for r in solved]),
        "phase1_unmatched": _stat([r["phase1_unmatched"] for r in rows]),
        "rotations": _stat([r["rotations"] for r in rows]), "rotations_share_gt0": _mean([r["rotations"] > 0 for r in rows]),
        "proposals": _stat([r["proposals"] for r in rows]),
        "naive_blocking": _stat([r["naive_blocking"] for r in solved]), "naive_blocking_share_gt0": _mean([r["naive_blocking"] > 0 for r in solved]),
        "same_count_share": _mean([r["same_count"] for r in solved]),
        "rank_stable_mean": (sum(r["rank_sum"] for r in solved) / max(sum(r["rank_n"] for r in solved), 1)) if solved else None,
        "rank_naive_mean": (sum(r["naive_rank_sum"] for r in solved) / max(sum(r["naive_rank_n"] for r in solved), 1)) if solved else None,
        "degree": _mean([r["degree"] for r in rows]),
    }


def reach_sweep(n, ballung=0, seeds=C.SWEEP_SEEDS, reaches=C.REACH_SWEEP):
    out = []
    for r in reaches:
        d = distribution(n, r, ballung, seeds=seeds)
        if d["n_valid"] == 0:
            continue
        out.append({"reach": r, "degree": d["degree"], "solvable_share": d["solvable_share"], "rotations_share_gt0": d["rotations_share_gt0"]})
    return out


def noise_sweep(n, reach, ballung=0, seeds=C.SWEEP_SEEDS, ks=C.NOISE_SWEEP):
    out = []
    for k in ks:
        d = distribution(n, reach, ballung, "dist" if k == 0 else "noise", max(k, 1), seeds)
        if d["n_valid"] == 0:
            continue
        out.append({"k": k, "solvable_share": d["solvable_share"], "rotations_share_gt0": d["rotations_share_gt0"]})
    return out


@lru_cache(maxsize=8)
def scale_table(ns=C.SCALE_NS, seeds=C.SCALE_SEEDS):
    """Aufwand (Vorschlaege) gegen Groesse, Reichweite so, dass der mittlere Grad etwa gleich bleibt."""
    import math
    out = []
    for n in ns:
        reach = max(3, math.isqrt(C.SCALE_DEGREE_AREA // n))
        props, deg = [], []
        for sd in seeds:
            sc = generate(n, reach, 0, sd)
            prefs = preferences(sc, "noise", DEFAULT_NOISE, sd)
            res = solve(prefs, record=False)
            props.append(res.proposals)
            deg.append(sum(len(a) for a in sc.adj) / n)
        out.append({"n": n, "reach": reach, "proposals": _mean(props), "degree": _mean(deg)})
    return out


@lru_cache(maxsize=8)
def uniqueness(ns=C.UNIQUE_NS, seeds=C.UNIQUE_SEEDS, reach=40):
    """Anzahl stabiler Paarungen (Brute Force, nur kleine n): Anteil loesbarer Karten mit genau 1 / mehr als 1 Loesung."""
    out = []
    for n in ns:
        counts = []
        for sd in seeds:
            sc = generate(n, reach, 0, sd)
            prefs = preferences(sc, "noise", DEFAULT_NOISE, sd)
            all_m = all_stable_roommates_matchings(prefs, max_n=C.UNIQUE_MAX_N)
            counts.append(len(all_m))
        solved = [c for c in counts if c > 0]
        out.append({"n": n, "n_seeds": len(seeds), "n_solvable": len(solved),
                    "unique_share": _mean([c == 1 for c in solved]) if solved else None,
                    "multi_share": _mean([c > 1 for c in solved]) if solved else None,
                    "max_count": max(counts) if counts else 0})
    return out


def scenario_from_settings(n, reach, ballung, seed):
    return generate(n, reach, ballung, seed)
