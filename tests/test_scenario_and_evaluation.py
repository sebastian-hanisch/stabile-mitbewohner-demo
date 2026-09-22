"""Kopierwächter (`sr_scenario.py` = `bl_scenario.py` unverändert), Vorlieben-Grundeigenschaften und die Plumbing der
Auswertung (Verdict, Vergleichstabelle, Verteilung, Sweeps, Skalierung, Eindeutigkeit)."""

import pytest

import sr_constants as C
import sr_evaluation as ev
import sr_irving as I
import sr_preferences as P
import sr_scenario as S


def test_splitmix_vector_and_a_pinned_point_list():
    """Wächter gegen stille Abweichungen beim Kopieren aus `blossom-demo`."""
    rng = S.SplitMix64(0)
    assert [rng.next() for _ in range(2)] == [0xE220A8397B1DCDAF, 0x6E789E6AA1B965F4]
    sc = S.generate(30, 20, 0, 100000)
    assert sc.pts[:3] == ((8, 69), (86, 39), (66, 62)) and sc.m == 46


def test_preferences_are_strict_and_restricted_to_reachable_neighbours():
    sc = S.generate(15, 25, 0, 3)
    for model in ("dist", "noise", "random"):
        prefs = P.preferences(sc, model, seed=3)
        for i in range(sc.n):
            assert sorted(prefs[i]) == sorted(sc.adj[i])                   # exakt die erreichbaren Nachbarn, nicht mehr/weniger
            assert len(set(prefs[i])) == len(prefs[i])                     # keine Duplikate


def test_ordered_pair_independence_is_what_makes_cycles_possible():
    """rank_i(j) und rank_j(i) sind bei `noise`/`random` UNABHAENGIG voneinander (kein Seitenbegriff) - im Gegensatz zu
    `dist`, wo beide dieselbe (symmetrische) Fahrzeit ordnen."""
    sc = S.generate(10, 40, 0, 7)
    prefs_dist = P.preferences(sc, "dist", seed=7)
    prefs_noise = P.preferences(sc, "noise", noise=30, seed=7)
    differs = False
    for i in range(sc.n):
        for j in sc.adj[i]:
            if prefs_dist[i].index(j) != prefs_noise[i].index(j):
                differs = True
    assert differs


def test_analyse_and_verdict_solvable():
    sc = S.generate(20, 20, 0, 20)
    a = ev.analyse(sc, "noise", 20, 20)
    level, code, data = ev.verdict(a)
    assert code == ev.SOLVED and level == "success"
    assert data["solvable"] is True and data["count"] > 0
    assert data["cert_ok"] is True


def test_analyse_and_verdict_unsolvable():
    sc = S.generate(4, 20, 0, 18)
    a = ev.analyse(sc, "noise", 20, 18)
    level, code, data = ev.verdict(a)
    assert code == ev.UNSOLVABLE and level == "error"
    assert data["solvable"] is False and data["unsolvable_agent"] != -1


def test_analyse_and_verdict_none():
    sc = S.generate(C.N_MIN, C.REACH_MIN, 0, next(k for k in range(500) if S.generate(C.N_MIN, C.REACH_MIN, 0, k).m == 0))
    a = ev.analyse(sc, "noise", 20, 0)
    level, code, data = ev.verdict(a)
    assert code == ev.NONE and level == "info"


def test_compare_table_naive_never_beats_stable_on_blocking():
    for seed in range(30):
        sc = S.generate(15, 25, 0, seed)
        a = ev.analyse(sc, "noise", 20, seed)
        if not a.result.solvable:
            continue
        rows = ev.compare_table(a)
        naive_row, stable_row = rows
        assert stable_row["blocking"] == 0                                 # Irvings Ergebnis ist per Definition blockierungsfrei
        assert naive_row["blocking"] >= 0


def test_distribution_and_sweeps_shapes():
    d = ev.distribution(12, 25, 0, "noise", 20, seeds=range(20))
    assert d["n_valid"] == 20 and 0.0 <= d["solvable_share"] <= 1.0
    rs = ev.reach_sweep(12, 0, seeds=range(10), reaches=(15, 25))
    assert len(rs) == 2 and all("solvable_share" in r for r in rs)
    ns = ev.noise_sweep(12, 25, 0, seeds=range(10), ks=(0, 20))
    assert len(ns) == 2


def test_scale_table_and_uniqueness_repeatable():
    a1, a2 = ev.scale_table(), ev.scale_table()
    assert a1 == a2                                                        # lru_cache: dieselbe Anfrage liefert dasselbe Tupel
    u1 = ev.uniqueness(ns=(6, 8), seeds=tuple(range(10)))
    assert all(r["max_count"] >= 1 for r in u1 if r["n_solvable"])


def test_naive_pairing_is_a_valid_matching():
    sc = S.generate(20, 20, 0, 5)
    prefs = P.preferences(sc, "noise", 20, 5)
    pairs = ev.naive_pairing(prefs)
    seen = set()
    for i, j in pairs:
        assert i not in seen and j not in seen
        assert j in prefs[i] and i in prefs[j]
        seen.add(i)
        seen.add(j)
