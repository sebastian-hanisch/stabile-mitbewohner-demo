"""Unabhängiges Orakel zu Irvings Algorithmus: ALLE Paarungen (auch unvollständige) werden ohne jedes Pruning aufgezählt und einzeln auf
blockierende Paare geprüft (anderer Rechenweg als `sr_oracle.py`, das während des Aufbaus abschneidet). Verglichen werden Existenz, die
gelieferte Paarung, die Menge der unversorgten Personen (in allen stabilen Paarungen gleich) und das Zertifikat.

Dazu eine Invariante der angezeigten Kennzahlen: auf lösbaren Karten ist die Zahl der in Phase 1 harmlos Unversorgten genau n - 2 * Paare
(die frühere Verteilung mittelte sie über ALLE Karten, auch unlösbare, und passte so nicht zur Paarzahl daneben)."""

import random

import sr_constants as C
from sr_evaluation import distribution
from sr_irving import certificate, solve


def _all_matchings(adj):
    n, out = len(adj), []

    def rec(i, used, cur):
        if i == n:
            out.append(tuple(cur))
        elif i in used:
            rec(i + 1, used, cur)
        else:
            rec(i + 1, used, cur)
            for j in adj[i]:
                if j > i and j not in used:
                    rec(i + 1, used | {i, j}, cur + [(i, j)])
    rec(0, frozenset(), [])
    return out


def _stable(prefs, matching):
    partner = {}
    for a, b in matching:
        partner[a], partner[b] = b, a
    for a, lst in enumerate(prefs):
        for b in lst:
            pa, pb = partner.get(a), partner.get(b)
            if pa == b:
                continue
            if (pa is None or lst.index(b) < lst.index(pa)) and (pb is None or prefs[b].index(a) < prefs[b].index(pb)):
                return False
    return True


def _random_prefs(rng, n):
    p = rng.choice([0.4, 0.7, 1.0])
    adj = [[] for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            if rng.random() < p:
                adj[i].append(j)
                adj[j].append(i)
    for lst in adj:
        rng.shuffle(lst)
    return adj


def test_irving_agrees_with_full_enumeration_on_random_small_instances():
    rng = random.Random(2026)
    solvable = unsolvable = 0
    for _ in range(250):
        prefs = _random_prefs(rng, rng.randint(0, 7))
        stable = [m for m in _all_matchings(prefs) if _stable(prefs, m)]
        res = solve(prefs, record=False)
        assert res.solvable == bool(stable), prefs
        if not stable:
            unsolvable += 1
            assert res.pairs == () and res.unsolvable_agent >= 0
            continue
        solvable += 1
        assert res.pairs in {tuple(sorted(m)) for m in stable}, prefs
        free_sets = {frozenset(range(len(prefs))) - {x for p in m for x in p} for m in stable}
        assert len(free_sets) == 1                                         # Satz: dieselben Personen bleiben in jeder stabilen Paarung frei
        assert set(res.phase1_unmatched) <= next(iter(free_sets))
        assert certificate(prefs, res.pairs, len(prefs))["all_ok"]
    assert solvable > 100 and unsolvable > 10


def test_phase1_unmatched_statistic_is_consistent_with_the_pair_count():
    d = distribution(20, 20, 0, "noise", 20, C.SWEEP_SEEDS)
    assert abs(d["phase1_unmatched"]["mean"] - (20 - 2 * d["count"]["mean"])) < 1e-9
