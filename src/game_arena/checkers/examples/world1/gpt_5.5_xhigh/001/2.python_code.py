
import time

# -----------------------------
# Constants and precomputed data
# -----------------------------

INF = 10**9
MATE = 10**7

MAN_VALUE = 100
KING_VALUE = 185

KING_DIRS = ((1, 1), (1, -1), (-1, 1), (-1, -1))
MAN_STEP = {"b": -1, "w": 1}
OPP_COLOR = {"b": "w", "w": "b"}
PROMOTE_ROW = {"b": 0, "w": 7}
HOME_ROW = {"b": 7, "w": 0}

COORD = [(i >> 3, i & 7) for i in range(64)]
ROW = [i >> 3 for i in range(64)]
COL = [i & 7 for i in range(64)]

KING_SIMPLE = [[] for _ in range(64)]
KING_CAPTURE = [[] for _ in range(64)]
MAN_SIMPLE = {"b": [[] for _ in range(64)], "w": [[] for _ in range(64)]}
MAN_CAPTURE = {"b": [[] for _ in range(64)], "w": [[] for _ in range(64)]}

CENTER_SCORE = [0] * 64
EDGE = [0] * 64

for idx in range(64):
    r, c = COORD[idx]

    CENTER_SCORE[idx] = 14 - (abs(2 * r - 7) + abs(2 * c - 7))
    EDGE[idx] = 1 if c == 0 or c == 7 else 0

    for dr, dc in KING_DIRS:
        r1, c1 = r + dr, c + dc
        if 0 <= r1 < 8 and 0 <= c1 < 8:
            KING_SIMPLE[idx].append((r1 << 3) | c1)

        r2, c2 = r + 2 * dr, c + 2 * dc
        if 0 <= r2 < 8 and 0 <= c2 < 8 and 0 <= r1 < 8 and 0 <= c1 < 8:
            KING_CAPTURE[idx].append(((r1 << 3) | c1, (r2 << 3) | c2))

    for color in ("b", "w"):
        dr = MAN_STEP[color]
        for dc in (-1, 1):
            r1, c1 = r + dr, c + dc
            if 0 <= r1 < 8 and 0 <= c1 < 8:
                MAN_SIMPLE[color][idx].append((r1 << 3) | c1)

            r2, c2 = r + 2 * dr, c + 2 * dc
            if 0 <= r2 < 8 and 0 <= c2 < 8 and 0 <= r1 < 8 and 0 <= c1 < 8:
                MAN_CAPTURE[color][idx].append(((r1 << 3) | c1, (r2 << 3) | c2))


# Move tuple is: (source_index, destination_index, captured_index_or_minus_one)

TT = {}
TT_LIMIT = 120000
DEADLINE = 0.0
NODES = 0


class SearchTimeout(Exception):
    pass


# -----------------------------
# Utility functions
# -----------------------------

def _mask_from_squares(squares):
    mask = 0
    for sq in squares:
        r, c = sq
        r, c = int(r), int(c)
        if 0 <= r < 8 and 0 <= c < 8:
            mask |= 1 << ((r << 3) | c)
    return mask


def _time_check():
    global NODES
    NODES += 1
    if (NODES & 1023) == 0 and time.perf_counter() >= DEADLINE:
        raise SearchTimeout()


def _popcount(x):
    return x.bit_count()


def _opponent(color):
    return "w" if color == "b" else "b"


# -----------------------------
# Legal move generation
# -----------------------------

def _gen_captures(my_men, my_kings, opp_men, opp_kings, color):
    opp = opp_men | opp_kings
    occupied = my_men | my_kings | opp
    moves = []

    men = my_men
    while men:
        b = men & -men
        src = b.bit_length() - 1
        for mid, dst in MAN_CAPTURE[color][src]:
            mb = 1 << mid
            db = 1 << dst
            if (opp & mb) and not (occupied & db):
                moves.append((src, dst, mid))
        men ^= b

    kings = my_kings
    while kings:
        b = kings & -kings
        src = b.bit_length() - 1
        for mid, dst in KING_CAPTURE[src]:
            mb = 1 << mid
            db = 1 << dst
            if (opp & mb) and not (occupied & db):
                moves.append((src, dst, mid))
        kings ^= b

    return moves


def _gen_quiets(my_men, my_kings, opp_men, opp_kings, color):
    occupied = my_men | my_kings | opp_men | opp_kings
    moves = []

    men = my_men
    while men:
        b = men & -men
        src = b.bit_length() - 1
        for dst in MAN_SIMPLE[color][src]:
            if not (occupied & (1 << dst)):
                moves.append((src, dst, -1))
        men ^= b

    kings = my_kings
    while kings:
        b = kings & -kings
        src = b.bit_length() - 1
        for dst in KING_SIMPLE[src]:
            if not (occupied & (1 << dst)):
                moves.append((src, dst, -1))
        kings ^= b

    return moves


def _gen_moves(my_men, my_kings, opp_men, opp_kings, color):
    captures = _gen_captures(my_men, my_kings, opp_men, opp_kings, color)
    if captures:
        return captures
    return _gen_quiets(my_men, my_kings, opp_men, opp_kings, color)


def _has_quiet_move(my_men, my_kings, opp_men, opp_kings, color):
    occupied = my_men | my_kings | opp_men | opp_kings

    men = my_men
    while men:
        b = men & -men
        src = b.bit_length() - 1
        for dst in MAN_SIMPLE[color][src]:
            if not (occupied & (1 << dst)):
                return True
        men ^= b

    kings = my_kings
    while kings:
        b = kings & -kings
        src = b.bit_length() - 1
        for dst in KING_SIMPLE[src]:
            if not (occupied & (1 << dst)):
                return True
        kings ^= b

    return False


# -----------------------------
# Move application
# -----------------------------

def _apply_move(my_men, my_kings, opp_men, opp_kings, color, move):
    src, dst, cap = move
    sb = 1 << src
    db = 1 << dst

    if my_kings & sb:
        my_kings ^= sb
        my_kings |= db
    else:
        my_men ^= sb
        if ROW[dst] == PROMOTE_ROW[color]:
            my_kings |= db
        else:
            my_men |= db

    if cap >= 0:
        cb = 1 << cap
        if opp_men & cb:
            opp_men ^= cb
        else:
            opp_kings ^= cb

    return my_men, my_kings, opp_men, opp_kings


# -----------------------------
# Evaluation
# -----------------------------

def _advancement(color, idx):
    r = ROW[idx]
    if color == "b":
        return 7 - r
    return r


def _distance_to_king(color, idx):
    r = ROW[idx]
    if color == "b":
        return r
    return 7 - r


def _mobility_count(my_men, my_kings, opp_men, opp_kings, color):
    opp = opp_men | opp_kings
    occupied = my_men | my_kings | opp
    count = 0

    men = my_men
    while men:
        b = men & -men
        src = b.bit_length() - 1

        for mid, dst in MAN_CAPTURE[color][src]:
            if (opp & (1 << mid)) and not (occupied & (1 << dst)):
                count += 4

        for dst in MAN_SIMPLE[color][src]:
            if not (occupied & (1 << dst)):
                count += 1

        men ^= b

    kings = my_kings
    while kings:
        b = kings & -kings
        src = b.bit_length() - 1

        for mid, dst in KING_CAPTURE[src]:
            if (opp & (1 << mid)) and not (occupied & (1 << dst)):
                count += 5

        for dst in KING_SIMPLE[src]:
            if not (occupied & (1 << dst)):
                count += 1

        kings ^= b

    return count


def _capture_value(att_men, att_kings, def_men, def_kings, color):
    defenders = def_men | def_kings
    occupied = att_men | att_kings | defenders
    seen = 0
    value = 0

    men = att_men
    while men:
        b = men & -men
        src = b.bit_length() - 1

        for mid, dst in MAN_CAPTURE[color][src]:
            mb = 1 << mid
            if (defenders & mb) and not (occupied & (1 << dst)) and not (seen & mb):
                seen |= mb
                value += KING_VALUE if (def_kings & mb) else MAN_VALUE

        men ^= b

    kings = att_kings
    while kings:
        b = kings & -kings
        src = b.bit_length() - 1

        for mid, dst in KING_CAPTURE[src]:
            mb = 1 << mid
            if (defenders & mb) and not (occupied & (1 << dst)) and not (seen & mb):
                seen |= mb
                value += KING_VALUE if (def_kings & mb) else MAN_VALUE

        kings ^= b

    return value


def _men_positional(mask, color, total_pieces):
    score = 0
    men = mask
    home = HOME_ROW[color]

    while men:
        b = men & -men
        idx = b.bit_length() - 1
        r = ROW[idx]
        c = COL[idx]

        adv = _advancement(color, idx)
        dist = _distance_to_king(color, idx)

        score += 4 * adv
        score += CENTER_SCORE[idx] // 2

        if c == 0 or c == 7:
            score += 4

        if r == home and total_pieces > 12:
            score += 6

        if dist == 1:
            score += 22
        elif dist == 2:
            score += 10

        men ^= b

    return score


def _king_positional(mask, total_pieces):
    score = 0
    kings = mask

    while kings:
        b = kings & -kings
        idx = b.bit_length() - 1

        score += 8
        score += CENTER_SCORE[idx]

        if EDGE[idx]:
            score -= 5

        kings ^= b

    return score


def _evaluate(my_men, my_kings, opp_men, opp_kings, color):
    opp_color = OPP_COLOR[color]

    my_piece_count = _popcount(my_men | my_kings)
    opp_piece_count = _popcount(opp_men | opp_kings)

    if opp_piece_count == 0:
        return MATE // 2
    if my_piece_count == 0:
        return -MATE // 2

    total = my_piece_count + opp_piece_count

    my_men_count = _popcount(my_men)
    my_king_count = _popcount(my_kings)
    opp_men_count = _popcount(opp_men)
    opp_king_count = _popcount(opp_kings)

    # Kings become increasingly important in sparse endgames.
    king_value = KING_VALUE + max(0, 12 - total) * 5

    score = 0
    score += MAN_VALUE * (my_men_count - opp_men_count)
    score += king_value * (my_king_count - opp_king_count)

    score += _men_positional(my_men, color, total)
    score -= _men_positional(opp_men, opp_color, total)

    score += _king_positional(my_kings, total)
    score -= _king_positional(opp_kings, total)

    # Mobility and threats are important, but do not overpower material.
    my_mob = _mobility_count(my_men, my_kings, opp_men, opp_kings, color)
    opp_mob = _mobility_count(opp_men, opp_kings, my_men, my_kings, opp_color)
    score += 3 * (my_mob - opp_mob)

    my_caps = _capture_value(my_men, my_kings, opp_men, opp_kings, color)
    opp_caps = _capture_value(opp_men, opp_kings, my_men, my_kings, opp_color)
    score += (my_caps - opp_caps) // 3

    return score


# -----------------------------
# Move ordering and greedy backup
# -----------------------------

def _move_order_score(move, my_men, my_kings, opp_men, opp_kings, color, tt_move=None):
    src, dst, cap = move
    sb = 1 << src
    is_king = bool(my_kings & sb)

    score = 0

    if tt_move is not None and move == tt_move:
        score += 100000000

    if cap >= 0:
        cb = 1 << cap
        score += 100000
        score += 20 * (KING_VALUE if (opp_kings & cb) else MAN_VALUE)
        score -= KING_VALUE if is_king else MAN_VALUE

        if (not is_king) and ROW[dst] == PROMOTE_ROW[color]:
            score += 25000

        score += 20 * CENTER_SCORE[dst]
        if EDGE[dst]:
            score += 30
    else:
        if (not is_king) and ROW[dst] == PROMOTE_ROW[color]:
            score += 50000

        score += 40 * (CENTER_SCORE[dst] - CENTER_SCORE[src])

        if not is_king:
            score += 100 * (_advancement(color, dst) - _advancement(color, src))
            if _distance_to_king(color, dst) == 1:
                score += 2000

        if EDGE[dst] and not is_king:
            score += 80

    return score


def _ordered_moves(moves, my_men, my_kings, opp_men, opp_kings, color, tt_move=None):
    if len(moves) <= 1:
        return moves

    scored = [
        (_move_order_score(m, my_men, my_kings, opp_men, opp_kings, color, tt_move), m)
        for m in moves
    ]
    scored.sort(key=lambda x: x[0], reverse=True)
    return [m for _, m in scored]


def _static_root_score(move, my_men, my_kings, opp_men, opp_kings, color):
    opp_color = OPP_COLOR[color]
    n_my_men, n_my_kings, n_opp_men, n_opp_kings = _apply_move(
        my_men, my_kings, opp_men, opp_kings, color, move
    )

    if not (n_opp_men | n_opp_kings):
        return MATE

    opp_moves = _gen_moves(n_opp_men, n_opp_kings, n_my_men, n_my_kings, opp_color)
    if not opp_moves:
        return MATE - 1

    score = -_evaluate(n_opp_men, n_opp_kings, n_my_men, n_my_kings, opp_color)

    # Prefer immediate captures and promotions as a safe fallback.
    src, dst, cap = move
    if cap >= 0:
        score += 500
        if opp_kings & (1 << cap):
            score += 250

    if (my_men & (1 << src)) and ROW[dst] == PROMOTE_ROW[color]:
        score += 600

    # Penalize moves where the just-moved piece can be captured immediately.
    opp_caps = _gen_captures(n_opp_men, n_opp_kings, n_my_men, n_my_kings, opp_color)
    if opp_caps:
        dst_bit = 1 << dst
        for _, _, captured in opp_caps:
            if captured == dst:
                score -= KING_VALUE + 80 if (n_my_kings & dst_bit) else MAN_VALUE + 60
                break

    return score


def _greedy_best(moves, my_men, my_kings, opp_men, opp_kings, color):
    best = moves[0]
    best_score = -INF

    for m in moves:
        s = _static_root_score(m, my_men, my_kings, opp_men, opp_kings, color)
        if s > best_score:
            best_score = s
            best = m

    return best


# -----------------------------
# Alpha-beta search
# -----------------------------

def _qsearch(my_men, my_kings, opp_men, opp_kings, color, qdepth, alpha, beta, ply):
    _time_check()

    if not (my_men | my_kings):
        return -MATE + ply
    if not (opp_men | opp_kings):
        return MATE - ply

    captures = _gen_captures(my_men, my_kings, opp_men, opp_kings, color)

    if not captures:
        if not _has_quiet_move(my_men, my_kings, opp_men, opp_kings, color):
            return -MATE + ply
        return _evaluate(my_men, my_kings, opp_men, opp_kings, color)

    if qdepth <= 0:
        return _evaluate(my_men, my_kings, opp_men, opp_kings, color)

    best = -INF
    opp_color = OPP_COLOR[color]

    for move in _ordered_moves(captures, my_men, my_kings, opp_men, opp_kings, color):
        n_my_men, n_my_kings, n_opp_men, n_opp_kings = _apply_move(
            my_men, my_kings, opp_men, opp_kings, color, move
        )

        score = -_qsearch(
            n_opp_men,
            n_opp_kings,
            n_my_men,
            n_my_kings,
            opp_color,
            qdepth - 1,
            -beta,
            -alpha,
            ply + 1,
        )

        if score > best:
            best = score
        if score > alpha:
            alpha = score
        if alpha >= beta:
            break

    return best


def _search(my_men, my_kings, opp_men, opp_kings, color, depth, alpha, beta, ply):
    _time_check()

    if not (my_men | my_kings):
        return -MATE + ply
    if not (opp_men | opp_kings):
        return MATE - ply

    if depth <= 0:
        return _qsearch(my_men, my_kings, opp_men, opp_kings, color, 8, alpha, beta, ply)

    alpha_orig = alpha
    beta_orig = beta
    key = (my_men, my_kings, opp_men, opp_kings, color)
    tt_move = None

    entry = TT.get(key)
    if entry is not None:
        stored_depth, stored_value, stored_flag, stored_move = entry
        tt_move = stored_move
        if stored_depth >= depth:
            if stored_flag == 0:       # exact
                return stored_value
            elif stored_flag == 1:     # lower bound
                if stored_value > alpha:
                    alpha = stored_value
            else:                      # upper bound
                if stored_value < beta:
                    beta = stored_value
            if alpha >= beta:
                return stored_value

    moves = _gen_moves(my_men, my_kings, opp_men, opp_kings, color)
    if not moves:
        return -MATE + ply

    best = -INF
    best_move = moves[0]
    opp_color = OPP_COLOR[color]

    for move in _ordered_moves(moves, my_men, my_kings, opp_men, opp_kings, color, tt_move):
        n_my_men, n_my_kings, n_opp_men, n_opp_kings = _apply_move(
            my_men, my_kings, opp_men, opp_kings, color, move
        )

        score = -_search(
            n_opp_men,
            n_opp_kings,
            n_my_men,
            n_my_kings,
            opp_color,
            depth - 1,
            -beta,
            -alpha,
            ply + 1,
        )

        if score > best:
            best = score
            best_move = move

        if score > alpha:
            alpha = score

        if alpha >= beta:
            break

    if len(TT) < TT_LIMIT:
        if best <= alpha_orig:
            flag = 2   # upper bound
        elif best >= beta_orig:
            flag = 1   # lower bound
        else:
            flag = 0   # exact
        TT[key] = (depth, best, flag, best_move)

    return best


def _max_depth(total_pieces, root_move_count, has_capture):
    if has_capture:
        if total_pieces <= 8:
            return 13
        if total_pieces <= 14:
            return 11
        return 9

    if total_pieces <= 6:
        return 13
    if total_pieces <= 10:
        return 11
    if total_pieces <= 16:
        return 9
    if root_move_count <= 6:
        return 8
    return 7


def _choose_move(my_men, my_kings, opp_men, opp_kings, color, moves):
    global NODES

    fallback = _greedy_best(moves, my_men, my_kings, opp_men, opp_kings, color)
    best_move = fallback
    best_score = -INF

    root_order = sorted(
        moves,
        key=lambda m: _static_root_score(m, my_men, my_kings, opp_men, opp_kings, color),
        reverse=True,
    )

    total_pieces = _popcount(my_men | my_kings | opp_men | opp_kings)
    has_capture = root_order[0][2] >= 0
    max_depth = _max_depth(total_pieces, len(root_order), has_capture)

    opp_color = OPP_COLOR[color]

    for depth in range(1, max_depth + 1):
        try:
            NODES = 0
            alpha = -INF
            beta = INF
            current_best = None
            current_score = -INF

            # Search previous principal variation first.
            if best_move in root_order:
                ordered = [best_move] + [m for m in root_order if m != best_move]
            else:
                ordered = root_order

            for move in ordered:
                _time_check()

                n_my_men, n_my_kings, n_opp_men, n_opp_kings = _apply_move(
                    my_men, my_kings, opp_men, opp_kings, color, move
                )

                score = -_search(
                    n_opp_men,
                    n_opp_kings,
                    n_my_men,
                    n_my_kings,
                    opp_color,
                    depth - 1,
                    -beta,
                    -alpha,
                    1,
                )

                if score > current_score:
                    current_score = score
                    current_best = move

                if score > alpha:
                    alpha = score

            if current_best is not None:
                best_move = current_best
                best_score = current_score

            # If we found a forced win, no need to spend more time.
            if best_score > MATE // 2:
                break

            if time.perf_counter() >= DEADLINE - 0.015:
                break

        except SearchTimeout:
            break

    return best_move


# -----------------------------
# Required API
# -----------------------------

def policy(my_men, my_kings, opp_men, opp_kings, color) -> tuple[tuple[int, int], tuple[int, int]]:
    global DEADLINE, TT

    color = str(color).lower()
    if color not in ("b", "w"):
        color = "b"

    my_men_mask = _mask_from_squares(my_men)
    my_kings_mask = _mask_from_squares(my_kings)
    opp_men_mask = _mask_from_squares(opp_men)
    opp_kings_mask = _mask_from_squares(opp_kings)

    # Avoid pathological memory growth across many arena games.
    if len(TT) > TT_LIMIT:
        TT.clear()

    moves = _gen_moves(my_men_mask, my_kings_mask, opp_men_mask, opp_kings_mask, color)

    # The arena should not call policy when no legal move exists. This fallback
    # is only for robustness in a terminal state.
    if not moves:
        own = list(my_men) + list(my_kings)
        if own:
            r, c = own[0]
            r, c = int(r), int(c)
            return ((r, c), (r, c))
        return ((0, 0), (0, 0))

    if len(moves) == 1:
        src, dst, _ = moves[0]
        return (COORD[src], COORD[dst])

    start = time.perf_counter()
    DEADLINE = start + 0.88

    try:
        best = _choose_move(my_men_mask, my_kings_mask, opp_men_mask, opp_kings_mask, color, moves)
    except Exception:
        # Last-resort safety: still return a legal move.
        best = _greedy_best(moves, my_men_mask, my_kings_mask, opp_men_mask, opp_kings_mask, color)

    src, dst, _ = best
    return (COORD[src], COORD[dst])
