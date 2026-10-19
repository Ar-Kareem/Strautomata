
from __future__ import annotations

from typing import List, Tuple, Set
import time
import math

Square = Tuple[int, int]
Move = Tuple[Square, Square]

INF = 10**9


def policy(my_men, my_kings, opp_men, opp_kings, color) -> Move:
    """
    Return a legal move ((from_row, from_col), (to_row, to_col)).
    Captures are mandatory.
    """
    start_time = time.perf_counter()
    time_limit = 0.92  # leave safety margin

    # Convert input into absolute black/white board representation.
    if color == 'b':
        b_men = set(map(tuple, my_men))
        b_kings = set(map(tuple, my_kings))
        w_men = set(map(tuple, opp_men))
        w_kings = set(map(tuple, opp_kings))
        root_side = 'b'
    else:
        w_men = set(map(tuple, my_men))
        w_kings = set(map(tuple, my_kings))
        b_men = set(map(tuple, opp_men))
        b_kings = set(map(tuple, opp_kings))
        root_side = 'w'

    state = (b_men, b_kings, w_men, w_kings, root_side)

    legal = generate_moves(state)
    if not legal:
        # Should not happen in normal play, but return something syntactically valid.
        # We still try to pick one of our squares if any exist.
        mine = list(b_men | b_kings) if root_side == 'b' else list(w_men | w_kings)
        if mine:
            s = mine[0]
            return (s, s)
        return ((0, 1), (0, 1))

    # Fast path if only one legal move.
    if len(legal) == 1:
        return legal[0][0]

    # Dynamic depth choice.
    capture_exists = any(is_capture_move(mv) for mv, _ in legal)
    piece_count = len(b_men) + len(b_kings) + len(w_men) + len(w_kings)
    if piece_count <= 8:
        max_depth = 7
    elif piece_count <= 12:
        max_depth = 6
    elif capture_exists:
        max_depth = 5
    else:
        max_depth = 4

    # Iterative deepening for safety.
    best_move = legal[0][0]
    best_score = -INF

    ordered = order_moves(state, legal, root_side)

    for depth in range(2, max_depth + 1):
        if time.perf_counter() - start_time > time_limit:
            break

        alpha = -INF
        beta = INF
        current_best_move = best_move
        current_best_score = -INF

        for mv, child in ordered:
            if time.perf_counter() - start_time > time_limit:
                break
            score = -alphabeta(
                child,
                depth - 1,
                -beta,
                -alpha,
                opposite(root_side),
                root_side,
                start_time,
                time_limit,
            )
            if score > current_best_score:
                current_best_score = score
                current_best_move = mv
            if score > alpha:
                alpha = score

        if current_best_score > -INF:
            best_score = current_best_score
            best_move = current_best_move
            # Reorder around principal variation for next iteration
            ordered.sort(key=lambda x: 1 if x[0] == best_move else 0, reverse=True)

    return best_move


def opposite(side: str) -> str:
    return 'w' if side == 'b' else 'b'


def in_bounds(r: int, c: int) -> bool:
    return 0 <= r < 8 and 0 <= c < 8


def occupied_sets(state):
    b_men, b_kings, w_men, w_kings, _ = state
    black = b_men | b_kings
    white = w_men | w_kings
    occ = black | white
    return black, white, occ


def piece_dirs(side: str, is_king: bool):
    if is_king:
        return ((1, 1), (1, -1), (-1, 1), (-1, -1))
    if side == 'w':
        return ((1, 1), (1, -1))
    return ((-1, 1), (-1, -1))


def generate_moves(state) -> List[Tuple[Move, tuple]]:
    """
    Generate legal moves for side to move.
    Returns list of (move, child_state), enforcing mandatory captures.
    Single-hop moves/captures only.
    """
    b_men, b_kings, w_men, w_kings, side = state
    black, white, occ = occupied_sets(state)

    if side == 'b':
        my_men, my_kings = b_men, b_kings
        opp_men, opp_kings = w_men, w_kings
        my_occ, opp_occ = black, white
    else:
        my_men, my_kings = w_men, w_kings
        opp_men, opp_kings = b_men, b_kings
        my_occ, opp_occ = white, black

    captures = []
    quiets = []

    # Men
    for sq in my_men:
        r, c = sq
        for dr, dc in piece_dirs(side, False):
            mr, mc = r + dr, c + dc
            tr, tc = r + 2 * dr, c + 2 * dc
            if in_bounds(tr, tc) and (mr, mc) in opp_occ and (tr, tc) not in occ:
                child = apply_move(state, sq, (tr, tc), is_king=False, captured=(mr, mc))
                captures.append(((sq, (tr, tc)), child))
        if not captures:
            for dr, dc in piece_dirs(side, False):
                nr, nc = r + dr, c + dc
                if in_bounds(nr, nc) and (nr, nc) not in occ:
                    child = apply_move(state, sq, (nr, nc), is_king=False, captured=None)
                    quiets.append(((sq, (nr, nc)), child))

    # Kings
    for sq in my_kings:
        r, c = sq
        for dr, dc in piece_dirs(side, True):
            mr, mc = r + dr, c + dc
            tr, tc = r + 2 * dr, c + 2 * dc
            if in_bounds(tr, tc) and (mr, mc) in opp_occ and (tr, tc) not in occ:
                child = apply_move(state, sq, (tr, tc), is_king=True, captured=(mr, mc))
                captures.append(((sq, (tr, tc)), child))
        if not captures:
            for dr, dc in piece_dirs(side, True):
                nr, nc = r + dr, c + dc
                if in_bounds(nr, nc) and (nr, nc) not in occ:
                    child = apply_move(state, sq, (nr, nc), is_king=True, captured=None)
                    quiets.append(((sq, (nr, nc)), child))

    return captures if captures else quiets


def apply_move(state, frm: Square, to: Square, is_king: bool, captured: Square | None):
    b_men, b_kings, w_men, w_kings, side = state

    # Copy sets
    b_men = set(b_men)
    b_kings = set(b_kings)
    w_men = set(w_men)
    w_kings = set(w_kings)

    if side == 'b':
        if is_king:
            b_kings.remove(frm)
        else:
            b_men.remove(frm)
        if captured is not None:
            if captured in w_men:
                w_men.remove(captured)
            else:
                w_kings.remove(captured)

        promote = (not is_king and to[0] == 0)
        if is_king or not promote:
            if is_king:
                b_kings.add(to)
            else:
                b_men.add(to)
        else:
            b_kings.add(to)

    else:  # side == 'w'
        if is_king:
            w_kings.remove(frm)
        else:
            w_men.remove(frm)
        if captured is not None:
            if captured in b_men:
                b_men.remove(captured)
            else:
                b_kings.remove(captured)

        promote = (not is_king and to[0] == 7)
        if is_king or not promote:
            if is_king:
                w_kings.add(to)
            else:
                w_men.add(to)
        else:
            w_kings.add(to)

    return (b_men, b_kings, w_men, w_kings, opposite(side))


def is_capture_move(mv: Move) -> bool:
    (r1, c1), (r2, c2) = mv
    return abs(r2 - r1) == 2 and abs(c2 - c1) == 2


def alphabeta(state, depth, alpha, beta, side_to_move, root_side, start_time, time_limit):
    if time.perf_counter() - start_time > time_limit:
        return evaluate(state, root_side)

    legal = generate_moves(state)
    if depth <= 0 or not legal:
        # No legal moves means side to move loses.
        if not legal:
            return -200000 if state[4] == root_side else 200000
        return quiesce_or_eval(state, alpha, beta, root_side, start_time, time_limit)

    legal = order_moves(state, legal, state[4])

    best = -INF
    for mv, child in legal:
        if time.perf_counter() - start_time > time_limit:
            break
        score = -alphabeta(
            child, depth - 1, -beta, -alpha, opposite(side_to_move),
            root_side, start_time, time_limit
        )
        if score > best:
            best = score
        if score > alpha:
            alpha = score
        if alpha >= beta:
            break

    if best == -INF:
        return evaluate(state, root_side)
    return best


def quiesce_or_eval(state, alpha, beta, root_side, start_time, time_limit):
    stand = evaluate(state, root_side)
    if time.perf_counter() - start_time > time_limit:
        return stand

    legal = generate_moves(state)
    captures = [(mv, child) for mv, child in legal if is_capture_move(mv)]
    if not captures:
        return stand

    if stand >= beta:
        return beta
    if alpha < stand:
        alpha = stand

    captures = order_moves(state, captures, state[4])

    best = stand
    for mv, child in captures:
        if time.perf_counter() - start_time > time_limit:
            break
        score = -quiesce_or_eval(child, -beta, -alpha, root_side, start_time, time_limit)
        if score > best:
            best = score
        if score > alpha:
            alpha = score
        if alpha >= beta:
            break
    return best


def order_moves(state, legal, side):
    def move_key(item):
        mv, child = item
        (r1, c1), (r2, c2) = mv
        capture = 1 if is_capture_move(mv) else 0
        promote = 0
        # promotion check from mover's side
        b_men, b_kings, w_men, w_kings, stm = state
        if side == 'b' and (r1, c1) in b_men and r2 == 0:
            promote = 1
        elif side == 'w' and (r1, c1) in w_men and r2 == 7:
            promote = 1
        center = 3 - abs(3.5 - r2) - abs(3.5 - c2)
        advance = (r1 - r2) if side == 'b' else (r2 - r1)
        return (capture * 100 + promote * 30 + advance * 2 + center)

    return sorted(legal, key=move_key, reverse=True)


def evaluate(state, root_side):
    b_men, b_kings, w_men, w_kings, stm = state

    def side_score(side):
        if side == 'b':
            men, kings = b_men, b_kings
            opp_men, opp_kings = w_men, w_kings
        else:
            men, kings = w_men, w_kings
            opp_men, opp_kings = b_men, b_kings

        score = 0

        # Material
        score += 100 * len(men)
        score += 175 * len(kings)

        # Advancement / promotion pressure for men
        for r, c in men:
            adv = (7 - r) if side == 'b' else r
            score += adv * 7
            if c in (0, 7):
                score += 4
            if 2 <= c <= 5 and 2 <= r <= 5:
                score += 6

        # Kings prefer center and activity
        for r, c in kings:
            score += 12
            if 2 <= c <= 5 and 2 <= r <= 5:
                score += 10

        # Back-rank guard
        home_row = 7 if side == 'b' else 0
        back_guard = sum(1 for (r, c) in men if r == home_row)
        score += 6 * min(back_guard, 3)

        # Mobility
        temp_state = (b_men, b_kings, w_men, w_kings, side)
        mobility = len(generate_moves(temp_state))
        score += 3 * mobility

        # Immediate tactical safety / threats
        vulnerable_self = count_immediate_capturable(temp_state, side)
        vulnerable_opp = count_immediate_capturable(temp_state, opposite(side))
        score -= 18 * vulnerable_self
        score += 14 * vulnerable_opp

        # Promotion-near bonus
        for r, c in men:
            if side == 'b' and r == 1:
                score += 22
            if side == 'w' and r == 6:
                score += 22

        return score

    val = side_score(root_side) - side_score(opposite(root_side))

    # Small tempo bonus
    if stm == root_side:
        val += 4
    else:
        val -= 4

    return val


def count_immediate_capturable(state, target_side):
    """
    Count pieces of target_side that opponent can capture in one move.
    """
    b_men, b_kings, w_men, w_kings, _ = state
    if target_side == 'b':
        my_occ = b_men | b_kings
        opp_side = 'w'
    else:
        my_occ = w_men | w_kings
        opp_side = 'b'

    opp_state = (b_men, b_kings, w_men, w_kings, opp_side)
    opp_moves = generate_moves(opp_state)
    cnt = 0
    seen = set()
    for mv, _ in opp_moves:
        if is_capture_move(mv):
            (r1, c1), (r2, c2) = mv
            mid = ((r1 + r2) // 2, (c1 + c2) // 2)
            if mid in my_occ and mid not in seen:
                seen.add(mid)
                cnt += 1
    return cnt
