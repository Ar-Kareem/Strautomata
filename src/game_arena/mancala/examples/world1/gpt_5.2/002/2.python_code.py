
# kalah_policy.py
from __future__ import annotations

from dataclasses import dataclass
import time
from typing import List, Tuple, Dict, Optional


class _Timeout(Exception):
    pass


# --- Core mechanics (standard 6-house Kalah, skipping opponent store) ---

def _terminal_collect(you: List[int], opp: List[int]) -> bool:
    """If game ended (either side houses empty), sweep remaining seeds to store."""
    s_you = you[0] + you[1] + you[2] + you[3] + you[4] + you[5]
    s_opp = opp[0] + opp[1] + opp[2] + opp[3] + opp[4] + opp[5]
    if s_you == 0 or s_opp == 0:
        if s_you > 0:
            you[6] += s_you
            you[0] = you[1] = you[2] = you[3] = you[4] = you[5] = 0
        if s_opp > 0:
            opp[6] += s_opp
            opp[0] = opp[1] = opp[2] = opp[3] = opp[4] = opp[5] = 0
        return True
    return False


def _apply_move(you: List[int], opp: List[int], mv: int) -> Tuple[List[int], List[int], bool, int]:
    """
    Apply move mv for side 'you' to move.
    Returns (new_you, new_opp, extra_turn, store_gain_for_you).
    """
    you2 = you[:]   # copy
    opp2 = opp[:]   # copy

    seeds = you2[mv]
    you2[mv] = 0
    if seeds <= 0:
        # caller should never do this, but keep safe
        return you2, opp2, False, 0

    store_before = you2[6]

    # Track positions on a 13-slot ring: 0-5 you houses, 6 your store, 7-12 opp houses.
    pos = mv
    # For capture rule, "was empty before the drop" means after pickup, before sowing.
    pre_you = you2[:]  # after pickup

    last_pos = -1
    for _ in range(seeds):
        pos = (pos + 1) % 13
        last_pos = pos
        if pos <= 5:
            you2[pos] += 1
        elif pos == 6:
            you2[6] += 1
        else:
            opp2[pos - 7] += 1

    extra_turn = (last_pos == 6)

    # Capture
    if 0 <= last_pos <= 5:
        if pre_you[last_pos] == 0 and you2[last_pos] == 1:
            opp_idx = 5 - last_pos
            if opp2[opp_idx] > 0:
                you2[6] += opp2[opp_idx] + 1
                opp2[opp_idx] = 0
                you2[last_pos] = 0

    _terminal_collect(you2, opp2)

    store_gain = you2[6] - store_before
    return you2, opp2, extra_turn, store_gain


# --- Evaluation ---

_WEIGHTS_YOU = (1, 2, 3, 4, 5, 6)       # closer to store is better
_WEIGHTS_OPP = (6, 5, 4, 3, 2, 1)       # opp closer to their store (index 5) is better for them


def _tactical_potential(you: List[int], opp: List[int]) -> int:
    """Fast-ish estimate: count extra-turn and capture opportunities (not exact outcome)."""
    pot = 0
    for i in range(6):
        s = you[i]
        if s <= 0:
            continue
        last = (i + s) % 13
        if last == 6:
            pot += 6  # extra turn is big
        elif 0 <= last <= 5:
            # Rough capture check based on current emptiness (ignores intermediate drops),
            # but works well as a heuristic signal.
            if you[last] == 0 and opp[5 - last] > 0:
                pot += 2 + min(8, opp[5 - last])
    return pot


def _evaluate(you: List[int], opp: List[int]) -> int:
    # Terminal positions: after collection, houses may be empty.
    if (you[0] + you[1] + you[2] + you[3] + you[4] + you[5] == 0) or \
       (opp[0] + opp[1] + opp[2] + opp[3] + opp[4] + opp[5] == 0):
        return (you[6] - opp[6]) * 100000

    score = 0

    # Stores dominate.
    score += (you[6] - opp[6]) * 24

    # Positional seed distribution.
    for i in range(6):
        score += _WEIGHTS_YOU[i] * you[i]
        score -= _WEIGHTS_OPP[i] * opp[i]

    # Mobility.
    my_moves = sum(1 for i in range(6) if you[i] > 0)
    op_moves = sum(1 for i in range(6) if opp[i] > 0)
    score += 2 * (my_moves - op_moves)

    # Tactical chances.
    score += _tactical_potential(you, opp)
    score -= _tactical_potential(opp, you)

    return score


# --- Search ---

@dataclass
class _TTEntry:
    depth: int
    value: int


def policy(you: list[int], opponent: list[int]) -> int:
    """
    Return a legal move index 0..5 with you[i] > 0.
    """
    legal = [i for i in range(6) if you[i] > 0]
    if not legal:
        # Per spec, should never happen, but must return something legal-ish.
        return 0
    if len(legal) == 1:
        return legal[0]

    # Time budget per call
    start = time.perf_counter()
    time_limit = 0.95

    # Depth selection: search deeper when fewer seeds remain in houses.
    total_house_seeds = sum(you[:6]) + sum(opponent[:6])
    if total_house_seeds <= 18:
        max_depth = 22
    elif total_house_seeds <= 30:
        max_depth = 18
    elif total_house_seeds <= 42:
        max_depth = 14
    else:
        max_depth = 12

    tt: Dict[Tuple[Tuple[int, ...], Tuple[int, ...]], _TTEntry] = {}

    def check_time():
        if time.perf_counter() - start >= time_limit:
            raise _Timeout

    def negamax(y: List[int], o: List[int], depth: int, alpha: int, beta: int) -> int:
        check_time()

        key = (tuple(y), tuple(o))
        ent = tt.get(key)
        if ent is not None and ent.depth >= depth:
            return ent.value

        # If depth exhausted or terminal
        if depth == 0:
            val = _evaluate(y, o)
            tt[key] = _TTEntry(depth, val)
            return val

        # Terminal positions should already be collected, but evaluate handles it.
        if (y[0] + y[1] + y[2] + y[3] + y[4] + y[5] == 0) or \
           (o[0] + o[1] + o[2] + o[3] + o[4] + o[5] == 0):
            val = _evaluate(y, o)
            tt[key] = _TTEntry(depth, val)
            return val

        moves = [i for i in range(6) if y[i] > 0]

        # Move ordering: simulate once to get tactical sorting + child states.
        children = []
        for mv in moves:
            y2, o2, extra, gain = _apply_move(y, o, mv)
            # Simple priority: extra turn > store gain > capture-like gain.
            pri = 0
            if extra:
                pri += 1000
            pri += 40 * gain
            pri += 2 * (y2[6] - y[6])
            pri += (_tactical_potential(y2, o2) - _tactical_potential(o2, y2))
            children.append((pri, mv, y2, o2, extra))
        children.sort(key=lambda t: t[0], reverse=True)

        best = -10**18
        a = alpha
        for _, mv, y2, o2, extra in children:
            if extra:
                val = negamax(y2, o2, depth - 1, a, beta)
            else:
                val = -negamax(o2, y2, depth - 1, -beta, -a)

            if val > best:
                best = val
            if best > a:
                a = best
            if a >= beta:
                break

        tt[key] = _TTEntry(depth, best)
        return best

    def root_search(depth: int) -> Tuple[int, int]:
        check_time()
        moves = [i for i in range(6) if you[i] > 0]

        # Root ordering
        children = []
        for mv in moves:
            y2, o2, extra, gain = _apply_move(you, opponent, mv)
            pri = 0
            if extra:
                pri += 1000
            pri += 40 * gain
            pri += (_tactical_potential(y2, o2) - _tactical_potential(o2, y2))
            children.append((pri, mv, y2, o2, extra))
        children.sort(key=lambda t: t[0], reverse=True)

        best_val = -10**18
        best_move = children[0][1]
        alpha = -10**18
        beta = 10**18

        for _, mv, y2, o2, extra in children:
            if extra:
                val = negamax(y2, o2, depth - 1, alpha, beta)
            else:
                val = -negamax(o2, y2, depth - 1, -beta, -alpha)

            if val > best_val:
                best_val = val
                best_move = mv
            if best_val > alpha:
                alpha = best_val

        return best_val, best_move

    # Iterative deepening with safe fallback
    fallback = legal[0]
    best_move = fallback
    try:
        for d in range(1, max_depth + 1):
            val, mv = root_search(d)
            best_move = mv
    except _Timeout:
        pass
    except Exception:
        # If anything unexpected happens, still return a legal move.
        return fallback

    # Ensure legal
    if 0 <= best_move <= 5 and you[best_move] > 0:
        return best_move
    return fallback
