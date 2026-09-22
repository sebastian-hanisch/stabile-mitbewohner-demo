"""Orakel für Tests: Brute Force über alle Paarungen (auch unvollständige), das nichts aus `sr_irving.py` verwendet -
eigenständig hergeleitet, exakt wie `bl_oracle.py` in der Blossom-Demo als unabhängiger Prüfer gedacht.

`stable_roommates_brute(prefs)` sucht rekursiv, Person für Person (aufsteigender Index): für die jeweils nächste noch
nicht entschiedene Person entweder "bleibt frei" oder "wird mit einer noch offenen, erreichbaren Person gepaart" -
sobald eine Entscheidung fällt, wird sie SOFORT gegen alle bereits entschiedenen Personen auf ein blockierendes Paar
geprüft (nicht erst am Ende): das schneidet hoffnungslose Äste früh ab und macht auch den Nachweis der Unlösbarkeit für
kleine n praktikabel. Nur für n <= ~12-14 gedacht (Telefonzahlen: T(12) = 140152, T(14) = 2390480 mögliche Paarungen
ohne die Kürzung - mit ihr in der Praxis deutlich weniger); das ist für Tests ausreichend, in der App läuft nur
`sr_irving.solve`.
"""

from functools import lru_cache

PRACTICAL_MAX_N = 14


def _ranks(prefs):
    return [{x: k for k, x in enumerate(p)} for p in prefs]


def _is_stable(prefs, ranks_, matched, n):
    """Unabhängige Ganzkontrolle: kein Paar (a, b) mit b in a's Liste, a != matched[b], das beide ihrem jetzigen
    Zustand (Partner oder frei) vorziehen. Wird nur einmal je gefundener Lösung aufgerufen (billig), als Absicherung
    gegen einen Fehler in der schrittweisen Kürzung unten."""
    for a in range(n):
        for b in range(a + 1, n):
            if b not in ranks_[a] or matched.get(a) == b:
                continue
            pa, pb = matched.get(a), matched.get(b)
            a_pref = pa is None or ranks_[a][b] < ranks_[a][pa]
            b_pref = pb is None or ranks_[b][a] < ranks_[b][pb]
            if a_pref and b_pref:
                return False
    return True


def stable_roommates_brute(prefs):
    """Irgendeine stabile Paarung (Tupel aus (i, j), i < j) oder None, wenn keine existiert."""
    n = len(prefs)
    ranks_ = _ranks(prefs)
    matched, free_final = {}, set()
    result = [None]

    def is_finalized(x):
        return x in matched or x in free_final

    def blocks(a, b):
        if b not in ranks_[a] or matched.get(a) == b:
            return False
        pa, pb = matched.get(a), matched.get(b)
        a_pref = pa is None or ranks_[a][b] < ranks_[a][pa]
        b_pref = pb is None or ranks_[b][a] < ranks_[b][pb]
        return a_pref and b_pref

    def blocks_any(x, others):
        return any(blocks(x, y) for y in others)

    def backtrack(idx):
        if result[0] is not None:
            return
        if idx == n:
            assert _is_stable(prefs, ranks_, matched, n)
            result[0] = dict(matched)
            return
        a = idx
        if is_finalized(a):
            backtrack(idx + 1)
            return
        prior = [z for z in range(n) if is_finalized(z)]
        free_final.add(a)
        if not blocks_any(a, prior):
            backtrack(idx + 1)
        free_final.discard(a)
        if result[0] is not None:
            return
        for b in range(a + 1, n):
            if is_finalized(b) or b not in ranks_[a]:
                continue
            matched[a] = b
            matched[b] = a
            if not blocks_any(a, prior) and not blocks_any(b, prior):
                backtrack(idx + 1)
            del matched[a]
            del matched[b]
            if result[0] is not None:
                return

    backtrack(0)
    if result[0] is None:
        return None
    return tuple(sorted({(min(i, j), max(i, j)) for i, j in result[0].items()}))


def all_stable_roommates_matchings(prefs, max_n=10):
    """ALLE stabilen Paarungen (nicht nur eine) - deutlich teurer, nur für kleine n (<= max_n) gedacht, z. B. um
    Eindeutigkeit zu prüfen. Rückgabe: sortierte Liste von Paarungs-Tupeln (kann leer sein)."""
    n = len(prefs)
    if n > max_n:
        raise ValueError(f"all_stable_roommates_matchings: n={n} > max_n={max_n}")
    ranks_ = _ranks(prefs)
    matched, free_final, found = {}, set(), []

    def is_finalized(x):
        return x in matched or x in free_final

    def blocks(a, b):
        if b not in ranks_[a] or matched.get(a) == b:
            return False
        pa, pb = matched.get(a), matched.get(b)
        a_pref = pa is None or ranks_[a][b] < ranks_[a][pa]
        b_pref = pb is None or ranks_[b][a] < ranks_[b][pb]
        return a_pref and b_pref

    def blocks_any(x, others):
        return any(blocks(x, y) for y in others)

    def backtrack(idx):
        if idx == n:
            assert _is_stable(prefs, ranks_, matched, n)
            found.append(tuple(sorted({(min(i, j), max(i, j)) for i, j in matched.items()})))
            return
        a = idx
        if is_finalized(a):
            backtrack(idx + 1)
            return
        prior = [z for z in range(n) if is_finalized(z)]
        free_final.add(a)
        if not blocks_any(a, prior):
            backtrack(idx + 1)
        free_final.discard(a)
        for b in range(a + 1, n):
            if is_finalized(b) or b not in ranks_[a]:
                continue
            matched[a] = b
            matched[b] = a
            if not blocks_any(a, prior) and not blocks_any(b, prior):
                backtrack(idx + 1)
            del matched[a]
            del matched[b]

    backtrack(0)
    return sorted(set(found))
