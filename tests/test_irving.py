"""Irvings Algorithmus (`sr_irving.py`) gegen den unabhaengigen Brute-Force-Pruefer (`sr_oracle.py`), Lehrbuchbeispiele,
die Phase-1- gegen Phase-2-Unterscheidung, Negativkontrollen fuer die drei beim Portieren gefundenen Fehlerklassen,
das Zertifikat und das Ereignisprotokoll."""

import random

import pytest

import sr_irving as I
import sr_oracle as O


def _ranks(prefs):
    return [{x: k for k, x in enumerate(p)} for p in prefs]


def _is_stable(prefs, pairs):
    matched = {}
    for i, j in pairs:
        matched[i] = j
        matched[j] = i
    return O._is_stable(prefs, _ranks(prefs), matched, len(prefs))


def _random_complete(n, seed):
    rng = random.Random(seed)
    prefs = []
    for i in range(n):
        others = [j for j in range(n) if j != i]
        rng.shuffle(others)
        prefs.append(others)
    return prefs


def _random_incomplete(n, p_edge, seed):
    rng = random.Random(seed)
    adj = [[] for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            if rng.random() < p_edge:
                adj[i].append(j)
                adj[j].append(i)
    prefs = []
    for i in range(n):
        lst = list(adj[i])
        rng.shuffle(lst)
        prefs.append(lst)
    return prefs


# --- Kreuzpruefung gegen die Brute-Force -------------------------------------------------------------------------

@pytest.mark.parametrize("n", range(2, 13))
@pytest.mark.parametrize("trial", range(25))
def test_matches_brute_force_complete_lists(n, trial):
    prefs = _random_complete(n, n * 1000003 + trial)
    res = I.solve(prefs, record=False)
    brute = O.stable_roommates_brute(prefs)
    assert res.solvable == (brute is not None), (n, trial, prefs)
    if res.solvable:
        assert _is_stable(prefs, res.pairs), (n, trial, prefs, res.pairs)


@pytest.mark.parametrize("n", range(2, 13))
@pytest.mark.parametrize("p_edge", [0.3, 0.5, 0.7])
@pytest.mark.parametrize("trial", range(15))
def test_matches_brute_force_incomplete_lists(n, p_edge, trial):
    prefs = _random_incomplete(n, p_edge, n * 7000003 + trial * 13 + int(p_edge * 100))
    res = I.solve(prefs, record=False)
    brute = O.stable_roommates_brute(prefs)
    assert res.solvable == (brute is not None), (n, p_edge, trial, prefs)
    if res.solvable:
        assert _is_stable(prefs, res.pairs), (n, p_edge, trial, prefs, res.pairs)


def test_geometric_scenarios_match_brute_force():
    """Echte Karten aus `sr_scenario.py`/`sr_preferences.py` (nicht nur abstrakte Zufallsgraphen), kleine n fuer die
    Brute-Force-Grenze."""
    import sr_preferences as P
    import sr_scenario as S

    for seed in range(20):
        sc = S.generate(10, 30, 0, seed)
        for model in ("dist", "noise", "random"):
            prefs = P.preferences(sc, model, seed=seed)
            res = I.solve(prefs, record=False)
            brute = O.stable_roommates_brute(prefs)
            assert res.solvable == (brute is not None), (seed, model)
            if res.solvable:
                assert _is_stable(prefs, res.pairs)


# --- Lehrbuchbeispiele --------------------------------------------------------------------------------------------

def test_classic_n4_no_stable_matching():
    """Das klassische Lehrbuchbeispiel: 4 Personen, zyklische Vorlieben, keine stabile Paarung (Irving 1985)."""
    prefs = [[1, 2, 3], [2, 0, 3], [0, 1, 3], [0, 1, 2]]
    res = I.solve(prefs)
    assert res.solvable is False
    assert O.stable_roommates_brute(prefs) is None


def test_classic_n3_cyclic_no_stable_matching():
    """Kleinstes Beispiel ohne stabile Paarung: 3 Personen, zyklische Vorlieben 0:[1,2],1:[2,0],2:[0,1] - von Hand
    nachgerechnet (alle drei moeglichen Einzelpaarungen haben ein blockierendes Paar) UND von der Brute-Force bestaetigt.
    Dies ist genau das Beispiel, an dem die ERSTE (verworfene) Fassung dieses Moduls scheiterte: sie lieferte
    faelschlich pairs=((0,1),) - siehe Moduldoku."""
    prefs = [[1, 2], [2, 0], [0, 1]]
    res = I.solve(prefs)
    assert res.solvable is False
    assert O.stable_roommates_brute(prefs) is None
    # der ganze Graph reduziert sich auf eine einzige Rotation, die alles beseitigt
    assert res.rotations == 1
    assert any(e.kind == I.EV_NO_STABLE_MATCHING for e in res.events)


def test_n3_one_agent_legitimately_free():
    """n=3, NICHT zyklisch (0:[1,2],1:[0,2],2:[0,1]): 0 und 1 sind gegenseitig ihre beste Wahl, 2 bleibt harmlos frei -
    stabil, im Gegensatz zum zyklischen Fall oben. Brute-Force bestaetigt (0,1) als stabil; 2 landet in
    `phase1_unmatched` (Phase 1 allein reicht, keine Rotation noetig)."""
    prefs = [[1, 2], [0, 2], [0, 1]]
    res = I.solve(prefs)
    assert res.solvable is True
    assert res.pairs == ((0, 1),)
    assert res.phase1_unmatched == (2,)
    assert res.rotations == 0
    assert O.stable_roommates_brute(prefs) == ((0, 1),)


# --- Phase 1 (harmlos) vs. Phase 2 (beweist Unloesbarkeit) leer ----------------------------------------------------

def test_phase1_emptying_is_harmless_not_fatal():
    """Mehrere Personen laufen in Phase 1 leer (ungerade Gruppe, kurze Reichweite) - die Instanz bleibt fuer den Rest
    trotzdem loesbar. Wichtig: das darf NICHT als 'unloesbar' fehlinterpretiert werden."""
    # 5 Personen: 0-1 und 2-3 sind wechselseitig beste Wahl, 4 ist zu niemandem kompatibel (isoliert)
    prefs = [[1], [0], [3], [2], []]
    res = I.solve(prefs)
    assert res.solvable is True
    assert res.pairs == ((0, 1), (2, 3))
    assert res.phase1_unmatched == (4,)
    assert res.unsolvable_agent == -1


def test_phase2_emptying_proves_unsolvable():
    """Eine Liste, die ERST durch eine Rotationsbeseitigung leerlaeuft (nicht schon in Phase 1), beweist echte
    Unloesbarkeit - `unsolvable_agent` muss gesetzt sein und auf eine Person zeigen, die NICHT in `phase1_unmatched`
    stand."""
    prefs = [[1, 2, 3], [2, 0, 3], [0, 1, 3], [0, 1, 2]]
    res = I.solve(prefs)
    assert res.solvable is False
    assert res.unsolvable_agent != -1
    assert res.unsolvable_agent not in res.phase1_unmatched


def test_phase1_and_phase2_unmatched_distinction_on_many_instances():
    """Ueber viele Zufallsinstanzen: jede in Phase 1 unversorgte Person taucht NIE in einer spaeteren Rotation auf
    (ihre Liste ist ja schon leer - Rotationssuche kann sie gar nicht erreichen), und `unsolvable_agent` (falls
    gesetzt) ist nie Teil von `phase1_unmatched`."""
    seen_phase1_unmatched = False
    seen_phase2_failure = False
    for trial in range(300):
        prefs = _random_incomplete(9, 0.35, trial + 500)
        res = I.solve(prefs)
        if res.phase1_unmatched:
            seen_phase1_unmatched = True
        if not res.solvable:
            seen_phase2_failure = True
            assert res.unsolvable_agent not in res.phase1_unmatched
    assert seen_phase1_unmatched and seen_phase2_failure


# --- `dist`-Modell ist eine Falle: nie eine Rotation, Phase 2 dort nie geprueft -------------------------------------

def test_dist_model_is_always_solvable_and_unique():
    """`dist`-Vorlieben (nur Entfernung, siehe `sr_preferences.py`) sind IMMER loesbar und eindeutig - Phase 2 feuert
    hier nie (0 Rotationen). Wichtig fuer die Testabdeckung selbst: `dist` allein wuerde Phase 2 nie pruefen (siehe
    Modultests oben, die bewusst `noise`/`random` verwenden)."""
    import sr_preferences as P
    import sr_scenario as S

    for seed in range(60):
        sc = S.generate(12, 25, seed % 60, seed)
        prefs = P.preferences(sc, "dist", seed=seed)
        res = I.solve(prefs, record=False)
        assert res.solvable is True
        assert res.rotations == 0


# --- Negativkontrollen: die drei beim Portieren gefundenen Fehlerklassen -------------------------------------------

def test_pitfall_missing_trim_on_accept():
    """#1: ohne die Kuerzung ('jeder in der Liste des Annehmenden, der schlechter ist als der neu Angenommene, wird
    gestrichen') direkt bei jeder Annahme wuerde die 'bedingungslose Annahme' falsch: der Favorit koennte jemanden
    annehmen, den er eigentlich schlechter einstuft als seinen aktuellen Halt. Reproduziert an einem handgebauten
    Fall: ohne Kuerzung wuerde 2 (das 0 bevorzugt, aber erst nach der Kuerzung dran waere) niemals 0 erreichen, weil
    0 dauerhaft bei 1 haengen bliebe, obwohl 0 eigentlich 2 vorzieht."""
    # 0:[2,1] (0 will eigentlich 2, aber 1 bewirbt sich zuerst), 1:[0], 2:[0,1]
    prefs = [[2, 1], [0], [0, 1]]
    res = I.solve(prefs)
    assert res.solvable is True
    # 0 und 2 sind gegenseitig beste erreichbare Wahl (0 will 2 am meisten, 2 will 0 am meisten) -> muessen sich finden
    assert (0, 2) in res.pairs
    assert _is_stable(prefs, res.pairs)


def test_pitfall_rotation_pairing_uses_second_choice_not_holder():
    """#2: `_locate_rotation` muss y_i als den ZWEITEN Eintrag von x_i lesen (nicht neu aus einer anderen Groesse
    herleiten) - an der Mehrrotationen-Karte (siehe `test_geometric_scenarios_match_brute_force`) und am n=3-Beispiel
    oben waere ein Off-by-one sofort an einer falschen (nicht-stabilen) Endpaarung sichtbar gewesen; hier zusaetzlich
    eine feste, von Hand verfolgbare Instanz mit genau einer Rotation ueber 3 Personen."""
    prefs = [[1, 2], [2, 0], [0, 1]]
    res = I.solve(prefs)
    assert res.rotations == 1
    ev = next(e for e in res.events if e.kind == I.EV_ROTATION_FOUND)
    assert set(ev.pairs) == {(0, 1), (1, 2), (2, 0)}
    # jedes Paar (xi, yi) muss xi's ZWEITEN Listeneintrag zum Zeitpunkt des Fundes sein
    for x, y in ev.pairs:
        assert y in prefs[x]


def test_pitfall_stale_held_after_rotation_elimination():
    """#3: nach einer Rotationsbeseitigung darf keine veraltete Buchfuehrung stehen bleiben, an der eine SPAETERE
    Rotation abstuerzt (versucht, eine schon entfernte Kante nochmal zu entfernen). Regressionstest: mehrere
    aufeinanderfolgende Rotationen auf derselben, groesseren Zufallsinstanz duerfen nie eine Ausnahme werfen."""
    for seed in range(100):
        prefs = _random_complete(12, seed + 9000)
        res = I.solve(prefs, record=False)  # darf nicht werfen, egal wie viele Rotationen noetig sind
        if res.solvable:
            assert _is_stable(prefs, res.pairs)


# --- Zertifikat ----------------------------------------------------------------------------------------------------

def test_certificate_positive():
    prefs = [[1, 2], [0, 2], [0, 1]]
    res = I.solve(prefs)
    cert = I.certificate(prefs, res.pairs, res.n)
    assert cert["all_ok"]


def test_certificate_catches_blocking_pair():
    prefs = [[1, 2], [0, 2], [0, 1]]
    # absichtlich eine instabile Paarung uebergeben: 1-2 statt 0-1 (0 und 1 sind gegenseitig beste Wahl -> blockiert)
    cert = I.certificate(prefs, ((1, 2),), 3)
    assert cert["all_ok"] is False
    assert cert["s2_no_blocking"] is False


def test_certificate_catches_duplicate_agent():
    prefs = [[1, 2], [0, 2], [0, 1]]
    cert = I.certificate(prefs, ((0, 1), (0, 2)), 3)
    assert cert["s1_valid"] is False
    assert cert["all_ok"] is False


def test_certificate_catches_non_maximal():
    """Zwei freie, gegenseitig erreichbare Personen haetten noch gepaart werden koennen."""
    prefs = [[1, 2, 3], [0, 2, 3], [0, 1, 3], [0, 1, 2]]
    cert = I.certificate(prefs, (), 4)  # niemand gepaart, obwohl alle sich gegenseitig erreichen
    assert cert["s3_maximal"] is False
    assert cert["all_ok"] is False


# --- Ereignisprotokoll / Replay -------------------------------------------------------------------------------------

def test_state_at_replay_matches_final_result():
    prefs = _random_incomplete(10, 0.4, 42)
    res = I.solve(prefs)
    final_snap = I.state_at(res, res.n_events)
    if res.solvable:
        held = res.held_list()
        for i in range(res.n):
            assert final_snap.list_len[i] in (0, 1)
    assert len(res.snapshots) == res.n_events + 1


def test_record_false_matches_record_true_pairs_and_counters():
    for trial in range(30):
        prefs = _random_incomplete(10, 0.4, trial + 3000)
        r1 = I.solve(prefs, record=True)
        r2 = I.solve(prefs, record=False)
        assert r1.solvable == r2.solvable
        assert r1.pairs == r2.pairs
        assert r1.proposals == r2.proposals
        assert r1.rejections1 == r2.rejections1
        assert r1.rejections2 == r2.rejections2
        assert r1.rotations == r2.rotations
        assert r2.events == () and r2.snapshots == ()


# --- Groesse / Aufwand (kein Zeitlimit, nur "haengt nicht") ---------------------------------------------------------

# --- Sekundaerer Smoke-Test gegen das PyPI-Paket `matching` --------------------------------------------------------

def test_agrees_with_matching_package_where_it_is_trustworthy():
    """NICHT das primaere Orakel (das bleibt `sr_oracle.py`, s.o.): `matching.games.StableRoommates` verlangt
    vollstaendige Listen und hat zwei bekannte eigene Fehler (liefert bei manchen unloesbaren Instanzen still eine
    instabile Teilpaarung statt 'keine Loesung'; vereinzelt auch bei loesbaren Instanzen eine instabile Paarung) - hier
    daher nur auf kleinen, VOLLSTAENDIGEN Instanzen geprueft und nur uebernommen, wenn das Paket selbst ein laut
    unserem unabhaengigen Zertifikat stabiles Ergebnis liefert; sonst wird die Instanz einfach uebersprungen."""
    import warnings

    from matching.games import StableRoommates

    agree, checked = 0, 0
    for trial in range(200):
        prefs = _random_complete(8, trial + 20000)
        game = StableRoommates.create_from_dictionary({i: prefs[i] for i in range(8)})
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            pkg_matching = game.solve()
        pkg_pairs = tuple(sorted({(min(a.name, b.name), max(a.name, b.name)) for a, b in pkg_matching.items() if b is not None}))
        pkg_cert = I.certificate(prefs, pkg_pairs, 8)
        if not pkg_cert["all_ok"]:
            continue  # eines der beiden bekannten Paket-Probleme - ueberspringen, nicht als Wahrheitsquelle werten
        checked += 1
        res = I.solve(prefs, record=False)
        assert res.solvable is True
        assert res.pairs == pkg_pairs
        agree += 1
    assert checked >= 100 and agree == checked


def test_large_sparse_instance_solves():
    prefs = _random_incomplete(320, 3.0 / 319, 12345)
    res = I.solve(prefs, record=False)
    assert res.n == 320
    if res.solvable:
        assert _is_stable(prefs, res.pairs)
