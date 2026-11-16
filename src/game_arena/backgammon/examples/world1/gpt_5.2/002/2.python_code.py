
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple, Optional, Iterable


# ----------------------------
# Helpers: tokens and parsing
# ----------------------------

def _pt_to_token(p: int) -> str:
    return f"A{p}"


def _token_to_pt(tok: str) -> Optional[int]:
    if tok.startswith("A"):
        return int(tok[1:])
    return None


# ----------------------------
# State copy / primitives
# ----------------------------

def _copy_state(state: dict) -> dict:
    return {
        "my_pts": list(state["my_pts"]),
        "opp_pts": list(state["opp_pts"]),
        "my_bar": int(state["my_bar"]),
        "opp_bar": int(state["opp_bar"]),
        "my_off": int(state["my_off"]),
        "opp_off": int(state["opp_off"]),
        "dice": list(state.get("dice", [])),
    }


def _can_bear_off(st: dict) -> bool:
    if st["my_bar"] != 0:
        return False
    # All remaining checkers must be in home board A0..A5
    return sum(st["my_pts"][6:]) == 0


def _my_backmost_point(st: dict) -> int:
    """Highest index with my checker, or 24 if I have any on bar, or -1 if none."""
    if st["my_bar"] > 0:
        return 24
    for i in range(23, -1, -1):
        if st["my_pts"][i] > 0:
            return i
    return -1


def _opp_backmost_point(st: dict) -> int:
    """Lowest index with opponent checker, or -1 if opponent has bar (treat as -1), or 24 if none."""
    # If opponent has checkers on bar, they are "behind everything", so contact definitely exists.
    if st["opp_bar"] > 0:
        return -1
    for i in range(24):
        if st["opp_pts"][i] > 0:
            return i
    return 24


def _is_race(st: dict) -> bool:
    # Race when no contact and nobody on the bar.
    if st["my_bar"] != 0 or st["opp_bar"] != 0:
        return False
    my_back = _my_backmost_point(st)
    opp_back = _opp_backmost_point(st)
    # If my furthest-back checker is in front of opponent's furthest-back checker, we have passed.
    return my_back < opp_back


# ----------------------------
# Move legality + simulation
# ----------------------------

def _entry_dest(die: int) -> int:
    # My bar entry: from "24" downwards by die.
    return 24 - die  # maps die 1..6 to point 23..18


def _is_legal_land(st: dict, dest: int) -> bool:
    return st["opp_pts"][dest] <= 1


def _bearoff_legal_from_point(st: dict, p: int, die: int) -> bool:
    # Only from home board
    if p < 0 or p > 5:
        return False
    if not _can_bear_off(st):
        return False
    # Exact bear off always ok
    if die == p + 1:
        return True
    # Overshoot allowed only if no checkers on higher points (p+1..5)
    if die > p + 1:
        return sum(st["my_pts"][p + 1 : 6]) == 0
    return False


def _legal_from_locations(st: dict, die: int) -> List[str]:
    """Return list of FROM tokens that are legal starts for this single die, given current st."""
    if die < 1 or die > 6:
        return []

    # Must enter from bar if any on bar
    if st["my_bar"] > 0:
        dest = _entry_dest(die)
        if 0 <= dest <= 23 and _is_legal_land(st, dest):
            return ["B"]
        return []

    locs: List[str] = []
    my_pts = st["my_pts"]
    opp_pts = st["opp_pts"]

    can_off = _can_bear_off(st)

    for p in range(24):
        if my_pts[p] <= 0:
            continue
        dest = p - die
        if dest >= 0:
            if opp_pts[dest] <= 1:
                locs.append(_pt_to_token(p))
        else:
            # bearing off attempt
            if can_off and _bearoff_legal_from_point(st, p, die):
                locs.append(_pt_to_token(p))
    return locs


def _apply_one_move(st: dict, from_tok: str, die: int) -> Tuple[Optional[dict], int]:
    """
    Apply a single move (from_tok using die). Return (new_state, hits) or (None, 0) if illegal.
    """
    if from_tok == "P":
        return None, 0

    ns = _copy_state(st)
    my_pts = ns["my_pts"]
    opp_pts = ns["opp_pts"]
    hits = 0

    # Determine source
    if from_tok == "B":
        if ns["my_bar"] <= 0:
            return None, 0
        src = 24
        ns["my_bar"] -= 1
    else:
        p = _token_to_pt(from_tok)
        if p is None or p < 0 or p > 23:
            return None, 0
        if my_pts[p] <= 0:
            return None, 0
        src = p
        my_pts[p] -= 1

    dest = src - die

    if dest >= 0:
        if dest > 23:
            return None, 0
        # Blocked?
        if opp_pts[dest] >= 2:
            return None, 0
        # Hit?
        if opp_pts[dest] == 1:
            opp_pts[dest] = 0
            ns["opp_bar"] += 1
            hits = 1
        my_pts[dest] += 1
        return ns, hits

    # dest < 0 => bearing off
    # Must be moving from a board point, not from bar
    if from_tok == "B":
        return None, 0
    p = src
    if not _bearoff_legal_from_point(ns, p, die):
        return None, 0
    ns["my_off"] += 1
    return ns, hits


@dataclass(frozen=True)
class Action:
    order: str          # 'H' or 'L'
    from1: str          # token
    from2: str          # token or 'P'
    used_high: bool
    used_low: bool
    used_both: bool
    hits: int
    final_state: dict

    def to_string(self) -> str:
        return f"{self.order}:{self.from1},{self.from2}"


def _generate_legal_actions(state: dict) -> List[Action]:
    dice = list(state.get("dice", []))
    if len(dice) == 0:
        return []

    if len(dice) == 1:
        d = dice[0]
        starts = _legal_from_locations(state, d)
        actions: List[Action] = []
        for s in starts:
            ns, h = _apply_one_move(state, s, d)
            if ns is None:
                continue
            actions.append(
                Action(
                    order="H",
                    from1=s,
                    from2="P",
                    used_high=True,
                    used_low=True,   # irrelevant for single die; mark both to avoid filtering issues
                    used_both=False,
                    hits=h,
                    final_state=ns,
                )
            )
        return actions

    # Two dice
    d1, d2 = dice[0], dice[1]
    hi = max(d1, d2)
    lo = min(d1, d2)

    orders = ["H"] if hi == lo else ["H", "L"]
    actions: List[Action] = []

    for order in orders:
        die_first = hi if order == "H" else lo
        die_second = lo if order == "H" else hi

        starts1 = _legal_from_locations(state, die_first)
        for s1 in starts1:
            st1, h1 = _apply_one_move(state, s1, die_first)
            if st1 is None:
                continue
            starts2 = _legal_from_locations(st1, die_second)
            if not starts2:
                # Only first die played
                used_high = (die_first == hi)
                used_low = (die_first == lo)
                actions.append(
                    Action(
                        order=order,
                        from1=s1,
                        from2="P",
                        used_high=used_high,
                        used_low=used_low,
                        used_both=False,
                        hits=h1,
                        final_state=st1,
                    )
                )
            else:
                for s2 in starts2:
                    st2, h2 = _apply_one_move(st1, s2, die_second)
                    if st2 is None:
                        continue
                    actions.append(
                        Action(
                            order=order,
                            from1=s1,
                            from2=s2,
                            used_high=True,
                            used_low=True,
                            used_both=True,
                            hits=h1 + h2,
                            final_state=st2,
                        )
                    )

    # Enforce rules:
    # 1) If any action uses both dice, only those are legal choices.
    both = [a for a in actions if a.used_both]
    if both:
        return both

    # 2) Otherwise, if any action uses the higher die, must choose higher.
    if hi != lo:
        any_high = any(a.used_high and not a.used_both for a in actions)
        if any_high:
            actions = [a for a in actions if a.used_high and not a.used_both]

    return actions


# ----------------------------
# Evaluation
# ----------------------------

def _pip_counts(st: dict) -> Tuple[int, int]:
    my_pip = st["my_bar"] * 25
    opp_pip = st["opp_bar"] * 25

    my_pts = st["my_pts"]
    opp_pts = st["opp_pts"]

    # I move 23->0, so from point i distance is (i+1)
    for i in range(24):
        c = my_pts[i]
        if c:
            my_pip += c * (i + 1)

    # Opp moves 0->23, so from point i distance is (24-i)
    for i in range(24):
        c = opp_pts[i]
        if c:
            opp_pip += c * (24 - i)

    return my_pip, opp_pip


def _count_made_points(pts: List[int], a: int, b: int) -> int:
    return sum(1 for i in range(a, b + 1) if pts[i] >= 2)


def _prime_strength(pts: List[int], a: int, b: int) -> int:
    """Max consecutive made points in [a,b]."""
    best = cur = 0
    for i in range(a, b + 1):
        if pts[i] >= 2:
            cur += 1
            if cur > best:
                best = cur
        else:
            cur = 0
    return best


def _blot_danger(st: dict) -> int:
    """
    Approximate how many of our blots are directly in range (1..6) of any opponent checker behind them.
    Opp moves upward, so an opp checker at q can hit point p if q < p and p-q in 1..6.
    """
    danger = 0
    my_pts = st["my_pts"]
    opp_pts = st["opp_pts"]
    for p in range(24):
        if my_pts[p] == 1:
            lo = max(0, p - 6)
            # any opponent checker on a point that could reach p by 1..6
            if any(opp_pts[q] > 0 for q in range(lo, p)):
                danger += 1
    return danger


def _eval_state(st: dict) -> float:
    my_pip, opp_pip = _pip_counts(st)
    race = _is_race(st)

    my_pts = st["my_pts"]
    opp_pts = st["opp_pts"]

    score = 0.0

    # Big progress terms
    score += 1200.0 * (st["my_off"] - st["opp_off"])
    score += 180.0 * (st["opp_bar"] - st["my_bar"])

    if race:
        # In a race: mostly pip count and bearing off speed.
        score += 6.0 * (opp_pip - my_pip)
        # Slight preference to keep checkers compact in home (fewer big stacks outside home already impossible in race)
        score += 10.0 * _count_made_points(my_pts, 0, 5)
        return score

    # Contact game: include structure + safety.
    score += 2.5 * (opp_pip - my_pip)

    # Home board strength helps when opponent is on bar / in contact
    score += 22.0 * _count_made_points(my_pts, 0, 5)
    score -= 10.0 * _count_made_points(opp_pts, 18, 23)  # their home blocks our re-entry

    # Anchors in opponent home board
    score += 16.0 * _count_made_points(my_pts, 18, 23)

    # Prime building in mid-board
    score += 14.0 * _prime_strength(my_pts, 6, 17)

    # Blots and immediate exposure
    blots = sum(1 for i in range(24) if my_pts[i] == 1)
    score -= 7.0 * blots
    score -= 11.0 * _blot_danger(st)

    return score


# ----------------------------
# Policy
# ----------------------------

def policy(state: dict) -> str:
    """
    Return a legal move string: <ORDER>:<FROM1>,<FROM2>
    Always returns something legal; falls back to pass if nothing is playable.
    """
    dice = list(state.get("dice", []))
    if not dice:
        return "H:P,P"

    actions = _generate_legal_actions(state)

    if not actions:
        return "H:P,P"

    # Choose best by evaluation + tactical hit bonus
    best_a = None
    best_score = None
    for a in actions:
        sc = _eval_state(a.final_state) + 90.0 * a.hits
        # deterministic tie-breakers: prefer using both dice, then order H, then lexical
        tie = (1 if a.used_both else 0, 1 if a.order == "H" else 0, a.from1, a.from2)
        if best_a is None:
            best_a = a
            best_score = (sc, tie)
        else:
            if (sc, tie) > best_score:
                best_a = a
                best_score = (sc, tie)

    if best_a is None:
        return "H:P,P"
    return best_a.to_string()
