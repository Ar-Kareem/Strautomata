
from math import inf
import time

# Checkers policy for 8x8 American-style movement:
# - black men move toward decreasing row numbers
# - white men move toward increasing row numbers
# - kings move both directions
# - captures are mandatory
# API returns one step from -> to. If a multi-jump is available after this,
# the arena should request the next move from the resulting state.


TIME_LIMIT = 0.88
MAX_DEPTH = 5

DARK = {(r, c) for r in range(8) for c in range(8) if (r + c) % 2 == 1}


def policy(my_men, my_kings, opp_men, opp_kings, color) -> tuple[tuple[int, int], tuple[int, int]]:
    start = time.time()

    my_men = tuple(map(tuple, my_men))
    my_kings = tuple(map(tuple, my_kings))
    opp_men = tuple(map(tuple, opp_men))
    opp_kings = tuple(map(tuple, opp_kings))

    state = (frozenset(my_men), frozenset(my_kings), frozenset(opp_men), frozenset(opp_kings), color)

    moves = legal_moves(state)
    if not moves:
        # Should not happen in normal play; return a syntactically valid fallback from any own piece.
        pieces = list(my_men) + list(my_kings)
        if pieces:
            p = pieces[0]
            return (p, p)
        return ((0, 1), (0, 1))

    # Immediate tactical ordering/fallback.
    best_move = max(moves, key=lambda m: move_heuristic(state, m))

    # Iterative deepening; keep best fully completed result.
    for depth in range(1, MAX_DEPTH + 1):
        try:
            val, mv = alphabeta_root(state, depth, start)
            if mv is not None:
                best_move = mv
        except TimeoutError:
            break

    return (best_move[0], best_move[1])


def in_bounds(sq):
    r, c = sq
    return 0 <= r < 8 and 0 <= c < 8 and ((r + c) & 1) == 1


def man_dirs(color):
    return [(-1, -1), (-1, 1)] if color == 'b' else [(1, -1), (1, 1)]


def all_dirs():
    return [(-1, -1), (-1, 1), (1, -1), (1, 1)]


def opponent_color(color):
    return 'w' if color == 'b' else 'b'


def legal_moves(state):
    my_men, my_kings, opp_men, opp_kings, color = state
    occupied = my_men | my_kings | opp_men | opp_kings
    opp_all = opp_men | opp_kings

    captures = []
    for p in my_men:
        for dr, dc in man_dirs(color):
            mid = (p[0] + dr, p[1] + dc)
            dst = (p[0] + 2 * dr, p[1] + 2 * dc)
            if in_bounds(dst) and mid in opp_all and dst not in occupied:
                captures.append((p, dst))
    for p in my_kings:
        for dr, dc in all_dirs():
            mid = (p[0] + dr, p[1] + dc)
            dst = (p[0] + 2 * dr, p[1] + 2 * dc)
            if in_bounds(dst) and mid in opp_all and dst not in occupied:
                captures.append((p, dst))

    if captures:
        return captures

    moves = []
    for p in my_men:
        for dr, dc in man_dirs(color):
            dst = (p[0] + dr, p[1] + dc)
            if in_bounds(dst) and dst not in occupied:
                moves.append((p, dst))
    for p in my_kings:
        for dr, dc in all_dirs():
            dst = (p[0] + dr, p[1] + dc)
            if in_bounds(dst) and dst not in occupied:
                moves.append((p, dst))
    return moves


def apply_move(state, move):
    my_men, my_kings, opp_men, opp_kings, color = state
    src, dst = move
    dr = dst[0] - src[0]
    is_capture = abs(dr) == 2

    my_men = set(my_men)
    my_kings = set(my_kings)
    opp_men = set(opp_men)
    opp_kings = set(opp_kings)

    moving_king = src in my_kings
    if moving_king:
        my_kings.remove(src)
    else:
        my_men.remove(src)

    if is_capture:
        mid = ((src[0] + dst[0]) // 2, (src[1] + dst[1]) // 2)
        opp_men.discard(mid)
        opp_kings.discard(mid)

    # Promotion.
    promote_row = 0 if color == 'b' else 7
    if moving_king or dst[0] == promote_row:
        my_kings.add(dst)
    else:
        my_men.add(dst)

    # Swap perspective: returned state is for next player to move.
    return (frozenset(opp_men), frozenset(opp_kings),
            frozenset(my_men), frozenset(my_kings),
            opponent_color(color))


def captured_square(move):
    src, dst = move
    if abs(dst[0] - src[0]) == 2:
        return ((src[0] + dst[0]) // 2, (src[1] + dst[1]) // 2)
    return None


def is_attacked_by_opp_after_our_move(state_after_swap, sq):
    # state_after_swap is opponent-to-move perspective.
    # sq is one of our pieces, therefore in opp_* sets in this perspective.
    opp_moves = legal_moves(state_after_swap)
    for m in opp_moves:
        if captured_square(m) == sq:
            return True
    return False


def move_heuristic(state, move):
    my_men, my_kings, opp_men, opp_kings, color = state
    src, dst = move
    score = 0

    is_king = src in my_kings
    is_cap = abs(dst[0] - src[0]) == 2
    if is_cap:
        mid = captured_square(move)
        score += 120
        if mid in opp_kings:
            score += 80
        # Prefer landing where another capture may be possible in real play.
        temp = apply_move_no_swap(state, move)
        cont = legal_captures_for_piece(temp, dst, color)
        score += 25 * len(cont)

    # Promotion and advancement.
    promote_row = 0 if color == 'b' else 7
    if not is_king and dst[0] == promote_row:
        score += 180
    if not is_king:
        score += (src[0] - dst[0]) * 8 if color == 'b' else (dst[0] - src[0]) * 8

    # Center control.
    r, c = dst
    score += 14 - 3 * (abs(3.5 - r) + abs(3.5 - c))

    # Edges are safer but less mobile; small safety bonus.
    if c == 0 or c == 7:
        score += 8

    # Back rank preservation for men.
    back = 7 if color == 'b' else 0
    if src[0] == back and not is_king:
        score -= 15

    # Avoid immediate recapture unless it wins material/promotion.
    after = apply_move(state, move)
    if is_attacked_by_opp_after_our_move(after, dst):
        score -= 70 if not is_king else 110

    return score


def apply_move_no_swap(state, move):
    my_men, my_kings, opp_men, opp_kings, color = state
    src, dst = move
    my_men = set(my_men)
    my_kings = set(my_kings)
    opp_men = set(opp_men)
    opp_kings = set(opp_kings)
    moving_king = src in my_kings

    if moving_king:
        my_kings.remove(src)
    else:
        my_men.remove(src)

    if abs(dst[0] - src[0]) == 2:
        mid = captured_square(move)
        opp_men.discard(mid)
        opp_kings.discard(mid)

    promote_row = 0 if color == 'b' else 7
    if moving_king or dst[0] == promote_row:
        my_kings.add(dst)
    else:
        my_men.add(dst)

    return (frozenset(my_men), frozenset(my_kings), frozenset(opp_men), frozenset(opp_kings), color)


def legal_captures_for_piece(state, piece, color):
    my_men, my_kings, opp_men, opp_kings, _ = state
    occupied = my_men | my_kings | opp_men | opp_kings
    opp_all = opp_men | opp_kings
    dirs = all_dirs() if piece in my_kings else man_dirs(color)
    caps = []
    for dr, dc in dirs:
        mid = (piece[0] + dr, piece[1] + dc)
        dst = (piece[0] + 2 * dr, piece[1] + 2 * dc)
        if in_bounds(dst) and mid in opp_all and dst not in occupied:
            caps.append((piece, dst))
    return caps


def alphabeta_root(state, depth, start):
    moves = legal_moves(state)
    moves.sort(key=lambda m: move_heuristic(state, m), reverse=True)

    alpha = -inf
    beta = inf
    best = None

    for m in moves:
        if time.time() - start > TIME_LIMIT:
            raise TimeoutError
        val = -alphabeta(apply_move(state, m), depth - 1, -beta, -alpha, start)
        if val > alpha:
            alpha = val
            best = m
    return alpha, best


def alphabeta(state, depth, alpha, beta, start):
    if time.time() - start > TIME_LIMIT:
        raise TimeoutError

    moves = legal_moves(state)
    if not moves:
        return -100000

    # Quiescence-like extension for forced tactical capture nodes.
    has_capture = abs(moves[0][1][0] - moves[0][0][0]) == 2
    if depth <= 0 and not has_capture:
        return evaluate(state)

    if depth <= -2:
        return evaluate(state)

    moves.sort(key=lambda m: move_heuristic(state, m), reverse=True)

    best = -inf
    for m in moves:
        val = -alphabeta(apply_move(state, m), depth - 1, -beta, -alpha, start)
        if val > best:
            best = val
        if val > alpha:
            alpha = val
        if alpha >= beta:
            break
    return best


def evaluate(state):
    my_men, my_kings, opp_men, opp_kings, color = state
    score = 0

    # Material.
    score += 100 * (len(my_men) - len(opp_men))
    score += 170 * (len(my_kings) - len(opp_kings))

    # Positional values.
    for p in my_men:
        score += man_pos_value(p, color)
    for p in opp_men:
        score -= man_pos_value(p, opponent_color(color))

    for p in my_kings:
        score += king_pos_value(p)
    for p in opp_kings:
        score -= king_pos_value(p)

    # Mobility.
    score += 4 * len(legal_moves(state))
    opp_state = (opp_men, opp_kings, my_men, my_kings, opponent_color(color))
    score -= 4 * len(legal_moves(opp_state))

    # Tempo / capture availability.
    my_moves = legal_moves(state)
    if my_moves and abs(my_moves[0][1][0] - my_moves[0][0][0]) == 2:
        score += 35
    opp_moves = legal_moves(opp_state)
    if opp_moves and abs(opp_moves[0][1][0] - opp_moves[0][0][0]) == 2:
        score -= 35

    return score


def man_pos_value(p, color):
    r, c = p
    val = 0
    # Advancement toward promotion.
    val += (7 - r) * 8 if color == 'b' else r * 8

    # Center.
    val += int(12 - 2 * (abs(3.5 - r) + abs(3.5 - c)))

    # Edge safety.
    if c == 0 or c == 7:
        val += 5

    # Back row guard.
    back = 7 if color == 'b' else 0
    if r == back:
        val += 12

    # Near promotion.
    promo = 0 if color == 'b' else 7
    if abs(r - promo) <= 1:
        val += 20

    return val


def king_pos_value(p):
    r, c = p
    val = 25
    val += int(16 - 2 * (abs(3.5 - r) + abs(3.5 - c)))
    if c == 0 or c == 7:
        val += 4
    return val
