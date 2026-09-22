"""Plotly-Abbildungen: Karte mit dem Ereignisverlauf, Fortschritt (wie viele Listen schon entschieden sind), Reichweiten-
/Rauschen-Sweep, Aufwand gegen Größe, Eindeutigkeit gegen Größe. Achsen sind gesperrt (fixedrange) für Touch-Geräte.

Anders als bei Gale-Shapley gibt es waehrend Phase 1 KEINE global konsistente "aktuelle Paarung" (`held` in `sr_irving.py`
ist waehrend Phase 1 bewusst einseitig, siehe dortige Moduldoku) - die Karte zeigt deshalb den Status jeder Person
(entschieden/offen/ausgeschlossen) plus das jeweils letzte Ereignis, und zeichnet eine durchgezogene Paarung nur am
allerletzten Schritt, wenn `res.pairs` tatsaechlich feststeht."""

import plotly.graph_objects as go
from plotly.subplots import make_subplots

import sr_constants as C
import sr_irving as I


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=-0.08), plot_bgcolor="rgba(0,0,0,0)")
    return lock_axes(fig)


def _collinear(sc):
    pts = sc.pts
    if len(pts) < 3:
        return True
    (x0, y0), (x1, y1) = pts[0], next((p for p in pts if p != pts[0]), pts[0])
    return all((x1 - x0) * (y - y0) - (y1 - y0) * (x - x0) == 0 for x, y in pts)


def _edge_path(sc, i, j, curved, steps=14):
    (x0, y0), (x1, y1) = sc.pts[i], sc.pts[j]
    if not curved:
        return [x0, x1], [y0, y1]
    dx, dy = x1 - x0, y1 - y0
    side = 1 if (i + j) % 2 == 0 else -1
    cx, cy = (x0 + x1) / 2 - side * 0.35 * dy, (y0 + y1) / 2 + side * 0.35 * dx
    ts = [k / steps for k in range(steps + 1)]
    return ([(1 - t) ** 2 * x0 + 2 * (1 - t) * t * cx + t * t * x1 for t in ts], [(1 - t) ** 2 * y0 + 2 * (1 - t) * t * cy + t * t * y1 for t in ts])


def _segments(sc, pairs, curved=False):
    x, y = [], []
    for i, j in pairs:
        px, py = _edge_path(sc, i, j, curved)
        x += px + [None]
        y += py + [None]
    return x, y


def _map_layout(fig, sc, height):
    xs = [p[0] for p in sc.pts]
    ys = [p[1] for p in sc.pts]
    pad = 8
    if _collinear(sc):
        span = max(max(xs) - min(xs), max(ys) - min(ys), 1)
        cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
        if max(xs) - min(xs) >= max(ys) - min(ys):
            fig.update_xaxes(visible=False, range=[min(xs) - pad, max(xs) + pad])
            fig.update_yaxes(visible=False, range=[cy - span * 0.22, cy + span * 0.22])
        else:
            fig.update_xaxes(visible=False, range=[cx - span * 0.22, cx + span * 0.22])
            fig.update_yaxes(visible=False, range=[min(ys) - pad, max(ys) + pad])
        return _base(fig, min(height, 320))
    fig.update_xaxes(visible=False, range=[min(xs) - pad, max(xs) + pad], scaleanchor="y", scaleratio=1, constrain="domain")
    fig.update_yaxes(visible=False, range=[min(ys) - pad, max(ys) + pad], constrain="domain")
    return _base(fig, height)


_EVENT_COLOR = {I.EV_PROPOSE: "#888", I.EV_ACCEPT: C.COLORS["propose"], I.EV_DISPLACE: C.COLORS["displace"],
                I.EV_TRIM_REJECT: "#aaaaaa", I.EV_ROTATION_FOUND: C.COLORS["rotation"], I.EV_ROTATION_REJECT: C.COLORS["rotation"]}


def build_sr_map(sc, snap, event=None, final_pairs=None, height=430):
    """Karte nach k Ereignissen: moegliche Paare schwach grau, am letzten Schritt die feststehende Paarung blau; jede
    Person eingefaerbt nach Status (entschieden/offen/ausgeschlossen); das letzte Ereignis als hervorgehobene Kante."""
    curved = _collinear(sc)
    fig = go.Figure()
    all_pairs = [(i, j) for i in range(sc.n) for j in sc.adj[i] if i < j]
    ex, ey = _segments(sc, all_pairs, curved)
    fig.add_trace(go.Scatter(x=ex, y=ey, mode="lines", line=dict(color="rgba(150,150,150,0.25)", width=1), hoverinfo="skip", name="mögliche Paare"))

    if final_pairs is not None:
        px, py = _segments(sc, list(final_pairs), curved)
        fig.add_trace(go.Scatter(x=px, y=py, mode="lines", line=dict(color=C.COLORS["stable"], width=3.5), hoverinfo="skip", name="stabile Paarung"))

    rings = []
    if event is not None:
        color = _EVENT_COLOR.get(event.kind, "#333")
        edges = list(event.pairs) if event.kind in (I.EV_ROTATION_FOUND,) else ([(event.p, event.q)] if event.q >= 0 else [])
        if edges:
            lx, ly = _segments(sc, edges, curved)
            dash = "dash" if event.kind in (I.EV_TRIM_REJECT, I.EV_ROTATION_REJECT, I.EV_ROTATION_FOUND) else None
            fig.add_trace(go.Scatter(x=lx, y=ly, mode="lines", line=dict(color=color, width=5, dash=dash), hoverinfo="skip", name=event.kind))
        if event.p >= 0:
            rings.append((event.p, color))
        if event.q >= 0 and event.kind not in (I.EV_ROTATION_FOUND,):
            rings.append((event.q, color))

    small = sc.n <= 30
    decided = [k for k in range(sc.n) if snap.list_len[k] == 1]
    open_ = [k for k in range(sc.n) if snap.list_len[k] > 1]
    excluded = [k for k in range(sc.n) if snap.list_len[k] == 0]
    for idx, name, color, symbol in ((decided, "entschieden", C.COLORS["stable"], "circle"),
                                      (open_, "noch offen", "#999999", "circle"),
                                      (excluded, "ausgeschlossen", "#d62728", "circle-open")):
        if idx:
            fig.add_trace(go.Scatter(x=[sc.pts[k][0] for k in idx], y=[sc.pts[k][1] for k in idx], mode="markers+text" if small else "markers", name=name,
                                     text=[str(k) for k in idx] if small else None, textposition="top center", hovertext=[f"Person {k}" for k in idx], hoverinfo="text",
                                     marker=dict(symbol=symbol, size=12, color=color, line=dict(width=2, color=color))))
    for k, color in rings:
        pt = sc.pts[k]
        fig.add_trace(go.Scatter(x=[pt[0]], y=[pt[1]], mode="markers", hoverinfo="skip", name="Ereignis", marker=dict(symbol="circle-open", size=26, color=color, line=dict(width=3, color=color))))
    fig = _map_layout(fig, sc, height)
    fig.update_layout(showlegend=False)
    return fig


def build_progress(res, k, height=240):
    """Ueber die Ereignisse: wie viele Listen schon entschieden (Laenge 1) bzw. ausgeschlossen (Laenge 0) sind - beides
    waechst monoton, da Listen nur schrumpfen. Senkrecht der aktuelle Schritt."""
    xs = list(range(res.n_events + 1))
    decided = [sum(1 for x in s.list_len if x == 1) for s in res.snapshots]
    excluded = [sum(1 for x in s.list_len if x == 0) for s in res.snapshots]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=xs, y=decided, mode="lines", name="entschieden", line=dict(color=C.COLORS["stable"], shape="hv")))
    fig.add_trace(go.Scatter(x=xs, y=excluded, mode="lines", name="ausgeschlossen", line=dict(color="#d62728", shape="hv")))
    fig.add_vline(x=k, line=dict(color="#333", width=2))
    fig.update_xaxes(title="Ereignis")
    fig.update_yaxes(title="Personen", rangemode="tozero")
    fig = _base(fig, height)
    fig.update_layout(legend=dict(orientation="h", y=-0.45))
    return fig


def build_reach_sweep(rows, height=320):
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    reaches = [r["reach"] for r in rows]
    fig.add_trace(go.Scatter(x=reaches, y=[100 * r["solvable_share"] for r in rows], mode="lines+markers", name="lösbar [%]", line=dict(color=C.COLORS["stable"])), secondary_y=False)
    fig.add_trace(go.Scatter(x=reaches, y=[r["degree"] for r in rows], mode="lines+markers", name="mittlerer Grad", line=dict(color=C.COLORS["naive"], dash="dot")), secondary_y=True)
    fig.update_xaxes(title="Reichweite [min]")
    fig.update_yaxes(title="Lösbar [%]", secondary_y=False, rangemode="tozero", range=[0, 105])
    fig.update_yaxes(title="Mittlerer Grad", secondary_y=True, rangemode="tozero", showgrid=False)
    fig = _base(fig, height)
    fig.update_layout(legend=dict(orientation="h", y=-0.3), height=height + 40)
    return fig


def build_noise_sweep(rows, height=320):
    fig = go.Figure()
    ks = [r["k"] for r in rows]
    fig.add_trace(go.Scatter(x=ks, y=[100 * r["solvable_share"] for r in rows], mode="lines+markers", name="lösbar [%]", line=dict(color=C.COLORS["stable"])))
    fig.add_trace(go.Scatter(x=ks, y=[100 * r["rotations_share_gt0"] for r in rows], mode="lines+markers", name="mit mindestens einer Rotation [%]", line=dict(color=C.COLORS["rotation"])))
    fig.update_xaxes(title="Streuung k [min] (0 = nur Entfernung)")
    fig.update_yaxes(title="Karten [%]", rangemode="tozero", range=[0, 105])
    fig = _base(fig, height)
    fig.update_layout(legend=dict(orientation="h", y=-0.3), height=height + 40)
    return fig


def build_scale(rows, height=320):
    fig = go.Figure()
    ns = [r["n"] for r in rows]
    fig.add_trace(go.Scatter(x=ns, y=[r["proposals"] for r in rows], mode="lines+markers", name="Vorschläge", line=dict(color=C.COLORS["stable"])))
    fig.update_xaxes(title="Mitbewohner", type="log")
    fig.update_yaxes(title="Vorschläge", type="log")
    fig = _base(fig, height)
    fig.update_layout(legend=dict(orientation="h", y=-0.3), height=height + 40)
    return fig


def build_uniqueness(rows, height=300):
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    ns = [r["n"] for r in rows]
    fig.add_trace(go.Scatter(x=ns, y=[100 * (r["unique_share"] or 0) for r in rows], mode="lines+markers", name="genau 1 stabile Paarung [%]", line=dict(color=C.COLORS["stable"])), secondary_y=False)
    fig.add_trace(go.Scatter(x=ns, y=[r["max_count"] for r in rows], mode="lines+markers", name="höchste beobachtete Anzahl", line=dict(color=C.COLORS["rotation"], dash="dot")), secondary_y=True)
    fig.update_xaxes(title="Mitbewohner")
    fig.update_yaxes(title="Eindeutig [%]", secondary_y=False, rangemode="tozero", range=[0, 105])
    fig.update_yaxes(title="Höchste Anzahl stabiler Paarungen", secondary_y=True, rangemode="tozero", showgrid=False)
    fig = _base(fig, height)
    fig.update_layout(legend=dict(orientation="h", y=-0.3), height=height + 40)
    return fig
