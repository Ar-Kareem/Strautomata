
import time
from typing import List, Tuple, Dict

INF = 10**18

# Time budget per call. Keep a safety margin.
TIME_LIMIT = 0.92

# Global timer used by search
_START_TIME = 0.0


def _time_up() -> bool:
    return (time.perf_counter() - _START_TIME) >= TIME_LIMIT


def _legal_moves(you: List[int]) -> List[int]:
    return [i for i in range(6) if you[i] > 0]


def _finalize_if_terminal(you: List[int], opp: List[int]) -> bool:
    """If game ended, sweep remaining seeds into the appropriate store. Return True iff terminal."""
    you_empty = (you[0] | you[1] | you[2] | you[3] | you[4] | you[5]) == 0
    opp_empty = (opp[0] | opp[1] | opp[2] | opp[3] | opp[4] | opp[5]) == 0
    if not you_empty and not opp_empty:
        return False

    if you_empty:
        rem = opp[0] + opp[1] + opp[2] + opp[3] + opp[4] + opp[5]
        if rem:
            opp[6] += rem
            for i in range(6):
                opp[i] = 0
    if opp_empty:
        rem = you[0] + you[1] + you[2] + you[3] + you[4] + you[5]
        if rem:
            you[6] += rem
            for i in range(6):
                you[i] = 0
    return True


def _simulate(you: List[int], opp: List[int], move: int) -> Tuple[List[int], List[int], bool, bool, bool]:
    """
    Apply move for current player.
    Returns:
        new_you, new_opp, extra_turn, terminal, did_capture
    """
    a = you[:]   # current player
    b = opp[:]
    seeds = a[move]
    a[move] = 0

    side = 0   # 0 = current player side, 1 = opponent side
    idx = move + 1
    last_side = None
    last_idx = None
    did_capture = False

    while seeds > 0:
        if side == 0:
            while idx <= 6 and seeds > 0:
                a[idx] += 1
                seeds -= 1
                last_side = 0
                last_idx = idx
                idx += 1
            if seeds == 0:
                break
            side = 1
            idx = 0
        else:
            while idx <= 5 and seeds > 0:  # skip opponent store
                b[idx] += 1
                seeds -= 1
                last_side = 1
                last_idx = idx
                idx += 1
            if seeds == 0:
                break
            side = 0
            idx = 0

    extra_turn = (last_side == 0 and last_idx == 6)

    # Capture rule: last seed lands in your own empty house, opposite has seeds.
    if last_side == 0 and last_idx is not None and 0 <= last_idx <= 5 and a[last_idx] == 1:
        opp_idx = 5 - last_idx
        if b[opp_idx] > 0:
            a[6] += a[last_idx] + b[opp_idx]
            a[last_idx] = 0
            b[opp_idx] = 0
            did_capture = True

    terminal = _finalize_if_terminal(a, b)
    return a, b, extra_turn, terminal, did_capture


def _extra_turn_moves(you: List[int]) -> int:
    cnt = 0
    for i in range(6):
        s = you[i]
        if s <= 0:
            continue
        # Positions on your ring that land in your store:
        # distance to store = 6 - i
        # cycle length excluding opp store = 13
        if s % 13 == (6 - i) % 13:
            cnt += 1
    return cnt


def _capture_potential(you: List[int], opp: List[int]) -> int:
    """
    Rough one-move tactical potential:
    sum of capturable opposite seeds if there exists a move landing in an empty own house.
    """
    pot = 0
    for m in range(6):
        s = you[m]
        if s <= 0:
            continue

        # Simulate only landing location roughly on own side.
        # Because Kalah loops, exact fast calc is messy; we can afford small tactical sim here.
        a, b, _, _, cap = _simulate(you, opp, m)
        if cap:
            pot += a[6] - you[6]
    return pot


def _evaluate(you: List[int], opp: List[int]) -> int:
    """
    Heuristic from side-to-move perspective.
    Positive is good for current player.
    """
    your_houses = you[0] + you[1] + you[2] + you[3] + you[4] + you[5]
    opp_houses = opp[0] + opp[1] + opp[2] + opp[3] + opp[4] + opp[5]
    store_diff = you[6] - opp[6]
    house_diff = your_houses - opp_houses

    # Terminal-like or near-endgame positions: store margin dominates heavily.
    if your_houses == 0 or opp_houses == 0:
        # Exact terminal should already be swept, but this is safe.
        return 10000 * store_diff + 100 * house_diff

    extra_me = _extra_turn_moves(you)
    extra_opp = _extra_turn_moves(opp)

    cap_me = _capture_potential(you, opp)
    cap_opp = _capture_potential(opp, you)

    # Encourage keeping seeds on your side only moderately; stores matter most.
    return (
        120 * store_diff
        + 8 * house_diff
        + 18 * (extra_me - extra_opp)
        + 2 * (cap_me - cap_opp)
    )


def _order_moves(you: List[int], opp: List[int], moves: List[int]) -> List[int]:
    scored = []
    for m in moves:
        a, b, extra, terminal, cap = _simulate(you, opp, m)
        if terminal:
            score = 10**9 + (a[6] - b[6])
        else:
            # Immediate tactical ordering.
            gain = a[6] - you[6]
            score = gain * 1000
            if extra:
                score += 50000
            if cap:
                score += 30000
            # Prefer leaving opponent with fewer seeds / more own seeds.
            score += (sum(a[:6]) - sum(b[:6])) * 10
        scored.append((score, m))
    scored.sort(reverse=True)
    return [m for _, m in scored]


def _negamax(
    you: List[int],
    opp: List[int],
    depth: int,
    alpha: int,
    beta: int,
    tt: Dict[Tuple[Tuple[int, ...], Tuple[int, ...], int], int],
) -> int:
    if _time_up():
        raise TimeoutError

    key = (tuple(you), tuple(opp), depth)
    if key in tt:
        return tt[key]

    # Terminal check
    if (you[0] | you[1] | you[2] | you[3] | you[4] | you[5]) == 0 or \
       (opp[0] | opp[1] | opp[2] | opp[3] | opp[4] | opp[5]) == 0:
        a = you[:]
        b = opp[:]
        _finalize_if_terminal(a, b)
        val = 100000 * (a[6] - b[6])
        tt[key] = val
        return val

    if depth <= 0:
        val = _evaluate(you, opp)
        tt[key] = val
        return val

    moves = _legal_moves(you)
    if not moves:
        a = you[:]
        b = opp[:]
        _finalize_if_terminal(a, b)
        val = 100000 * (a[6] - b[6])
        tt[key] = val
        return val

    best = -INF
    ordered = _order_moves(you, opp, moves)

    for m in ordered:
        a, b, extra, terminal, _ = _simulate(you, opp, m)

        if terminal:
            val = 100000 * (a[6] - b[6])
        elif extra:
            val = _negamax(a, b, depth - 1, alpha, beta, tt)
        else:
            val = -_negamax(b, a, depth - 1, -beta, -alpha, tt)

        if val > best:
            best = val
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break

    tt[key] = best
    return best


def policy(you: List[int], opponent: List[int]) -> int:
    global _START_TIME
    _START_TIME = time.perf_counter()

    legal = _legal_moves(you)
    if not legal:
        return 0  # Should never happen per spec.

    # Safe fallback: strongest immediate ordered move.
    ordered = _order_moves(you, opponent, legal)
    best_move = ordered[0]

    # If only one move, return immediately.
    if len(legal) == 1:
        return best_move

    tt: Dict[Tuple[Tuple[int, ...], Tuple[int, ...], int], int] = {}

    # Iterative deepening
    depth = 1
    try:
        while depth <= 12:
            if _time_up():
                break

            current_best = best_move
            current_best_val = -INF

            # Re-order root moves each iteration; keep prior best first if possible.
            root_moves = _order_moves(you, opponent, legal)
            if best_move in root_moves:
                root_moves.remove(best_move)
                root_moves.insert(0, best_move)

            alpha = -INF
            beta = INF

            for m in root_moves:
                if _time_up():
                    raise TimeoutError

                a, b, extra, terminal, _ = _simulate(you, opponent, m)

                if terminal:
                    val = 100000 * (a[6] - b[6])
                elif extra:
                    val = _negamax(a, b, depth - 1, alpha, beta, tt)
                else:
                    val = -_negamax(b, a, depth - 1, -beta, -alpha, tt)

                if val > current_best_val:
                    current_best_val = val
                    current_best = m
                if val > alpha:
                    alpha = val

            best_move = current_best
            depth += 1

    except TimeoutError:
        pass

    # Absolute legality guarantee
    if 0 <= best_move <= 5 and you[best_move] > 0:
        return best_move
    for m in legal:
        return m
    return 0
