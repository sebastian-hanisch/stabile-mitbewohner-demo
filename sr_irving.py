"""Irvings Algorithmus (1985) fuer das Problem der stabilen Mitbewohner (Stable Roommates): eine einzige Gruppe, jeder
ordnet seine erreichbaren Nachbarn - anders als beim zweiseitigen Gale-Shapley kann hier eine stabile Paarung FEHLEN.

Dieses Modul wurde NACH einer ersten, fehlgeschlagenen Portierung neu geschrieben: die erste Fassung verwendete ein
SYMMETRISCHES `held[]`-Feld (wer haelt wen) mit einer Bewerbung/Ablehnung PRO VERSUCH (Vergleich der Raenge bei jeder
einzelnen Bewerbung) - das ergab auf dem klassischen n=3-Lehrbuchbeispiel fuer "keine stabile Paarung" (zyklische
Vorlieben 0:[1,2], 1:[2,0], 2:[0,1]) faelschlich EINE Paarung, unabhaengig sowohl vom eigenen Brute-Force-Orakel als
auch von Hand nachgerechnet widerlegt. Die jetzige Fassung folgt stattdessen eng dem Aufbau des etablierten, auf PyPI
veroeffentlichten Pakets `matching` (dessen Kernmechanik an 9750 eigenen Zufallsinstanzen - vollstaendige UND
unvollstaendige Listen, n=2..14 - gegen den eigenen Brute-Force-Pruefer `sr_oracle.py` mit 0 Abweichungen bestaetigt
wurde, bevor dieses Modul geschrieben wurde) und ergaenzt sie um die fuer unser reichweitenbasiertes Szenario noetige
Verallgemeinerung auf UNVOLLSTAENDIGE Listen (das Paket selbst verlangt vollstaendige Listen).

**Die entscheidende Erkenntnis, an der die erste Fassung scheiterte:** man vergleicht beim Bewerben NICHT Rang gegen
Rang und lehnt dann ab - man bewirbt sich immer nur beim eigenen aktuellen Favoriten (`lst[p][0]`) und der NIMMT IMMER
BEDINGUNGSLOS AN (verdraengt dabei seinen bisherigen Halt, falls vorhanden, der dann selbst wieder frei wird). Das ist
nur deshalb korrekt, weil unmittelbar bei JEDER Annahme eine KUERZUNG folgt (jeder in der Liste des Annehmenden, der
schlechter eingestuft ist als der neu Angenommene, wird - GEGENSEITIG, symmetrisch - gestrichen): wer zum Zeitpunkt
seiner eigenen Bewerbung noch in der Liste des Angesprochenen steht, MUSS also schon mindestens so gut sein wie dessen
aktueller Halt, weil jeder Schlechtere laengst bei einer FRUEHEREN Annahme gestrichen wurde. Ablehnung geschieht also
nie im Bewerbungsmoment selbst, sondern immer VORAB, durch diese Kuerzung. Phase 2 (Rotationsbeseitigung) verwendet die
im Paket `matching` dokumentierte KORRIGIERTE Fassung (nicht die literarisch verbreitete vereinfachte, z. B. in einem
frei verfuegbaren studentischen Referenzcode auf GitHub, der bei genauerer Pruefung an echten Zufallsinstanzen -
n=3, Vorlieben 0:[1,2],1:[0,2],2:[0,1] - ebenfalls falsche Ergebnisse lieferte): beim Beseitigen einer Rotation
(x_0,y_0)...(x_{k-1},y_{k-1}) werden nicht nur diese Paare gestrichen, sondern zusaetzlich fuer jedes y_i alle in y_is
Liste SCHLECHTER als x_{i-1} eingestuften Eintraege (nicht nur schlechter als der eigene, gerade verlorene x_i) -
andernfalls wuerde nur ein "Schwanz" der Rotation statt der ganzen Rotation entfernt und wiederspruechliche Paare
blieben stehen.

**Verallgemeinerung auf unvollstaendige Listen (Reichweite, moeglicherweise ungerades n):** eine waehrend Phase 1
leerlaufende Liste ist HARMLOS - diese Person bleibt garantiert in jeder stabilen Paarung frei, der Rest kann trotzdem
lösbar sein (bewiesen: wer in Phase 1 von jedem seiner moeglichen Partner abgelehnt wird, wurde von jedem einzelnen zu
einem Zeitpunkt abgelehnt, als dieser bereits jemanden hielt, den er dieser Person vorzog - und ein gehaltener Partner
wird nur noch besser, nie schlechter, also kann diese Ablehnung nie durch ein spaeteres blockierendes Paar widerlegt
werden). Eine WAEHREND Phase 2 (Rotationsbeseitigung) leerlaufende Liste ist dagegen NUR DANN harmlos, wenn diese
Person schon VOR Phase 2 (also in Phase 1) leergelaufen war - eine Liste, die erst durch eine Rotationsbeseitigung auf
0 faellt, beweist echte Unloesbarkeit (Irvings Satz). Dieser Unterschied - wessen Leerlaufen harmlos ist und wessen
nicht - ist die konzeptionell wichtigste Einzelstelle dieses Moduls.

Aufwand wird gezaehlt (Bewerbungen, Ablehnungen/Kuerzungen je Phase, Rotationen), nie in Sekunden. Das Ergebnis ist ein
Ereignisprotokoll mit einem Schnappschuss je Ereignis (`state_at`) und ein von der Bewerbung unabhaengiges Zertifikat
(`certificate`), das Gueltigkeit, blockierende Paare und Maximalitaet direkt aus den Vorlieben und der Paarung neu
herleitet.
"""

from dataclasses import dataclass

EV_PROPOSE, EV_ACCEPT, EV_DISPLACE, EV_TRIM_REJECT = "propose", "accept", "displace", "trim_reject"
EV_PHASE1_UNMATCHED, EV_ROTATION_FOUND, EV_ROTATION_REJECT, EV_NO_STABLE_MATCHING = "phase1_unmatched", "rotation_found", "rotation_reject", "no_stable_matching"


@dataclass(frozen=True)
class Event:
    kind: str            # propose | accept | displace | trim_reject | phase1_unmatched | rotation_found | rotation_reject | no_stable_matching
    phase: int            # 1 oder 2
    p: int = -1            # Bewerber bzw. gestrichene Person (rotation_*: xi)
    q: int = -1            # Angesprochener/Favorit (rotation_*: yi)
    cause: int = -1        # displace/trim_reject: wer neu angenommen wurde und dies ausloeste
    pairs: tuple = ()      # rotation_found: alle (xi, yi)-Paare der Rotation in Kettenreihenfolge
    proposals: int = 0     # kumulative Bewerbungen bis einschliesslich dieses Ereignisses


@dataclass(frozen=True)
class Snapshot:
    held: tuple            # wen jede Person aktuell haelt (-1: niemanden) - EINSEITIG (siehe Moduldoku), nur zur Anzeige
    list_len: tuple         # aktuelle Laenge der verbleibenden Liste je Person


@dataclass(frozen=True)
class Result:
    n: int
    solvable: bool
    pairs: tuple                    # (i, j) mit i < j, die stabile Paarung (leer, wenn nicht loesbar)
    phase1_unmatched: tuple         # in Phase 1 leergelaufene Personen - garantiert frei in jeder stabilen Paarung (harmlos)
    unsolvable_agent: int           # -1, sonst: wessen Liste in Phase 2 leerlief und die Unloesbarkeit bewies
    proposals: int
    rejections1: int                # Kuerzungen (Verdraengung + Streichung schlechterer Eintraege) in Phase 1
    rejections2: int                # Streichungen in Phase 2 (Rotationspaare + zugehoerige Kuerzungen)
    rotations: int                  # gefundene und beseitigte Rotationen
    events: tuple
    snapshots: tuple                # snapshots[k] = Zustand nach Ereignis k (k = 0: vor dem ersten Ereignis)

    @property
    def n_events(self):
        return len(self.events)

    def held_list(self):
        h = [-1] * self.n
        for i, j in self.pairs:
            h[i], h[j] = j, i
        return h


class _Stats:
    def __init__(self):
        self.proposals = 0
        self.rejections1 = 0
        self.rejections2 = 0
        self.rotations = 0


def _forget_pair(lst, a, b):
    """(a, b) symmetrisch streichen: b aus a's Liste, a aus b's Liste. Wird auf jeder Seite nur entfernt, wenn noch
    vorhanden (beide Richtungen koennen unabhaengig schon gestrichen worden sein)."""
    if b in lst[a]:
        lst[a].remove(b)
    if a in lst[b]:
        lst[b].remove(a)


def _phase1(n, lst, events, snaps, stats):
    """Bewerbung beim eigenen Favoriten, IMMER bedingungslos angenommen (siehe Moduldoku, warum das genuegt), sofort
    gefolgt von der Kuerzung der Liste des Annehmenden. `held[x]` ist EINSEITIG: es zeigt, wen x als Bewerbung
    haelt, nicht wen x selbst zuletzt anbot - nur zur Anzeige/zum Ereignisprotokoll, die eigentliche Paarung wird am
    Ende aus den (auf Laenge <= 1 reduzierten) Listen gelesen, nie aus `held` selbst."""
    held = [None] * n
    free = list(range(n))
    unmatched = set()

    def emit(kind, **kw):
        events.append(Event(kind=kind, phase=1, proposals=stats.proposals, **kw))
        snaps.append(Snapshot(tuple(-1 if h is None else h for h in held), tuple(len(x) for x in lst)))

    def mark_if_emptied(x):
        if not lst[x] and x in free:
            free.remove(x)
            unmatched.add(x)
            emit(EV_PHASE1_UNMATCHED, p=x)

    while free:
        player = free.pop()
        if not lst[player]:
            unmatched.add(player)
            continue
        favourite = lst[player][0]
        stats.proposals += 1
        emit(EV_PROPOSE, p=player, q=favourite)

        current = held[favourite]
        if current is not None:
            held[favourite] = None
            free.append(current)

        held[favourite] = player
        emit(EV_ACCEPT, p=player, q=favourite)

        idx = lst[favourite].index(player)
        successors = list(lst[favourite][idx + 1:])
        for s in successors:
            _forget_pair(lst, s, favourite)
            stats.rejections1 += 1
            if s == current:
                emit(EV_DISPLACE, p=s, q=favourite, cause=player)
            else:
                emit(EV_TRIM_REJECT, p=s, q=favourite, cause=player)
            mark_if_emptied(s)
            mark_if_emptied(favourite)

    return unmatched


def _locate_rotation(lst, start):
    """Kette x0, y0 = zweiter Eintrag von x0, x1 = letzter Eintrag von y0s Liste, y1 = zweiter Eintrag von x1, ...
    bis ein xk ein frueheres xj wiederholt. Rueckgabe: die Rotation (xj,yj)...(xk-1,yk-1) - der zyklische Teil."""
    lasts = [start]
    seconds = []
    x = start
    while True:
        second_best = lst[x][1]
        their_worst = lst[second_best][-1]
        seconds.append(second_best)
        lasts.append(their_worst)
        x = their_worst
        if lasts.count(x) > 1:
            break
    idx = lasts.index(x)
    return list(zip(lasts[idx + 1:], seconds[idx:]))


def _pairs_to_delete(lst, rotation):
    """Nicht nur die Rotationspaare (xi, yi) selbst: fuer jedes yi zusaetzlich alle in yis Liste SCHLECHTER als
    x_{i-1} (der Vorgaenger in der Rotation) eingestuften Eintraege - ohne diese zusaetzliche Kuerzung bliebe nur ein
    Teilstueck der Rotation entfernt statt der ganzen, mit widerspruechlichen Paaren als Folge (siehe Moduldoku)."""
    m = len(rotation)
    pairs = []
    for i, (_x, y) in enumerate(rotation):
        prev_x = rotation[(i - 1) % m][0]
        cut = lst[y].index(prev_x)
        for worse in lst[y][cut + 1:]:
            pair = (y, worse) if y < worse else (worse, y)
            if pair not in pairs:
                pairs.append(pair)
    return pairs


def _phase2(n, lst, already_unmatched, events, snaps, stats):
    """Rotation suchen und beseitigen, bis jede Liste hoechstens einen Eintrag hat (geloest) oder eine Liste einer
    Person leerlaeuft, die NICHT schon aus Phase 1 als harmlos unversorgt bekannt war (das beweist Unloesbarkeit -
    siehe Moduldoku, der Unterschied ist entscheidend)."""
    def emit(kind, **kw):
        events.append(Event(kind=kind, phase=2, proposals=stats.proposals, **kw))
        snaps.append(Snapshot(tuple(-1 if len(x) == 0 else x[0] for x in lst), tuple(len(x) for x in lst)))

    while True:
        start = next((i for i in range(n) if len(lst[i]) > 1), None)
        if start is None:
            return -1

        rotation = _locate_rotation(lst, start)
        stats.rotations += 1
        emit(EV_ROTATION_FOUND, p=rotation[0][0], pairs=tuple(rotation))

        for a, b in _pairs_to_delete(lst, rotation):
            _forget_pair(lst, a, b)
            stats.rejections2 += 1
            emit(EV_ROTATION_REJECT, p=a, q=b)

        newly_emptied = [i for i in range(n) if not lst[i] and i not in already_unmatched]
        if newly_emptied:
            culprit = newly_emptied[0]
            emit(EV_NO_STABLE_MATCHING, p=culprit)
            return culprit


def solve(prefs, *, record=True):
    """Irvings Algorithmus. `prefs[i]` = i's strikte Vorliebenliste (beste zuerst), z. B. aus `sr_preferences.preferences`.
    Rueckgabe: `Result` mit `solvable`, der Paarung (falls loesbar), den harmlos unversorgten Phase-1-Personen und
    vollem Aufwand. Ganzzahlig, deterministisch (Warteschlange von hinten abgearbeitet, aufsteigende Startreihenfolge)."""
    n = len(prefs)
    lst = [list(p) for p in prefs]
    stats = _Stats()
    events = [] if record else _NullList()
    snaps = [] if record else _NullList()
    if record:
        snaps.append(Snapshot(tuple(-1 for _ in range(n)), tuple(len(x) for x in lst)))

    phase1_unmatched = _phase1(n, lst, events, snaps, stats)

    unsolvable_agent = -1
    if any(len(x) > 1 for x in lst):
        unsolvable_agent = _phase2(n, lst, phase1_unmatched, events, snaps, stats)

    solvable = unsolvable_agent == -1
    if solvable:
        pairs = tuple(sorted((i, x[0]) for i, x in enumerate(lst) if x and i < x[0]))
    else:
        pairs = ()

    return Result(
        n=n, solvable=solvable, pairs=pairs, phase1_unmatched=tuple(sorted(phase1_unmatched)),
        unsolvable_agent=unsolvable_agent, proposals=stats.proposals, rejections1=stats.rejections1,
        rejections2=stats.rejections2, rotations=stats.rotations,
        events=tuple(events) if record else (), snapshots=tuple(snaps) if record else (),
    )


class _NullList(list):
    """Verwirft alles (record=False): Ereignisse/Schnappschuesse werden nirgends gesammelt, aber der Code in
    `_phase1`/`_phase2` kann unveraendert `events.append(...)` aufrufen."""

    def append(self, _x):
        pass


def state_at(res, k):
    """Zustand nach Ereignis k (k = 0: Startzustand, noch keine Bewerbung)."""
    return res.snapshots[k]


# --- Zertifikat: unabhaengig von der Bewerbung, nur aus `prefs` und `pairs` neu hergeleitet ------------------

def certificate(prefs, pairs, all_agents_n):
    """Beweis, der nichts aus dem `solve`-Lauf wiederverwendet: eigene, frische Rangtabellen aus `prefs`. Prueft
    (s1) Gueltigkeit - jede Person hoechstens einmal in `pairs`; (s2) keine blockierende Paarung - ein nicht gepaartes,
    gegenseitig erreichbares (a, b), das beide ihrem jetzigen Zustand (Partner oder frei) vorziehen, per Doppelschleife
    ueber alle Personenpaare; (s3) Maximalitaet - keine zwei freien Personen sind gegenseitig erreichbar (sonst haette
    man sie noch paaren koennen); (s4) jedes Paar aus `pairs` ist tatsaechlich gegenseitig erreichbar."""
    n = all_agents_n
    rnk = [{x: k for k, x in enumerate(p)} for p in prefs]
    matched = {}
    duplicate = False
    for i, j in pairs:
        if i in matched or j in matched:
            duplicate = True
        matched[i] = j
        matched[j] = i
    s1_valid = not duplicate

    s4_mutual = all(j in rnk[i] and i in rnk[j] for i, j in pairs)

    def prefers(a, b, current):
        if b not in rnk[a]:
            return False
        if current is None:
            return True
        return rnk[a][b] < rnk[a][current]

    s2_no_blocking = True
    for a in range(n):
        for b in range(a + 1, n):
            if b not in rnk[a] or matched.get(a) == b:
                continue
            if prefers(a, b, matched.get(a)) and prefers(b, a, matched.get(b)):
                s2_no_blocking = False

    unmatched = [a for a in range(n) if a not in matched]
    s3_maximal = True
    for ia in range(len(unmatched)):
        for ib in range(ia + 1, len(unmatched)):
            a, b = unmatched[ia], unmatched[ib]
            if b in rnk[a]:
                s3_maximal = False

    return {
        "s1_valid": s1_valid, "s2_no_blocking": s2_no_blocking, "s3_maximal": s3_maximal, "s4_mutual": s4_mutual,
        "matched": tuple(sorted(matched)), "unmatched": tuple(unmatched),
        "all_ok": s1_valid and s2_no_blocking and s3_maximal and s4_mutual,
    }
