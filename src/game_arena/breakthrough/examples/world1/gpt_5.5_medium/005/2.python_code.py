
import time
from typing import Optional

# Breakthrough policy for an 8x8 board.
# Public API:
#     policy(me, opp, color) -> ((from_row, from_col), (to_row, to_col))

INF = 10**9
WIN = 10**6

BITS = [1 << i for i in range(64)]
ROW = [i >> 3 for i in range(64)]
COL = [i & 7 for i in range(64)]

DIR = {"b": -1, "w": 1}
OTHER = {"b": "w", "w": "b"}

# Black wins by reaching row 0. White wins by reaching row 7.
GOAL_MASK = {
    "b": sum(BITS[i] for i in range(8)),
    "w": sum(BITS[i] for i in range(56, 64)),
}

CENTER_BONUS = [0, 1, 2, 3, 3, 2, 1, 0]

DEADLINE = 0.0
NODES = 0
TT = {}


class SearchTimeout(Exception):
    pass


def _bb(pieces):
    b = 0
    for r, c in pieces:
        if 0 <= r < 8 and 0 <= c < 8:
            b |= BITS[r * 8 + c]
    return b


def _idx_to_sq(i):
    return (ROW[i], COL[i])


def _move_to_tuple(move):
    f, t = move
    return (_idx_to_sq(f), _idx_to_sq(t))


def _iter_bits(bb):
    while bb:
        lsb = bb & -bb
        idx = lsb.bit_length() - 1
        yield idx
        bb ^= lsb


def _progress(idx, color):
    r = ROW[idx]
    if color == "b":
        return 7 - r
    return r


def _dist_to_goal(idx, color):
    return 7 - _progress(idx, color)


def _terminal_score(me, opp, color) -> Optional[int]:
    oc = OTHER[color]

    # At a side-to-move node, if the opponent already reached its goal,
    # the previous move ended the game.
    if (opp & GOAL_MASK[oc]) or me == 0:
        return -WIN
    if (me & GOAL_MASK[color]) or opp == 0:
        return WIN
    return None


def _generate_moves(me, opp, color):
    """Return legal moves as (from_index, to_index)."""
    occ = me | opp
    d = DIR[color]
    moves = []

    bb = me
    while bb:
        lsb = bb & -bb
        fr = lsb.bit_length() - 1
        bb ^= lsb

        r = ROW[fr]
        c = COL[fr]
        nr = r + d
        if nr < 0 or nr > 7:
            continue

        # Straight forward: only if empty.
        to = nr * 8 + c
        if not (occ & BITS[to]):
            moves.append((fr, to))

        # Diagonal forward: empty or opponent occupied, but not own occupied.
        if c > 0:
            to = nr * 8 + (c - 1)
            if not (me & BITS[to]):
                moves.append((fr, to))
        if c < 7:
            to = nr * 8 + (c + 1)
            if not (me & BITS[to]):
                moves.append((fr, to))

    return moves


def _apply_move(me, opp, move):
    fr, to = move
    fb = BITS[fr]
    tb = BITS[to]
    new_me = (me ^ fb) | tb
    new_opp = opp & ~tb
    return new_me, new_opp


def _is_winning_move(opp, color, move):
    _, to = move
    return (BITS[to] & GOAL_MASK[color]) != 0 or (opp & ~BITS[to]) == 0


def _attack_mask(bb, color):
    d = DIR[color]
    mask = 0

    x = bb
    while x:
        lsb = x & -x
        idx = lsb.bit_length() - 1
        x ^= lsb

        r = ROW[idx]
        c = COL[idx]
        nr = r + d
        if 0 <= nr < 8:
            if c > 0:
                mask |= BITS[nr * 8 + c - 1]
            if c < 7:
                mask |= BITS[nr * 8 + c + 1]

    return mask


def _is_passed(idx, color, opp):
    """A pawn is passed if no enemy pawn is in its forward three-file cone."""
    r = ROW[idx]
    c = COL[idx]
    d = DIR[color]

    rr = r + d
    while 0 <= rr < 8:
        for cc in (c - 1, c, c + 1):
            if 0 <= cc < 8 and (opp & BITS[rr * 8 + cc]):
                return False
        rr += d
    return True


def _static_piece_score(idx, color, enemy):
    prog = _progress(idx, color)
    dist = 7 - prog
    c = COL[idx]

    s = 18 * prog + 4 * prog * prog
    s += 3 * CENTER_BONUS[c]

    # Near-promotion pawns are extremely important in Breakthrough.
    if dist <= 2:
        s += (3 - dist) * 90

    if _is_passed(idx, color, enemy):
        s += 60 + 25 * prog
        if dist <= 2:
            s += 200

    return s


def _evaluate(me, opp, color):
    """Positive means good for side 'color' to move."""
    term = _terminal_score(me, opp, color)
    if term is not None:
        return term

    oc = OTHER[color]

    score = 100 * (me.bit_count() - opp.bit_count())

    my_best = 0
    x = me
    while x:
        lsb = x & -x
        idx = lsb.bit_length() - 1
        x ^= lsb
        p = _progress(idx, color)
        if p > my_best:
            my_best = p
        score += _static_piece_score(idx, color, opp)

    opp_best = 0
    x = opp
    while x:
        lsb = x & -x
        idx = lsb.bit_length() - 1
        x ^= lsb
        p = _progress(idx, oc)
        if p > opp_best:
            opp_best = p
        score -= _static_piece_score(idx, oc, me)

    # Race component: the most advanced pawn often decides the game.
    score += 50 * (my_best - opp_best)

    my_att = _attack_mask(me, color)
    op_att = _attack_mask(opp, oc)

    # Attacks, vulnerabilities, and support.
    score += 30 * ((my_att & opp).bit_count())
    score -= 38 * ((op_att & me).bit_count())
    score += 8 * ((my_att & me).bit_count())
    score -= 8 * ((op_att & opp).bit_count())

    return score


def _move_order_score(move, me, opp, color):
    fr, to = move
    tb = BITS[to]

    if tb & GOAL_MASK[color]:
        return 100000

    score = 10 * _progress(to, color)
    score += CENTER_BONUS[COL[to]]

    if opp & tb:
        oc = OTHER[color]
        # Capturing a more advanced enemy pawn is usually urgent.
        score += 600 + 25 * _progress(to, oc)

    after_opp = opp & ~tb
    if _is_passed(to, color, after_opp):
        score += 90 + 20 * _progress(to, color)

    # Slightly prefer diagonal moves because they create threats and avoid blocks.
    if COL[fr] != COL[to]:
        score += 8

    return score


def _has_immediate_win(me, opp, color):
    for m in _generate_moves(me, opp, color):
        if _is_winning_move(opp, color, m):
            return True
    return False


def _fallback_move(me, opp, color, moves):
    """Fast legal move choice used if search times out."""
    best = moves[0]
    best_val = -INF
    oc = OTHER[color]

    for m in moves:
        if _is_winning_move(opp, color, m):
            return m

        new_me, new_opp = _apply_move(me, opp, m)

        # Evaluation after the move, from our perspective.
        val = -_evaluate(new_opp, new_me, oc)

        # Avoid allowing an immediate opponent promotion if possible.
        if _has_immediate_win(new_opp, new_me, oc):
            val -= WIN // 2

        val += _move_order_score(m, me, opp, color) // 20

        if val > best_val:
            best_val = val
            best = m

    return best


def _negamax(me, opp, color, depth, alpha, beta):
    global NODES, TT

    NODES += 1
    if (NODES & 1023) == 0 and time.perf_counter() > DEADLINE:
        raise SearchTimeout()

    term = _terminal_score(me, opp, color)
    if term is not None:
        return term

    if depth <= 0:
        return _evaluate(me, opp, color)

    key = (me, opp, color, depth)
    entry = TT.get(key)
    if entry is not None:
        stored_depth, stored_val, flag = entry
        if stored_depth >= depth:
            if flag == 0:
                return stored_val
            if flag == 1:
                alpha = max(alpha, stored_val)
            elif flag == -1:
                beta = min(beta, stored_val)
            if alpha >= beta:
                return stored_val

    moves = _generate_moves(me, opp, color)
    if not moves:
        return -WIN + 1

    moves.sort(key=lambda m: _move_order_score(m, me, opp, color), reverse=True)

    orig_alpha = alpha
    orig_beta = beta
    best = -INF
    oc = OTHER[color]

    for m in moves:
        if _is_winning_move(opp, color, m):
            val = WIN + depth
        else:
            new_me, new_opp = _apply_move(me, opp, m)
            val = -_negamax(new_opp, new_me, oc, depth - 1, -beta, -alpha)

        if val > best:
            best = val
        if val > alpha:
            alpha = val
        if alpha >= beta:
            break

    if best <= orig_alpha:
        flag = -1   # upper bound
    elif best >= orig_beta:
        flag = 1    # lower bound
    else:
        flag = 0    # exact

    TT[key] = (depth, best, flag)
    return best


def _search_root(me, opp, color, depth, preferred):
    oc = OTHER[color]
    moves = _generate_moves(me, opp, color)
    if not moves:
        return preferred, -WIN

    def key_fn(m):
        return _move_order_score(m, me, opp, color) + (1000000 if m == preferred else 0)

    moves.sort(key=key_fn, reverse=True)

    best_move = moves[0]
    best_val = -INF
    alpha = -INF
    beta = INF

    for m in moves:
        if time.perf_counter() > DEADLINE:
            raise SearchTimeout()

        if _is_winning_move(opp, color, m):
            val = WIN + depth
        else:
            new_me, new_opp = _apply_move(me, opp, m)
            val = -_negamax(new_opp, new_me, oc, depth - 1, -beta, -alpha)

        if val > best_val:
            best_val = val
            best_move = m

        if val > alpha:
            alpha = val

    return best_move, best_val


def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[tuple[int, int], tuple[int, int]]:
    global DEADLINE, NODES, TT

    me_bb = _bb(me)
    opp_bb = _bb(opp)

    moves = _generate_moves(me_bb, opp_bb, color)

    # In normal Breakthrough play, this should not happen unless the game is
    # already over. Return a syntactically valid tuple as a last resort.
    if not moves:
        if me:
            r, c = me[0]
            return ((r, c), (r, c))
        return ((0, 0), (0, 0))

    # Immediate win.
    for m in moves:
        if _is_winning_move(opp_bb, color, m):
            return _move_to_tuple(m)

    # Always have a legal fallback before starting the timed search.
    fallback = _fallback_move(me_bb, opp_bb, color, moves)
    best_completed = fallback
    preferred = fallback

    TT = {}
    NODES = 0
    DEADLINE = time.perf_counter() + 0.88

    # Iterative deepening. The loop normally stops by timeout.
    try:
        for depth in range(1, 32):
            move, val = _search_root(me_bb, opp_bb, color, depth, preferred)
            best_completed = move
            preferred = move

            # If a forced win is visible, no need to spend more time.
            if val >= WIN:
                break

            if time.perf_counter() > DEADLINE:
                break
    except SearchTimeout:
        pass
    except Exception:
        # Never risk returning an illegal move due to an unexpected error.
        best_completed = fallback

    return _move_to_tuple(best_completed)
