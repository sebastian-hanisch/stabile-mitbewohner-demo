"""Jede Zahl in den Hilfetexten, Presets, Tabellen und Grenzen der App und der README ist hier über die 100 festen
Karten (DIST_SEEDS) bzw. die festen Sweep-/Skalierungs-Seedmengen belegt. Alles rechnet mit ganzen Zahlen und einem
eigenen Zufallsgenerator - die Werte sind auf jeder Plattform dieselben; die Toleranzen decken nur die Rundung auf die
im Text genannten Stellen."""

import pytest

import sr_evaluation as ev


def near(value, expected, tol):
    assert abs(value - expected) <= tol, f"{value:.4f} statt {expected}"


@pytest.fixture(scope="module")
def dist():
    return ev.distribution(20, 20, 0, "noise", 20)


def test_default_map_family(dist):
    d = dist
    near(d["degree"], 1.916, 0.001)
    near(d["solvable_share"], 0.61, 0.005)
    near(d["count"]["mean"], 7.2131, 0.005)
    assert d["count"]["median"] == 7.0 and (d["count"]["min"], d["count"]["max"]) == (5, 9)
    near(d["phase1_unmatched"]["mean"], 5.36, 0.005)
    assert d["phase1_unmatched"]["median"] == 5.5 and (d["phase1_unmatched"]["min"], d["phase1_unmatched"]["max"]) == (2, 10)


def test_rotations_and_effort(dist):
    d = dist
    near(d["rotations"]["mean"], 0.43, 0.005)
    assert d["rotations"]["median"] == 0.0 and (d["rotations"]["min"], d["rotations"]["max"]) == (0, 2)
    near(d["rotations_share_gt0"], 0.41, 0.005)
    near(d["proposals"]["mean"], 18.16, 0.05)
    assert d["proposals"]["median"] == 18.0 and (d["proposals"]["min"], d["proposals"]["max"]) == (11, 24)


def test_naive_vs_stable(dist):
    d = dist
    near(d["naive_blocking"]["mean"], 2.082, 0.005)
    assert d["naive_blocking"]["median"] == 2.0 and (d["naive_blocking"]["min"], d["naive_blocking"]["max"]) == (0, 5)
    near(d["naive_blocking_share_gt0"], 0.8689, 0.005)
    near(d["same_count_share"], 0.7213, 0.005)
    near(d["rank_stable_mean"], 0.2193, 0.005)
    near(d["rank_naive_mean"], 0.3764, 0.005)
    assert d["rank_stable_mean"] < d["rank_naive_mean"]                    # stabil erreicht durchgehend einen besseren Rang


def test_dist_model_always_matches_cheapest_edge_first_greedy():
    """`dist`-Vorlieben: die stabile Paarung ist immer eindeutig und gleich der billigsten-Kante-zuerst-Paarung,
    keine einzige Rotation - auf 60 getesteten Karten (n=20, Reichweite 20)."""
    import sr_scenario as S
    from sr_irving import solve
    from sr_preferences import preferences

    def cheapest_edge_first(sc):
        edges = sorted((int(sc.cost[i, j]), i, j) for i in range(sc.n) for j in sc.adj[i] if i < j)
        free = set(range(sc.n))
        pairs = []
        for _c, i, j in edges:
            if i in free and j in free:
                free.discard(i)
                free.discard(j)
                pairs.append((i, j))
        return tuple(sorted(pairs))

    matches, total_rotations = 0, 0
    for seed in range(60):
        sc = S.generate(20, 20, 0, seed)
        res = solve(preferences(sc, "dist", seed=seed), record=False)
        total_rotations += res.rotations
        if res.solvable and res.pairs == cheapest_edge_first(sc):
            matches += 1
    assert matches == 60 and total_rotations == 0


def test_noise_sweep_smooth_transition():
    rows = {r["k"]: r for r in ev.noise_sweep(20, 20, 0)}
    expect = {0: 1.0, 2: 1.0, 5: 0.95, 10: 0.75, 20: 0.7, 30: 0.7, 45: 0.675, 60: 0.675}
    for k, share in expect.items():
        near(rows[k]["solvable_share"], share, 0.005)
    shares = [rows[k]["solvable_share"] for k in (0, 2, 5, 10, 20, 30, 45, 60)]
    assert shares == sorted(shares, reverse=True)                          # streng fallend: mehr Streuung, seltener lösbar


def test_reach_sweep_solvability_falls_reach_20_and_100():
    """Reichweite senkt die Lösbarkeit, statt sie zu erhöhen - der gegenintuitive Kernbefund dieses Stücks."""
    rows = {r["reach"]: r for r in ev.reach_sweep(20, 0)}
    expect = {10: (0.505, 0.925), 15: (1.085, 0.9), 20: (1.9575, 0.7), 25: (2.895, 0.65), 30: (3.9475, 0.625), 40: (6.48, 0.6), 60: (11.4425, 0.575), 100: (18.43, 0.575)}
    for reach, (deg, share) in expect.items():
        near(rows[reach]["degree"], deg, 0.001)
        near(rows[reach]["solvable_share"], share, 0.005)
    shares = [rows[r]["solvable_share"] for r in (10, 15, 20, 25, 30, 40, 60, 100)]
    assert shares == sorted(shares, reverse=True)                          # streng fallend ueber den ganzen Sweep


def test_effort_against_size():
    rows = {r["n"]: r for r in ev.scale_table()}
    assert [rows[n]["reach"] for n in (10, 20, 40, 80, 160, 320)] == [34, 24, 17, 12, 8, 6]
    expect = {10: 10.7, 20: 20.1, 40: 45.0, 80: 90.4, 160: 177.6, 320: 375.8}
    for n, proposals in expect.items():
        near(rows[n]["proposals"], proposals, 0.5)
    assert all(2.5 < rows[n]["degree"] < 3.5 for n in rows)


def test_uniqueness_rare_multiplicity():
    """Anders als im zweiseitigen Fall (Gale-Shapley: 34 % mehrdeutig bei Streuung ±20) ist eine loesbare Karte hier
    meist eindeutig - Mehrdeutigkeit ist selten und (in diesem Messbereich) immer genau 2 Loesungen."""
    rows = {r["n"]: r for r in ev.uniqueness()}
    expect = {8: (37, 0.9730), 10: (33, 0.9697), 12: (29, 0.8966), 14: (24, 0.8750), 16: (26, 0.9231)}
    for n, (n_solvable, unique_share) in expect.items():
        assert rows[n]["n_solvable"] == n_solvable
        near(rows[n]["unique_share"], unique_share, 0.001)
        assert rows[n]["max_count"] == 2
        assert rows[n]["unique_share"] > 0.85                              # durchgehend deutlich seltener mehrdeutig als bei Gale-Shapley
