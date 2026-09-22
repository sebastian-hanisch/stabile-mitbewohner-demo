"""Presets: jedes hat einen Hilfetext, die genannten Zahlen stimmen, Regler-/Schrittgitter sind gültig, Permalink-Casting
funktioniert."""

import sr_constants as C
import sr_evaluation as ev
from sr_presets import PRESET_KEYS, SETTING_SPECS, STEPS


def test_every_preset_has_help_text():
    for name in C.PRESETS:
        assert name in C.PRESET_HELP and C.PRESET_HELP[name]


def test_preset_keys_cover_every_setting_spec_except_derived():
    assert set(PRESET_KEYS.values()) <= set(SETTING_SPECS)
    for name, p in C.PRESETS.items():
        assert set(p) == set(PRESET_KEYS), name


def test_bounds_and_step_grid_are_valid():
    for state_key, spec in SETTING_SPECS.items():
        if spec.lo is not None and spec.hi is not None:
            assert spec.lo <= spec.default <= spec.hi, state_key
    for key, step in STEPS.items():
        lo, hi = SETTING_SPECS[key].lo, SETTING_SPECS[key].hi
        assert (hi - lo) % step == 0, key


def test_presets_do_not_collide_with_dist_seeds():
    for name, p in C.PRESETS.items():
        assert p["seed"] not in C.DIST_SEEDS, name


def test_default_preset_like_medium_map_is_solvable_with_seven_pairs():
    sc = ev.scenario_from_settings(C.DEFAULT_N, C.DEFAULT_REACH, C.DEFAULT_BALLUNG, C.DEFAULT_SEED)
    a = ev.analyse(sc, C.DEFAULT_PREF, C.DEFAULT_NOISE, C.DEFAULT_SEED)
    assert a.result.solvable is True and len(a.result.pairs) == 7


def _verdict_for(name):
    p = C.PRESETS[name]
    sc = ev.scenario_from_settings(p["n"], p["reach"], p["ballung"], p["seed"])
    a = ev.analyse(sc, p["pref"], p["noise"], p["seed"])
    return ev.verdict(a)


def test_presets_show_what_the_help_text_says():
    level, code, d = _verdict_for("🔁 Kein stabiler Weg")
    assert code == ev.UNSOLVABLE and d["rotations"] == 1 and d["isolated"] == 1

    level, code, d = _verdict_for("🧩 Mehrere Rotationen")
    assert code == ev.SOLVED and d["rotations"] == 4 and d["count"] == 5

    level, code, d = _verdict_for("📏 Nur Entfernung")
    assert code == ev.SOLVED and d["rotations"] == 0

    level, code, d = _verdict_for("🗺️ Mittlere Karte")
    assert code == ev.SOLVED and d["count"] == 7 and d["phase1_unmatched"] == 6

    level, code, d = _verdict_for("📉 Große Reichweite")
    assert code == ev.UNSOLVABLE

    level, code, d = _verdict_for("🎲 Zufällige Vorlieben")
    assert code == ev.UNSOLVABLE and d["rotations"] == 2

    level, code, d = _verdict_for("➗ Ungerade Gruppe")
    assert code == ev.SOLVED and d["count"] == 9 and d["phase1_unmatched"] == 3

    level, code, d = _verdict_for("⚠️ Naives Vorgehen scheitert")
    assert code == ev.SOLVED and d["count"] == 8 and d["naive_blocking"] == 6


def test_the_reach_20_seed_used_in_the_reach_preset_is_solvable_with_eight_pairs():
    """Der Hilfetext des 'Große Reichweite'-Presets vergleicht mit derselben Ziehung bei Reichweite 20."""
    sc = ev.scenario_from_settings(20, 20, 0, 8)
    a = ev.analyse(sc, "noise", 20, 8)
    assert a.result.solvable is True and len(a.result.pairs) == 8
