
import time
from math import inf

# Kalah policy:
# - Iterative deepening alpha-beta search under a short time budget
# - Correct handling of extra turns, captures, and terminal sweeping
# - Heuristic evaluation emphasizing store lead, side control, extra-turn chances,
#   capture opportunities, and endgame conversion
# - Always returns a legal move

HOUSES = 6
STORE = 6

# Tuned for 1 second arena limit with safety margin
TIME_LIMIT = 0.92

# Move ordering priority helpers
BIG_NEG = -10**18
BIG_POS = 10**18


def _legal_moves(side):
    return [i for i in range(HOUSES) if side[i] > 0]


def _is_terminal(you, opp):
    return all(v == 0 for v in you[:HOUSES]) or all(v == 0 for v in opp[:HOUSES])


def _finalize_if_terminal(you, opp):
    """Sweep remaining seeds if either side is empty."""
    y_empty = True
    o_empty = True
    for i in range(HOUSES):
        if you[i] != 0:
            y_empty = False
        if opp[i] != 0:
            o_empty = False
    if y_empty or o_empty:
        if not y_empty:
            rem = sum(you[:HOUSES])
            if rem:
                you[STORE] += rem
                for i in range(HOUSES):
                    you[i] = 0
        if not o_empty:
            rem = sum(opp[:HOUSES])
            if rem:
                opp[STORE] += rem
                for i in range(HOUSES):
                    opp[i] = 0
        return True
    return False


def _simulate_move(you, opp, move):
    """
    Returns:
      new_you, new_opp, extra_turn, capture_amount, ended
    State returned is from the current player's perspective after making move.
    If extra_turn is False, caller should swap perspective for next player.
    """
    y = you[:]
    o = opp[:]
    seeds = y[move]
    y[move] = 0
    idx = move
    side = 0  # 0 => y side, 1 => o side

    last_side = None
    last_idx = None

    while seeds > 0:
        idx += 1
        if side == 0:
            if idx == STORE:
                y[STORE] += 1
                seeds -= 1
                last_side = 0
                last_idx = STORE
                if seeds == 0:
                    break
                side = 1
                idx = -1
            elif idx < HOUSES:
                y[idx] += 1
                seeds -= 1
                last_side = 0
                last_idx = idx
                if seeds == 0:
                    break
        else:
            if idx < HOUSES:
                o[idx] += 1
                seeds -= 1
                last_side = 1
                last_idx = idx
                if seeds == 0:
                    break
            elif idx == STORE:
                # skip opponent store
                side = 0
                idx = -1

    capture_amount = 0
    extra_turn = (last_side == 0 and last_idx == STORE)

    if not extra_turn and last_side == 0 and 0 <= last_idx < HOUSES and y[last_idx] == 1:
        opp_idx = 5 - last_idx
        if o[opp_idx] > 0:
            capture_amount = o[opp_idx] + 1
            y[STORE] += capture_amount
            y[last_idx] = 0
            o[opp_idx] = 0

    ended = _finalize_if_terminal(y, o)
    return y, o, extra_turn, capture_amount, ended


def _extra_turn_move(side, move):
    """Cheap test whether move ends in own store."""
    seeds = side[move]
    return ((move + seeds) % 13) == 6


def _capture_potential_now(you, opp):
    """
    Sum immediate capture values available this turn if a move ends in an empty own house.
    This is approximate but exact for current immediate moves.
    """
    total = 0
    for m in range(HOUSES):
        s = you[m]
        if s <= 0:
            continue
        pos = m
        side = 0
        seeds = s
        while seeds > 0:
            pos += 1
            if side == 0:
                if pos == STORE:
                    seeds -= 1
                    if seeds == 0:
                        # store, not capture
                        break
                    side = 1
                    pos = -1
                elif pos < HOUSES:
                    seeds -= 1
                    if seeds == 0:
                        # lands on own house pos
                        if you[pos] == 0 and opp[5 - pos] > 0:
                            total += opp[5 - pos] + 1
                        break
            else:
                if pos < HOUSES:
                    seeds -= 1
                    if seeds == 0:
                        break
                elif pos == STORE:
                    side = 0
                    pos = -1
    return total


def _empty_side_count(side):
    c = 0
    for i in range(HOUSES):
        if side[i] == 0:
            c += 1
    return c


def _eval(you, opp):
    # Terminal exact score
    if _is_terminal(you, opp):
        y = you[STORE] + sum(you[:HOUSES])
        o = opp[STORE] + sum(opp[:HOUSES])
        return 100000 * (y - o)

    y_store = you[STORE]
    o_store = opp[STORE]
    y_houses = sum(you[:HOUSES])
    o_houses = sum(opp[:HOUSES])

    score = 0

    # Primary objective
    score += 120 * (y_store - o_store)

    # Material on board matters, but less than secured store
    score += 18 * (y_houses - o_houses)

    # Shape and tactical motifs
    y_empty = _empty_side_count(you)
    o_empty = _empty_side_count(opp)
    score += 7 * (o_empty - y_empty)

    # Immediate tactical opportunities
    score += 14 * _capture_potential_now(you, opp)
    score -= 13 * _capture_potential_now(opp, you)

    # Extra turn opportunities
    y_extra = sum(1 for m in range(HOUSES) if you[m] > 0 and _extra_turn_move(you, m))
    o_extra = sum(1 for m in range(HOUSES) if opp[m] > 0 and _extra_turn_move(opp, m))
    score += 20 * (y_extra - o_extra)

    # Endgame awareness: when few seeds remain on board, store lead dominates
    rem = y_houses + o_houses
    if rem <= 20:
        score += 22 * (y_store - o_store)
    if rem <= 12:
        score += 35 * (y_store - o_store)

    # Slight preference for seeds closer to store on own side, and farther on opponent side
    for i in range(HOUSES):
        score += (i + 1) * you[i]
        score -= (6 - i) * opp[i]

    return score


def _ordered_moves(you, opp):
    moves = []
    for m in range(HOUSES):
        if you[m] <= 0:
            continue
        y2, o2, extra, cap, ended = _simulate_move(you, opp, m)
        # Strong ordering:
        # terminal-winning moves > extra turns > captures > eval gain
        if ended:
            terminal_margin = y2[STORE] - o2[STORE]
            pri = 10_000_000 + 1000 * terminal_margin
        else:
            base = 0
            if extra:
                base += 200_000
            base += 5000 * cap
            base += 100 * (y2[STORE] - o2[STORE])
            # If turn passes, perspective swaps; evaluate from mover's perspective anyway
            pri = base + _eval(y2, o2)
        moves.append((pri, m))
    moves.sort(reverse=True)
    return [m for _, m in moves]


def _negamax(you, opp, depth, alpha, beta, end_time):
    if time.perf_counter() >= end_time:
        raise TimeoutError

    if depth == 0 or _is_terminal(you, opp):
        return _eval(you, opp)

    best = BIG_NEG
    moves = _ordered_moves(you, opp)
    if not moves:
        # Should not happen for caller, but keep safe
        return _eval(you, opp)

    for m in moves:
        y2, o2, extra, cap, ended = _simulate_move(you, opp, m)

        if ended:
            val = _eval(y2, o2)
        elif extra:
            val = _negamax(y2, o2, depth - 1, alpha, beta, end_time)
        else:
            val = -_negamax(o2, y2, depth - 1, -beta, -alpha, end_time)

        if val > best:
            best = val
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break

    return best


def _choose_fallback(you, opp):
    legal = _legal_moves(you)
    # Prefer extra turn, then biggest capture, then best heuristic one-ply
    best_move = legal[0]
    best_key = None
    for m in legal:
        y2, o2, extra, cap, ended = _simulate_move(you, opp, m)
        key = (
            1 if ended and y2[STORE] > o2[STORE] else 0,
            1 if extra else 0,
            cap,
            y2[STORE] - o2[STORE],
            _eval(y2, o2),
            -m,
        )
        if best_key is None or key > best_key:
            best_key = key
            best_move = m
    return best_move


def policy(you: list[int], opponent: list[int]) -> int:
    legal = _legal_moves(you)
    if not legal:
        return 0  # defensive only; spec says this won't happen
    if len(legal) == 1:
        return legal[0]

    start = time.perf_counter()
    end_time = start + TIME_LIMIT

    # Safe fallback
    best_move = _choose_fallback(you, opponent)

    # Opening shortcut: value extra turns and central-ish accumulation quickly
    total_seeds = sum(you[:HOUSES]) + sum(opponent[:HOUSES])
    if total_seeds >= 36:
        for m in _ordered_moves(you, opponent):
            if _extra_turn_move(you, m):
                return m

    # Iterative deepening
    depth = 1
    try:
        while True:
            if time.perf_counter() >= end_time:
                break

            current_best_move = best_move
            current_best_val = BIG_NEG

            alpha = BIG_NEG
            beta = BIG_POS

            moves = _ordered_moves(you, opponent)
            for m in moves:
                if time.perf_counter() >= end_time:
                    raise TimeoutError

                y2, o2, extra, cap, ended = _simulate_move(you, opponent, m)

                if ended:
                    val = _eval(y2, o2)
                elif extra:
                    val = _negamax(y2, o2, depth - 1, alpha, beta, end_time)
                else:
                    val = -_negamax(o2, y2, depth - 1, -beta, -alpha, end_time)

                if val > current_best_val:
                    current_best_val = val
                    current_best_move = m
                if val > alpha:
                    alpha = val

            best_move = current_best_move
            depth += 1

    except TimeoutError:
        pass

    # Absolute safety: ensure legality
    if 0 <= best_move < HOUSES and you[best_move] > 0:
        return best_move
    return legal[0]
