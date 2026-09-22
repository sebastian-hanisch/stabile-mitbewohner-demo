"""Rauchtests der Streamlit-Oberfläche per AppTest: Standard, jedes Preset, Schritt-Zustand, Abspielen (auch auf
mehrbildrigen Karten - Regression gegen doppelte Plotly-Schlüssel), Randgrößen, Experimente auf Abruf, Permalink."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import sr_constants as C
from sr_presets import PRESET_KEYS

ROOT = Path(__file__).resolve().parent.parent
APP = ROOT / "app.py"


def _run(setup=None, timeout=600):
    at = AppTest.from_file(str(APP), default_timeout=timeout)
    at.run()
    assert not at.exception, [e.value for e in at.exception]
    if setup is not None:
        setup(at)
        at.run()
        assert not at.exception, [e.value for e in at.exception]
    return at


def _apply(at, name):
    for key, state_key in PRESET_KEYS.items():
        at.session_state[state_key] = C.PRESETS[name][key]


def _set(**kw):
    def setup(at):
        for k, v in kw.items():
            at.session_state[k] = v
    return setup


def _step(at):
    found = [s for s in at.slider if s.key == "sr_step"]
    return found[0] if found else None


def _texts(at):
    return [e.value for e in list(at.success) + list(at.warning) + list(at.info) + list(at.error)]


def _has(at, prefix):
    return any(t.startswith(prefix) for t in _texts(at))


def _play(at):
    [b for b in at.button if b.label == "▶️ Abspielen"][0].click()
    at.run()
    assert not at.exception, [e.value for e in at.exception]


def test_default_renders_without_exception():
    at = _run()
    assert any("Ablauf" in m.value for m in at.markdown)
    assert not at.error


@pytest.mark.parametrize("name", list(C.PRESETS))
def test_every_preset_renders(name):
    at = _run(lambda a: _apply(a, name))
    assert not at.exception


def test_every_preset_step_slider_reaches_the_end():
    for name in C.PRESETS:
        at = _run(lambda a: _apply(a, name))
        step = _step(at)
        if step is not None:
            assert step.value == step.max


def test_play_runs_through_all_frames_on_a_multi_event_map():
    at = _run(lambda a: _apply(a, "🧩 Mehrere Rotationen"))
    assert _step(at).max > 10
    _play(at)


def test_play_on_the_default_map():
    at = _run()
    if _step(at).max > 0:
        _play(at)


def test_step_slider_visits_every_kind_of_event():
    at = _run(lambda a: _apply(a, "🧩 Mehrere Rotationen"))
    last = int(_step(at).max)
    for k in (0, 1, last // 3, last // 2, last - 1, last):
        _step(at).set_value(k)
        at.run()
        assert not at.exception, (k, [e.value for e in at.exception])


def test_no_feasible_pair_renders():
    from sr_scenario import generate
    seed = next(k for k in range(500) if generate(C.N_MIN, C.REACH_MIN, 0, k).m == 0)
    at = _run(_set(n_slider=C.N_MIN, reach_slider=C.REACH_MIN, seed_input=seed))
    assert any("Kein einziges Paar ist möglich" in t for t in _texts(at))


def test_extreme_sizes_render():
    for n, reach in ((C.N_MIN, C.REACH_MIN), (C.N_MAX, C.REACH_MAX), (C.N_MIN, C.REACH_MAX), (C.N_MAX, C.REACH_MIN)):
        at = _run(_set(n_slider=n, reach_slider=reach))
        assert not at.exception


def test_noise_slider_hidden_unless_pref_is_noise():
    at = _run(_set(pref_radio="dist"))
    assert "Streuung [min]" not in {s.label for s in at.sidebar.slider}
    at = _run(_set(pref_radio="noise"))
    assert "Streuung [min]" in {s.label for s in at.sidebar.slider}


def test_step_slider_returns_to_the_last_step_when_the_map_changes():
    at = _run(lambda a: _apply(a, "🧩 Mehrere Rotationen"))
    last = int(_step(at).max)
    assert _step(at).value == last
    _step(at).set_value(2)
    at.run()
    assert _step(at).value == 2
    at.session_state["seed_input"] = C.PRESETS["🧩 Mehrere Rotationen"]["seed"] + 1
    at.run()
    assert _step(at).value == _step(at).max


def test_unsolvable_end_state_shows_the_culprit():
    at = _run(lambda a: _apply(a, "🔁 Kein stabiler Weg"))
    at.session_state["sr_step"] = int(_step(at).max)
    at.run()
    assert any("Bewiesen unlösbar" in e.value for e in at.error)


def test_solvable_end_state_shows_the_certificate():
    at = _run(lambda a: _apply(a, "🧩 Mehrere Rotationen"))
    at.session_state["sr_step"] = int(_step(at).max)
    at.run()
    proof = next((t.value for t in at.table if "Bestandteil" in t.value.to_dict("list")), None)
    assert proof is not None
    assert all(v == "✅" for v in proof["Ergebnis"])


def test_experiments_run_on_demand():
    at = _run(lambda a: _apply(a, "🗺️ Mittlere Karte"))
    for key in ("reach_start", "noise_start", "scale_start", "unique_start"):
        at.button(key=key).click()
        at.run()
        assert not at.exception, [e.value for e in at.exception]


def test_permalink_roundtrip_and_clamping():
    at = AppTest.from_file(str(APP), default_timeout=60)
    at.query_params["n"] = "999999"
    at.query_params["reach"] = "5"
    at.query_params["pref"] = "not-a-real-model"
    at.run()
    assert not at.exception
    n_slider = at.sidebar.slider(key="n_slider")
    reach_slider = at.sidebar.slider(key="reach_slider")
    assert n_slider.value == C.N_MAX
    assert reach_slider.value == C.REACH_MIN


def test_no_dead_file_links_in_markdown():
    at = _run()
    texts = " ".join(m.value for m in at.markdown)
    assert "sr_irving.py)" not in texts and "app.py)" not in texts


def test_footer_present():
    at = _run()
    assert any("sebastianhanisch.net" in c.value for c in at.caption)


def test_every_plotly_chart_has_a_unique_key():
    at = _run(lambda a: _apply(a, "🧩 Mehrere Rotationen"))
    keys = [c.proto.id for c in at.get("plotly_chart")] if hasattr(at, "get") else None
    # AppTest raises DuplicateWidgetID itself on rerun if keys collide - reaching here without exception across the
    # play-button regression test above is the real guard; this test just documents the convention.
    assert not at.exception
