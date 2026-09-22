"""Stabile Mitbewohner - Irvings Algorithmus - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Anders als die Fall-Demos im Portfolio (ein Anwendungsfall, mehrere Verfahren im Vergleich) zeigt diese Demo EIN
Verfahren - Irvings Algorithmus fuer das Problem der stabilen Mitbewohner - und laesst stattdessen das Beispiel
wachsen. Zehntes Stueck der Matching-Linie, erste Erweiterung des Gale-Shapley-Asts auf EINE Gruppe statt zwei Seiten.
Siehe README.

Lauffaehig mit: streamlit run app.py
"""

import time

import numpy as np
import streamlit as st

import sr_constants as C
import sr_evaluation as ev
import sr_irving as I
from sr_presets import apply_preset, bounds, init_session_state_defaults, load_permalink_settings, randomize_seed, sync_query_params
from sr_visualization import build_noise_sweep, build_progress, build_reach_sweep, build_scale, build_sr_map, build_uniqueness

st.set_page_config(page_title="Stabile Mitbewohner – Sebastian Hanisch", layout="wide")


def _f(x, digits=1):
    return "–" if x is None else f"{x:.{digits}f}".replace(".", ",")


def _int(x):
    return f"{x:,.0f}".replace(",", " ")


def _ms(s, digits=1):
    return f"{_f(s['mean'], digits)} | {_f(s['median'], digits)}"


def _share(x):
    return "–" if x is None else f"{100 * x:.0f} %"


@st.cache_resource(show_spinner=False, max_entries=16)
def _analysis(params):
    pref, noise, n, reach, ballung, seed = params
    sc = ev.scenario_from_settings(n, reach, ballung, seed)
    return ev.analyse(sc, pref, noise, seed)


@st.cache_data(show_spinner=False)
def _distribution(n, reach, ballung, pref, noise):
    return ev.distribution(n, reach, ballung, pref, noise)


@st.cache_data(show_spinner=False)
def _reach_sweep(n, ballung):
    return ev.reach_sweep(n, ballung)


@st.cache_data(show_spinner=False)
def _noise_sweep(n, reach, ballung):
    return ev.noise_sweep(n, reach, ballung)


@st.cache_data(show_spinner=False)
def _scale():
    return ev.scale_table()


@st.cache_data(show_spinner=False)
def _uniqueness():
    return ev.uniqueness()


st.title("🧩 Stabile Mitbewohner – wenn Stabilität nicht immer möglich ist")
st.markdown(
    """
**Gale-Shapley** findet immer eine stabile Paarung - solange es **zwei getrennte Seiten** gibt. Hier gibt es nur **eine
einzige Gruppe**: jeder ordnet jeden anderen erreichbaren Mitbewohner. **Irvings Algorithmus** (1985) findet trotzdem eine
stabile Paarung, wenn es eine gibt - aber anders als im zweiseitigen Fall **muss es keine geben**. Das ist der zentrale
Unterschied dieses Stücks: nicht ein neues Ziel, sondern eine neue, härtere Frage - existiert überhaupt eine Lösung?
"""
)
st.caption(
    "Anders als die Fall-Demos im Portfolio, die an einem Anwendungsfall mehrere Verfahren vergleichen, zeigt diese Demo - zehntes Stück der Matching-Linie der \"Konzepte\"-Reihe, "
    "erste von vier Erweiterungen des Gale-Shapley-Asts (inspiriert von Alvin Roths Arbeiten zu Marktdesign ohne Geld) - **ein** Verfahren an einem wachsenden Beispiel. "
    "Danach folgen Krankenhaus-Zulassung, Top Trading Cycles und Nierentausch, alle drei inzwischen gebaut."
)

with st.expander("So funktioniert Irvings Algorithmus", expanded=True):
    st.markdown(
        """
1. **Phase 1 – Bewerbung beim eigenen Favoriten:** jeder bewirbt sich bei seinem aktuell besten verbleibenden Kandidaten; der nimmt **bedingungslos** an (verdrängt dabei seinen bisherigen Halt, falls vorhanden - der wird wieder frei) und streicht sofort jeden, den er schlechter einstuft als den neu Angenommenen, aus seiner Liste.
2. **Läuft eine Liste dabei leer, ist das (noch) harmlos:** diese Person bleibt garantiert in jeder stabilen Paarung frei - der Rest kann trotzdem lösbar sein.
3. **Phase 2 – Rotationen beseitigen:** hat noch jemand mehr als einen möglichen Partner übrig, gibt es eine *Rotation* (eine Kette sich gegenseitig blockierender zweiter Wahlen) - sie wird symmetrisch aus allen betroffenen Listen gestrichen.
4. **Läuft dabei eine Liste leer, ist das kein Zufall mehr:** es beweist, dass **keine** stabile Paarung existiert. Läuft Phase 2 dagegen durch, bis jede Liste höchstens einen Eintrag hat, ist das die (eindeutig oder mehrfach mögliche) stabile Paarung.
        """
    )

st.caption("🎯 Schnellstart – eine Beispielkarte laden:")
names = list(C.PRESETS.keys())
for row in range(0, len(names), 4):
    preset_cols = st.columns(4)
    for col, name in zip(preset_cols, names[row:row + 4]):
        with col:
            st.button(name, width="stretch", on_click=apply_preset, args=(name,), help=C.PRESET_HELP[name] or None)

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    st.header("⚙️ Einstellungen")
    pref = st.radio("Vorlieben", list(C.PREF_LABELS), key="pref_radio", format_func=lambda k: C.PREF_LABELS[k],
                     help="Nur Entfernung: alle ordnen gleich, die Paarung ist immer eindeutig und gleich Greedy. Streuung: jeder schätzt selbst (mit Fahrzeit als Anker). Zufall: kein Bezug zur Fahrzeit mehr.")
    if pref == "noise":
        noise = st.slider("Streuung [min]", *bounds("noise_slider"), key="noise_slider", step=C.NOISE_STEP, help="Wie stark die eigene Schätzung von der echten Fahrzeit abweichen kann.")
    else:
        noise = C.DEFAULT_NOISE
    n = st.slider("Mitbewohner", *bounds("n_slider"), key="n_slider", help="Gruppengröße.")
    reach = st.slider("Reichweite [min]", *bounds("reach_slider"), key="reach_slider", step=5, help="Wie weit zwei Mitbewohner höchstens auseinander liegen dürfen, um überhaupt zueinander zu passen. Gegenintuitiv: größere Reichweite macht eine stabile Paarung seltener, nicht wahrscheinlicher.")
    ballung = st.slider("Ballung [%]", *bounds("ballung_slider"), key="ballung_slider", step=25, help="0 = gleichmäßig verteilt, 100 = alle um drei Zentren gruppiert.")
    seed = st.number_input("Zufalls-Seed", *bounds("seed_input"), key="seed_input", step=1)
    st.button("🎲 Neue Karte generieren", width="stretch", on_click=randomize_seed, help="Würfelt einen neuen Zufalls-Seed. Die Verteilung über 100 feste Karten weiter unten ändert sich dabei nicht.")

# --- Ziel und Ablauf ------------------------------------------------------------------------------------------------

st.markdown("## 🎯 Ablauf")
step_col, play_col = st.columns([6, 2])
params = (pref, int(noise), int(n), int(reach), int(ballung), int(seed))
with st.spinner("Rechne..."):
    a = _analysis(params)
sc, res = a.scenario, a.result
level, code, d = ev.verdict(a)
n_events = res.n_events
if st.session_state.get("sr_step_owner") != params:
    st.session_state["sr_step"] = n_events
    st.session_state["sr_step_owner"] = params
with step_col:
    if n_events > 0:
        step = st.slider("Ereignis", 0, n_events, key="sr_step", help="Wie viele Ereignisse der Suche schon geschehen sind (Bewerbung, Annahme, Verdrängung, Kürzung, Rotation). Ganz rechts das Ergebnis.")
    else:
        step = 0
        st.caption("Kein Ereignis: keine Paare möglich.")
with play_col:
    auto_play = st.button("▶️ Abspielen", width="stretch", disabled=n_events == 0)
sync_query_params({"pref_radio": pref, "noise_slider": int(noise), "n_slider": int(n), "reach_slider": int(reach), "ballung_slider": int(ballung), "seed_input": int(seed)})
view_slot = st.empty()


def _event_text(k):
    if k == 0:
        return f"Anfang: alle {sc.n} Personen stehen noch mit ihrer vollen Liste da. Noch keine Bewerbung."
    e = res.events[k - 1]
    if e.kind == I.EV_PROPOSE:
        return f"{e.p} bewirbt sich bei {e.q} (seinem aktuellen Favoriten)."
    if e.kind == I.EV_ACCEPT:
        return f"{e.q} nimmt {e.p} an (bedingungslos - jeder Schlechtere ist längst gestrichen)."
    if e.kind == I.EV_DISPLACE:
        return f"{e.p} wird dadurch von {e.q} verdrängt und wieder frei."
    if e.kind == I.EV_TRIM_REJECT:
        return f"{e.q} streicht {e.p} aus der eigenen Liste (schlechter als der neu Angenommene) - {e.p} hat sich {e.q} nie beworben."
    if e.kind == I.EV_PHASE1_UNMATCHED:
        return f"{e.p}s Liste ist leer und {e.p} ist frei - harmlos: {e.p} bleibt garantiert in jeder stabilen Paarung unversorgt."
    if e.kind == I.EV_ROTATION_FOUND:
        return f"Rotation gefunden: {' → '.join(f'{x}≻{y}' for x, y in e.pairs)} - wird jetzt symmetrisch beseitigt."
    if e.kind == I.EV_ROTATION_REJECT:
        return f"{e.p} und {e.q} streichen sich gegenseitig (Teil der Rotationsbeseitigung)."
    if e.kind == I.EV_NO_STABLE_MATCHING:
        return f"{e.p}s Liste läuft dabei leer - und das beweist: es gibt keine stabile Paarung für diese Karte."
    return "unbekanntes Ereignis"


def _cert_table():
    c = a.cert
    ok = lambda b: "✅" if b else "❌"
    rows = [("Gültigkeit", ok(c["s1_valid"])), ("Keine blockierende Paarung", ok(c["s2_no_blocking"])),
            ("Maximalität", ok(c["s3_maximal"])), ("Kanten tatsächlich möglich", ok(c["s4_mutual"]))]
    return {"Bestandteil": [r[0] for r in rows], "Ergebnis": [r[1] for r in rows]}


def _render(k):
    with view_slot.container():
        c1, c2 = st.columns([3, 2])
        c1.markdown(f"**Nach {k} von {n_events} Ereignissen** – " + _event_text(k))
        snap = I.state_at(res, k)
        event = res.events[k - 1] if k > 0 else None
        final = res.pairs if (k == n_events and res.solvable) else None
        c1.plotly_chart(build_sr_map(sc, snap, event, final), width="stretch", key=f"sr_map_{k}")
        c2.markdown("**Verlauf**")
        c2.plotly_chart(build_progress(res, k), width="stretch", key=f"sr_progress_{k}")
        if k == n_events and res.solvable:
            st.markdown("**Beweis:** ist die Paarung tatsächlich stabil?")
            st.table(_cert_table())
        elif k == n_events and not res.solvable:
            st.error(f"Bewiesen unlösbar: Person {res.unsolvable_agent}s Liste lief in Phase 2 leer (nicht schon harmlos in Phase 1).")


if auto_play:
    frames = sorted({int(round(x)) for x in np.linspace(0, n_events, min(n_events, 40) + 1)})
    for k in frames:
        _render(k)
        time.sleep(min(0.6, 6.0 / max(len(frames), 1)))
    step = n_events
else:
    _render(step)

st.caption("Grün = entschieden (Liste auf 1 Eintrag), grau = noch offen, rot umrandet = ausgeschlossen. Blaue Linien: die feststehende Paarung (nur am letzten Schritt). Farbige Kante: das letzte Ereignis "
           "(grün = Annahme, rot = Verdrängung, grau gestrichelt = Kürzung, violett = Rotation).")

st.markdown("---")

# --- Wie gut? ---------------------------------------------------------------------------------------------------------

st.markdown("## 🎯 Existiert überhaupt eine stabile Paarung?")
if code == ev.NONE:
    st.info("ℹ️ Kein einziges Paar ist möglich – die Reichweite ist zu klein.")
elif code == ev.UNSOLVABLE:
    st.error(f"❌ Keine stabile Paarung existiert. {d['phase1_unmatched']} Personen wären harmlos unversorgt geblieben, aber Person {d['unsolvable_agent']}s Liste lief erst in Phase 2 (Rotation) leer - das beweist die Unlösbarkeit.")
else:
    st.success(f"✅ {d['count']} Paare, {d['phase1_unmatched']} Personen bleiben harmlos unversorgt - bewiesen stabil (kein blockierendes Paar).")
m1, m2, m3, m4 = st.columns(4)
m1.metric("Lösbar?", "Ja" if d["solvable"] else "Nein")
m2.metric("Paare", f"{d['count']}" if d["solvable"] else "–", delta=f"{d['phase1_unmatched']} unversorgt" if d["solvable"] else None, delta_color="off")
m3.metric("Rotationen", f"{d['rotations']}", delta=f"{d['rejections2']} Streichungen in Phase 2", delta_color="off")
m4.metric("Aufwand (Vorschläge)", _int(d["proposals"]), delta=f"{d['rejections1']} Kürzungen in Phase 1", delta_color="off")

if d["solvable"]:
    st.markdown("**Naives Vorgehen gegen Irvings Algorithmus:**")
    cmp_rows = ev.compare_table(a)
    st.table({"": [r["label"] for r in cmp_rows], "Paare": [str(r["count"]) for r in cmp_rows], "Blockierende Paare": ["–" if r["blocking"] is None else str(r["blocking"]) for r in cmp_rows]})

st.markdown(f"**Nicht nur diese eine Karte:** {len(C.DIST_SEEDS)} feste Karten mit denselben Einstellungen (Mitbewohner {n}, Reichweite {reach}, Ballung {ballung} %, {C.PREF_LABELS[pref]}), getrennt vom Seed oben.")
dist = _distribution(int(n), int(reach), int(ballung), pref, int(noise))
if dist["n_valid"] == 0:
    st.info("ℹ️ Auf keiner der Karten gibt es ein mögliches Paar.")
else:
    p1, p2, p3, p4 = st.columns(4)
    p1.metric("Lösbar", _share(dist["solvable_share"]), delta=f"{dist['n_valid']} Karten geprüft", delta_color="off")
    p2.metric("Paare (Mittel | Median)", _ms(dist["count"]) if dist["count"]["mean"] is not None else "–")
    p3.metric("Mit mindestens einer Rotation", _share(dist["rotations_share_gt0"]))
    p4.metric("Naives Vorgehen scheitert", _share(dist["naive_blocking_share_gt0"]), delta=f"Rang Ø {_f(dist['rank_naive_mean'], 2)} gegen {_f(dist['rank_stable_mean'], 2)}", delta_color="off")

st.markdown("---")

# --- Experimente auf Abruf --------------------------------------------------------------------------------------------

st.subheader("🔬 Wovon hängt es ab?")
if st.button("Reichweiten-Sweep (40 Karten je Wert)", key="reach_start"):
    st.session_state["reach_on"] = (int(n), int(ballung))
if st.session_state.get("reach_on") == (int(n), int(ballung)):
    with st.spinner("Rechne..."):
        rrows = _reach_sweep(int(n), int(ballung))
    c1, c2 = st.columns([3, 2])
    c1.plotly_chart(build_reach_sweep(rrows), width="stretch", key="sr_reach_chart")
    c2.table({"Reichweite": [r["reach"] for r in rrows], "Grad": [_f(r["degree"], 2) for r in rrows], "Lösbar": [_share(r["solvable_share"]) for r in rrows]})
    st.caption("Je größer die Reichweite, desto mehr Kandidaten hat jeder - und desto seltener existiert eine stabile Paarung, nicht öfter.")

if st.button("Streuung-Sweep (40 Karten je Wert)", key="noise_start"):
    st.session_state["noise_on"] = (int(n), int(reach), int(ballung))
if st.session_state.get("noise_on") == (int(n), int(reach), int(ballung)):
    with st.spinner("Rechne..."):
        nrows = _noise_sweep(int(n), int(reach), int(ballung))
    c1, c2 = st.columns([3, 2])
    c1.plotly_chart(build_noise_sweep(nrows), width="stretch", key="sr_noise_chart")
    c2.table({"Streuung k": [r["k"] for r in nrows], "Lösbar": [_share(r["solvable_share"]) for r in nrows]})
    st.caption("k = 0 ist reine Entfernung (immer lösbar, immer eindeutig); schon kleine Streuung genügt für einen glatten Übergang.")

if st.button("Aufwand gegen die Größe (n = 10 bis 320)", key="scale_start"):
    st.session_state["scale_on"] = True
if st.session_state.get("scale_on"):
    with st.spinner("Rechne..."):
        srows = _scale()
    c1, c2 = st.columns([3, 2])
    c1.plotly_chart(build_scale(srows), width="stretch", key="sr_scale_chart")
    c2.table({"n": [r["n"] for r in srows], "Reichweite": [r["reach"] for r in srows], "Vorschläge": [_f(r["proposals"], 1) for r in srows]})
    st.caption("Mittel über 10 feste Karten, Reichweite so gewählt, dass der mittlere Grad bei jeder Größe etwa 3 bleibt.")

if st.button("Eindeutigkeit prüfen (Brute Force, kleine Karten)", key="unique_start"):
    st.session_state["unique_on"] = True
if st.session_state.get("unique_on"):
    with st.spinner("Probiere alle Paarungen..."):
        urows = _uniqueness()
    c1, c2 = st.columns([3, 2])
    c1.plotly_chart(build_uniqueness(urows), width="stretch", key="sr_unique_chart")
    c2.table({"n": [r["n"] for r in urows], "geprüft": [r["n_solvable"] for r in urows], "eindeutig": [_share(r["unique_share"]) for r in urows]})
    st.caption("Anders als im zweiseitigen Fall (dort waren bei Streuung ±20 34 % der Karten mehrdeutig) ist eine lösbare Karte hier meist eindeutig - Mehrdeutigkeit ist selten und fast immer genau 2 Lösungen.")

st.markdown("---")

# --- Grenzen -----------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Eine stabile Paarung existiert immer** | Muss nicht so sein, sobald es nur eine Gruppe statt zwei Seiten gibt. | **dieses Stück** |
| **Vorlieben, kein Preis** | Wer zahlen kann, verschiebt Prioritäten - das braucht Kapazitäten statt reiner Präferenzen. | **Krankenhaus-Zulassung** (gebaut) |
| **Paare, keine größeren Kreise** | Manche Tauschbörsen (Wohnungen, Nieren) brauchen Zyklen/Ketten statt Paare. | **Top Trading Cycles → Nierentausch** (gebaut) |
| **Jeder nimmt genau einen Partner** | Kliniken, Schulen und Fahrzeugflotten brauchen Kapazitäten statt 1:1. | **Krankenhaus-Zulassung** (gebaut) |
"""
)
st.caption("Damit ist die vierteilige Erweiterung der Matching-Linie um den Gale-Shapley-Ast vollständig gebaut, inspiriert von Alvin Roths Marktdesign-Arbeiten.")

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Modell.** Eine Gruppe $V$, jeder $i$ hat eine strikte Präferenzliste über eine Teilmenge $A(i)\subseteq V\setminus\{i\}$
(erreichbar/akzeptabel; symmetrisch: $j\in A(i) \iff i\in A(j)$). Gesucht: eine Paarung $M$ (Teilmenge disjunkter Paare),
sodass kein **blockierendes Paar** existiert - kein $(a,b)\notin M$ mit $b\in A(a)$, $a\in A(b)$, das beide ihrem
jetzigen Zustand (Partner oder frei) vorziehen.

**Phase 1 (Bewerbung).** Jeder bewirbt sich bei seinem aktuellen Favoriten $f$; $f$ nimmt bedingungslos an (verdrängt
den bisherigen Halt, falls vorhanden) und streicht aus der eigenen Liste symmetrisch jeden, der schlechter eingestuft
ist als der neu Angenommene. Das ist nur deshalb korrekt, weil dadurch bei jeder Bewerbung bereits jeder Schlechtere
gestrichen wurde: wer zum Zeitpunkt seiner Bewerbung noch auf der Liste des Angesprochenen steht, ist zwangsläufig
mindestens so gut wie dessen aktueller Halt. Eine während Phase 1 leerlaufende Liste beweist nur, dass diese eine
Person in jeder stabilen Paarung frei bleibt (falls eine existiert) - **nicht**, dass keine existiert.

**Phase 2 (Rotationen).** Eine *Rotation* ist eine Kette $(x_0,y_0),\dots,(x_{k-1},y_{k-1})$ mit $y_i=$ zweiter Eintrag
von $x_i$s Liste und $x_{i+1}=$ letzter Eintrag von $y_i$s Liste. Beseitigung: für jedes $i$ werden aus $y_i$s Liste
alle Eintraege gestrichen, die schlechter als $x_{i-1}$ eingestuft sind (nicht nur $x_i$ selbst - sonst bliebe nur ein
Teilstück der Rotation entfernt, siehe Gusfield & Irving 1989, Abschnitt 4.2.3). Läuft dabei eine Liste einer Person
leer, die **nicht** schon aus Phase 1 als harmlos unversorgt bekannt war, beweist das **Nichtexistenz** (Irvings Satz).
Terminiert Phase 2, ohne dass das passiert, hat jede Liste höchstens einen Eintrag - das ist die stabile Paarung.

**Aufwand.** $O(n^2)$ im schlechtesten Fall (Irving 1985); die Praxis liegt bei sparsamen, reichweitenbasierten Listen
deutlich darunter (siehe „Aufwand gegen die Größe").

Implementiert in `sr_scenario.py` (Karte, unverändert von `blossom-demo` übernommen), `sr_preferences.py` (Vorlieben),
`sr_irving.py` (Kern mit Ereignisprotokoll und Zertifikat), `sr_oracle.py` (Brute Force), `sr_evaluation.py`
(Kennzahlen, Verteilungen, Sweeps).
        """
    )

st.markdown("---")

st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning. Interesse an einer maßgeschneiderten Lösung für "
    "Ihr Unternehmen? [Kontakt aufnehmen](https://sebastianhanisch.net/kontakt.html)"
)
