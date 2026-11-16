
import time

INF = 10 ** 9
WIN = 10 ** 7

KING_DIRS = ((1, 1), (1, -1), (-1, 1), (-1, -1))


class _Timeout(Exception):
    pass


def _in_bounds(r, c):
    return 0 <= r < 8 and 0 <= c < 8


def _men_dirs(color):
    # Black moves toward smaller row numbers; white toward larger row numbers.
    if color == "b":
        return ((-1, -1), (-1, 1))
    return ((1, -1), (1, 1))


def _opponent(color):
    return "w" if color == "b" else "b"


def _normalize(pieces):
    return tuple(sorted((int(r), int(c)) for r, c in pieces))


def _generate_moves(bm, bk, wm, wk, turn):
    """Return legal moves for turn. Captures are mandatory."""
    if turn == "b":
        own_men, own_kings = bm, bk
        opp_men, opp_kings = wm, wk
    else:
        own_men, own_kings = wm, wk
        opp_men, opp_kings = bm, bk

    opp_occ = set(opp_men) | set(opp_kings)
    all_occ = set(bm) | set(bk) | set(wm) | set(wk)

    captures = []

    # Men captures.
    for r, c in own_men:
        for dr, dc in _men_dirs(turn):
            mr, mc = r + dr, c + dc
            tr, tc = r + 2 * dr, c + 2 * dc
            if _in_bounds(tr, tc) and (mr, mc) in opp_occ and (tr, tc) not in all_occ:
                captures.append(((r, c), (tr, tc)))

    # King captures.
    for r, c in own_kings:
        for dr, dc in KING_DIRS:
            mr, mc = r + dr, c + dc
            tr, tc = r + 2 * dr, c + 2 * dc
            if _in_bounds(tr, tc) and (mr, mc) in opp_occ and (tr, tc) not in all_occ:
                captures.append(((r, c), (tr, tc)))

    if captures:
        return captures

    moves = []

    # Men quiet moves.
    for r, c in own_men:
        for dr, dc in _men_dirs(turn):
            tr, tc = r + dr, c + dc
            if _in_bounds(tr, tc) and (tr, tc) not in all_occ:
                moves.append(((r, c), (tr, tc)))

    # King quiet moves.
    for r, c in own_kings:
        for dr, dc in KING_DIRS:
            tr, tc = r + dr, c + dc
            if _in_bounds(tr, tc) and (tr, tc) not in all_occ:
                moves.append(((r, c), (tr, tc)))

    return moves


def _apply_move(bm, bk, wm, wk, turn, move):
    (fr, fc), (tr, tc) = move

    bm_set, bk_set = set(bm), set(bk)
    wm_set, wk_set = set(wm), set(wk)

    if turn == "b":
        own_men, own_kings = bm_set, bk_set
        opp_men, opp_kings = wm_set, wk_set
        promotion_row = 0
    else:
        own_men, own_kings = wm_set, wk_set
        opp_men, opp_kings = bm_set, bk_set
        promotion_row = 7

    was_king = (fr, fc) in own_kings

    if was_king:
        own_kings.remove((fr, fc))
    else:
        own_men.remove((fr, fc))

    # Remove captured piece, if any.
    if abs(tr - fr) == 2:
        mr, mc = (fr + tr) // 2, (fc + tc) // 2
        if (mr, mc) in opp_men:
            opp_men.remove((mr, mc))
        elif (mr, mc) in opp_kings:
            opp_kings.remove((mr, mc))

    # Promotion.
    if was_king or tr == promotion_row:
        own_kings.add((tr, tc))
    else:
        own_men.add((tr, tc))

    return (
        tuple(sorted(bm_set)),
        tuple(sorted(bk_set)),
        tuple(sorted(wm_set)),
        tuple(sorted(wk_set)),
        _opponent(turn),
    )


def _is_capture(move):
    return abs(move[0][0] - move[1][0]) == 2


def _move_order_score(move, bm, bk, wm, wk, turn, preferred=None):
    if preferred is not None and move == preferred:
        return 1000000

    (fr, fc), (tr, tc) = move
    score = 0

    if turn == "b":
        own_kings = set(bk)
        opp_kings = set(wk)
        promotion_row = 0
    else:
        own_kings = set(wk)
        opp_kings = set(bk)
        promotion_row = 7

    if _is_capture(move):
        mr, mc = (fr + tr) // 2, (fc + tc) // 2
        score += 10000
        score += 700 if (mr, mc) in opp_kings else 400

    if (fr, fc) not in own_kings and tr == promotion_row:
        score += 2500

    # Prefer central destinations for flexibility.
    score += int(20 - 4 * abs(tr - 3.5) - 4 * abs(tc - 3.5))

    # Edges are often safer for men and sometimes useful for kings.
    if tc == 0 or tc == 7:
        score += 20

    return score


def _order_moves(moves, bm, bk, wm, wk, turn, preferred=None):
    return sorted(
        moves,
        key=lambda m: _move_order_score(m, bm, bk, wm, wk, turn, preferred),
        reverse=True,
    )


def _piece_square_score_men(r, c, color):
    if color == "b":
        advancement = 7 - r
        promotion_dist = r
        back_row = (r == 7)
    else:
        advancement = r
        promotion_dist = 7 - r
        back_row = (r == 0)

    score = 100
    score += 6 * advancement

    # Near-promotion men are tactically important.
    if promotion_dist == 1:
        score += 18
    elif promotion_dist == 2:
        score += 8

    # Center control.
    score += int(8 - 2 * abs(c - 3.5) - abs(r - 3.5))

    # Edge men are harder to capture.
    if c == 0 or c == 7:
        score += 4

    # Back-row guard delays enemy kings.
    if back_row:
        score += 7

    return score


def _piece_square_score_king(r, c):
    score = 180
    # Kings are strongest near the center.
    score += int(16 - 3 * abs(r - 3.5) - 3 * abs(c - 3.5))
    if c == 0 or c == 7:
        score += 2
    return score


def _side_positional_score(men, kings, color):
    score = 0

    men_set = set(men)
    kings_set = set(kings)
    own = men_set | kings_set

    for r, c in men:
        score += _piece_square_score_men(r, c, color)

        # Reward diagonally connected pieces.
        if color == "b":
            defenders = ((r + 1, c - 1), (r + 1, c + 1))
        else:
            defenders = ((r - 1, c - 1), (r - 1, c + 1))
        for d in defenders:
            if d in own:
                score += 3

    for r, c in kings:
        score += _piece_square_score_king(r, c)

    return score


def _evaluate(bm, bk, wm, wk, turn, root_color):
    black_pieces = len(bm) + len(bk)
    white_pieces = len(wm) + len(wk)

    if black_pieces == 0:
        return -WIN if root_color == "b" else WIN
    if white_pieces == 0:
        return WIN if root_color == "b" else -WIN

    black_score = _side_positional_score(bm, bk, "b")
    white_score = _side_positional_score(wm, wk, "w")

    score = black_score - white_score
    if root_color == "w":
        score = -score

    # Mobility and immediate tactical chances.
    root_turn = root_color
    opp_turn = _opponent(root_color)

    root_moves = _generate_moves(bm, bk, wm, wk, root_turn)
    opp_moves = _generate_moves(bm, bk, wm, wk, opp_turn)

    score += 3 * (len(root_moves) - len(opp_moves))

    if root_moves and _is_capture(root_moves[0]):
        score += 25
    if opp_moves and _is_capture(opp_moves[0]):
        score -= 25

    # Slight tempo preference.
    if turn == root_color:
        score += 2
    else:
        score -= 2

    return score


def policy(my_men, my_kings, opp_men, opp_kings, color):
    start = time.perf_counter()
    deadline = start + 0.88

    color = str(color)
    opp_color = _opponent(color)

    my_men = _normalize(my_men)
    my_kings = _normalize(my_kings)
    opp_men = _normalize(opp_men)
    opp_kings = _normalize(opp_kings)

    if color == "b":
        bm, bk, wm, wk = my_men, my_kings, opp_men, opp_kings
    else:
        bm, bk, wm, wk = opp_men, opp_kings, my_men, my_kings

    root_color = color
    root_state = (bm, bk, wm, wk, root_color)

    legal = _generate_moves(bm, bk, wm, wk, root_color)

    # The game engine should not ask for a move if none exists, but keep a
    # defensive fallback anyway.
    if not legal:
        occupied = set(bm) | set(bk) | set(wm) | set(wk)
        pieces = my_kings + my_men
        dirs = KING_DIRS
        for r, c in pieces:
            for dr, dc in dirs:
                tr, tc = r + dr, c + dc
                if _in_bounds(tr, tc) and (tr, tc) not in occupied:
                    return ((r, c), (tr, tc))
        return ((0, 0), (0, 0))

    if len(legal) == 1:
        return legal[0]

    node_counter = [0]
    tt = {}

    def check_time():
        node_counter[0] += 1
        if (node_counter[0] & 1023) == 0 and time.perf_counter() > deadline:
            raise _Timeout()

    def alphabeta(state, depth, alpha, beta, qleft):
        check_time()

        bm0, bk0, wm0, wk0, turn0 = state
        key = (bm0, bk0, wm0, wk0, turn0, depth, qleft, alpha, beta)
        # A conservative exact-cache is used only for identical windows.
        if key in tt:
            return tt[key]

        moves = _generate_moves(bm0, bk0, wm0, wk0, turn0)

        if not moves:
            if turn0 == root_color:
                return -WIN - depth
            return WIN + depth

        # Capture extension at leaf nodes to avoid horizon blunders.
        if depth <= 0:
            if qleft <= 0 or not _is_capture(moves[0]):
                return _evaluate(bm0, bk0, wm0, wk0, turn0, root_color)
            depth = 1
            qleft -= 1

        maximizing = (turn0 == root_color)
        ordered = _order_moves(moves, bm0, bk0, wm0, wk0, turn0)

        if maximizing:
            value = -INF
            completed = True
            for mv in ordered:
                child = _apply_move(bm0, bk0, wm0, wk0, turn0, mv)
                value = max(value, alphabeta(child, depth - 1, alpha, beta, qleft))
                alpha = max(alpha, value)
                if alpha >= beta:
                    completed = False
                    break
            if completed:
                tt[key] = value
            return value
        else:
            value = INF
            completed = True
            for mv in ordered:
                child = _apply_move(bm0, bk0, wm0, wk0, turn0, mv)
                value = min(value, alphabeta(child, depth - 1, alpha, beta, qleft))
                beta = min(beta, value)
                if alpha >= beta:
                    completed = False
                    break
            if completed:
                tt[key] = value
            return value

    # Iterative deepening. Always keep a legal move ready.
    ordered_root = _order_moves(legal, bm, bk, wm, wk, root_color)
    best_move = ordered_root[0]
    best_completed_move = best_move

    max_depth = 12

    for depth in range(1, max_depth + 1):
        if time.perf_counter() > deadline:
            break

        current_best = best_completed_move
        current_value = -INF
        alpha = -INF
        beta = INF

        try:
            root_moves = _order_moves(legal, bm, bk, wm, wk, root_color, preferred=best_completed_move)

            for mv in root_moves:
                if time.perf_counter() > deadline:
                    raise _Timeout()

                child = _apply_move(bm, bk, wm, wk, root_color, mv)
                value = alphabeta(child, depth - 1, alpha, beta, 3)

                if value > current_value:
                    current_value = value
                    current_best = mv

                alpha = max(alpha, current_value)

            best_completed_move = current_best
            best_move = best_completed_move

            # If a forced win is found, no need to spend more time.
            if current_value > WIN // 2:
                break

        except _Timeout:
            break

    return best_move
