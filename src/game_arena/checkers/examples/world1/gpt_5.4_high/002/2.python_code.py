
from __future__ import annotations

import time

# Assumes standard 8x8 checkers movement:
# - men move diagonally forward by 1
# - men capture diagonally forward by 2
# - kings move/capture diagonally in all 4 directions by 1/2
# - captures are mandatory
#
# The arena API asks for a single (from, to) move.

BLACK = 0
WHITE = 1

INF = 10**9
MATE = 10**6

TIME_BUDGET = 0.90

EXACT = 0
LOWER = 1
UPPER = 2

ROWS = [sq >> 3 for sq in range(64)]
COLS = [sq & 7 for sq in range(64)]

PROMO_ROW = [0, 7]

MAN_MOVES = [[[ ] for _ in range(64)] for _ in range(2)]
MAN_CAPS = [[[ ] for _ in range(64)] for _ in range(2)]
KING_MOVES = [[] for _ in range(64)]
KING_CAPS = [[] for _ in range(64)]

VULN_TO_BLACK = [[] for _ in range(64)]  # black piece vulnerable to white
VULN_TO_WHITE = [[] for _ in range(64)]  # white piece vulnerable to black

MAN_PST = [0] * 64
KING_PST = [0] * 64

TT: dict[tuple[int, int, int, int, int], tuple[int, int, int, tuple | None]] = {}
HISTORY: dict[tuple[int, int, int], int] = {}

DEADLINE = 0.0
NODES = 0


def _on_board(r: int, c: int) -> bool:
    return 0 <= r < 8 and 0 <= c < 8


def _build_tables() -> None:
    black_dirs = [(-1, -1), (-1, 1)]
    white_dirs = [(1, -1), (1, 1)]
    king_dirs = [(-1, -1), (-1, 1), (1, -1), (1, 1)]

    for sq in range(64):
        r = ROWS[sq]
        c = COLS[sq]

        # Men moves/captures
        for dr, dc in black_dirs:
            r1, c1 = r + dr, c + dc
            r2, c2 = r + 2 * dr, c + 2 * dc
            if _on_board(r1, c1):
                MAN_MOVES[BLACK][sq].append(r1 * 8 + c1)
            if _on_board(r2, c2):
                MAN_CAPS[BLACK][sq].append((r1 * 8 + c1, r2 * 8 + c2))

        for dr, dc in white_dirs:
            r1, c1 = r + dr, c + dc
            r2, c2 = r + 2 * dr, c + 2 * dc
            if _on_board(r1, c1):
                MAN_MOVES[WHITE][sq].append(r1 * 8 + c1)
            if _on_board(r2, c2):
                MAN_CAPS[WHITE][sq].append((r1 * 8 + c1, r2 * 8 + c2))

        # Kings
        for dr, dc in king_dirs:
            r1, c1 = r + dr, c + dc
            r2, c2 = r + 2 * dr, c + 2 * dc
            if _on_board(r1, c1):
                KING_MOVES[sq].append(r1 * 8 + c1)
            if _on_board(r2, c2):
                KING_CAPS[sq].append((r1 * 8 + c1, r2 * 8 + c2))

        # Vulnerability patterns:
        # target black -> white attackers
        cand_b = [
            (r - 1, c - 1, r + 1, c + 1, 1, 1),
            (r - 1, c + 1, r + 1, c - 1, 1, 1),
            (r + 1, c - 1, r - 1, c + 1, 0, 1),
            (r + 1, c + 1, r - 1, c - 1, 0, 1),
        ]
        lst = []
        for ar, ac, lr, lc, man_ok, king_ok in cand_b:
            if _on_board(ar, ac) and _on_board(lr, lc):
                lst.append((ar * 8 + ac, lr * 8 + lc, man_ok, king_ok))
        VULN_TO_BLACK[sq] = lst

        # target white -> black attackers
        cand_w = [
            (r + 1, c - 1, r - 1, c + 1, 1, 1),
            (r + 1, c + 1, r - 1, c - 1, 1, 1),
            (r - 1, c - 1, r + 1, c + 1, 0, 1),
            (r - 1, c + 1, r + 1, c - 1, 0, 1),
        ]
        lst = []
        for ar, ac, lr, lc, man_ok, king_ok in cand_w:
            if _on_board(ar, ac) and _on_board(lr, lc):
                lst.append((ar * 8 + ac, lr * 8 + lc, man_ok, king_ok))
        VULN_TO_WHITE[sq] = lst

        # Piece-square tables
        man_ps = 0
        if 2 <= r <= 5 and 2 <= c <= 5:
            man_ps += 4
        elif 1 <= r <= 6 and 1 <= c <= 6:
            man_ps += 2
        if c == 0 or c == 7:
            man_ps += 2
        MAN_PST[sq] = man_ps

        king_ps = 0
        if 2 <= r <= 5 and 2 <= c <= 5:
            king_ps += 10
        elif 1 <= r <= 6 and 1 <= c <= 6:
            king_ps += 5
        if r in (0, 7) or c in (0, 7):
            king_ps -= 2
        KING_PST[sq] = king_ps


_build_tables()

try:
    int.bit_count
    def popcount(x: int) -> int:
        return x.bit_count()
except AttributeError:
    def popcount(x: int) -> int:
        return bin(x).count("1")


def iter_bits(bb: int):
    while bb:
        lsb = bb & -bb
        yield lsb.bit_length() - 1
        bb ^= lsb


def coords_to_bb(coords) -> int:
    bb = 0
    for r, c in coords:
        bb |= 1 << (r * 8 + c)
    return bb


def rc_from_sq(sq: int) -> tuple[int, int]:
    return (ROWS[sq], COLS[sq])


def count_attackers_black(sq: int, occupied: int, wm: int, wk: int) -> int:
    cnt = 0
    for att, land, man_ok, king_ok in VULN_TO_BLACK[sq]:
        if (occupied >> land) & 1:
            continue
        if man_ok and ((wm >> att) & 1):
            cnt += 1
        elif king_ok and ((wk >> att) & 1):
            cnt += 1
    return cnt


def count_attackers_white(sq: int, occupied: int, bm: int, bk: int) -> int:
    cnt = 0
    for att, land, man_ok, king_ok in VULN_TO_WHITE[sq]:
        if (occupied >> land) & 1:
            continue
        if man_ok and ((bm >> att) & 1):
            cnt += 1
        elif king_ok and ((bk >> att) & 1):
            cnt += 1
    return cnt


# Move tuple:
# (from_sq, to_sq, cap_sq, mover_is_king, captured_is_king, promote)
def generate_moves(bm: int, bk: int, wm: int, wk: int, side: int) -> list[tuple[int, int, int, int, int, int]]:
    occupied = bm | bk | wm | wk

    if side == BLACK:
        my_men, my_kings = bm, bk
        opp_men, opp_kings = wm, wk
    else:
        my_men, my_kings = wm, wk
        opp_men, opp_kings = bm, bk

    opp_all = opp_men | opp_kings
    promo_row = PROMO_ROW[side]

    caps = []

    for sq in iter_bits(my_men):
        for mid, to in MAN_CAPS[side][sq]:
            if ((opp_all >> mid) & 1) and not ((occupied >> to) & 1):
                caps.append(
                    (
                        sq,
                        to,
                        mid,
                        0,
                        1 if ((opp_kings >> mid) & 1) else 0,
                        1 if ROWS[to] == promo_row else 0,
                    )
                )

    for sq in iter_bits(my_kings):
        for mid, to in KING_CAPS[sq]:
            if ((opp_all >> mid) & 1) and not ((occupied >> to) & 1):
                caps.append(
                    (
                        sq,
                        to,
                        mid,
                        1,
                        1 if ((opp_kings >> mid) & 1) else 0,
                        0,
                    )
                )

    if caps:
        return caps

    quiet = []

    for sq in iter_bits(my_men):
        for to in MAN_MOVES[side][sq]:
            if not ((occupied >> to) & 1):
                quiet.append(
                    (
                        sq,
                        to,
                        -1,
                        0,
                        0,
                        1 if ROWS[to] == promo_row else 0,
                    )
                )

    for sq in iter_bits(my_kings):
        for to in KING_MOVES[sq]:
            if not ((occupied >> to) & 1):
                quiet.append((sq, to, -1, 1, 0, 0))

    return quiet


def apply_move(
    bm: int, bk: int, wm: int, wk: int, side: int, move: tuple[int, int, int, int, int, int]
) -> tuple[int, int, int, int, int]:
    frm, to, cap, mover_is_king, captured_is_king, promote = move

    from_mask = 1 << frm
    to_mask = 1 << to

    if side == BLACK:
        if mover_is_king:
            bk = (bk ^ from_mask) | to_mask
        else:
            bm ^= from_mask
            if promote:
                bk |= to_mask
            else:
                bm |= to_mask

        if cap != -1:
            cap_mask = 1 << cap
            if captured_is_king:
                wk ^= cap_mask
            else:
                wm ^= cap_mask
    else:
        if mover_is_king:
            wk = (wk ^ from_mask) | to_mask
        else:
            wm ^= from_mask
            if promote:
                wk |= to_mask
            else:
                wm |= to_mask

        if cap != -1:
            cap_mask = 1 << cap
            if captured_is_king:
                bk ^= cap_mask
            else:
                bm ^= cap_mask

    return bm, bk, wm, wk, side ^ 1


def move_order_score(move: tuple[int, int, int, int, int, int], tt_move, side: int) -> int:
    frm, to, cap, mover_is_king, captured_is_king, promote = move

    score = 0
    if tt_move is not None and move == tt_move:
        score += 1_000_000

    score += HISTORY.get((side, frm, to), 0)

    if cap != -1:
        score += 50_000
        if captured_is_king:
            score += 10_000
        else:
            score += 4_000
        if promote:
            score += 7_000
        score += (KING_PST[to] if (mover_is_king or promote) else MAN_PST[to]) * 10
    else:
        if promote:
            score += 30_000
        score += (KING_PST[to] if mover_is_king else MAN_PST[to]) * 10
        if side == BLACK:
            score += (ROWS[frm] - ROWS[to]) * 50
        else:
            score += (ROWS[to] - ROWS[frm]) * 50

    return score


def order_moves(moves: list[tuple[int, int, int, int, int, int]], tt_move, side: int):
    if len(moves) > 1:
        moves.sort(key=lambda m: move_order_score(m, tt_move, side), reverse=True)
    return moves


def evaluate(bm: int, bk: int, wm: int, wk: int, side: int) -> int:
    occupied = bm | bk | wm | wk
    total_pieces = popcount(occupied)

    black_men_n = popcount(bm)
    white_men_n = popcount(wm)
    black_kings_n = popcount(bk)
    white_kings_n = popcount(wk)

    king_val = 190 if total_pieces > 8 else 205
    mobility_wt = 2 if total_pieces > 10 else 3

    black_score = 0
    white_score = 0
    black_mob = 0
    white_mob = 0
    black_threat = 0
    white_threat = 0

    black_all = bm | bk
    white_all = wm | wk

    # Black men
    for sq in iter_bits(bm):
        r = ROWS[sq]
        s = 100 + 6 * (7 - r) + MAN_PST[sq]

        if white_men_n and r == 7:
            s += 6
        if r == 1:
            s += 12
        elif r == 2:
            s += 4

        atk = count_attackers_black(sq, occupied, wm, wk)
        if atk:
            s -= 16 * atk

        black_score += s

        for to in MAN_MOVES[BLACK][sq]:
            if not ((occupied >> to) & 1):
                black_mob += 1
                if ROWS[to] == 0:
                    black_score += 10

        for mid, to in MAN_CAPS[BLACK][sq]:
            if ((white_all >> mid) & 1) and not ((occupied >> to) & 1):
                black_threat += 1 + (1 if ((wk >> mid) & 1) else 0) + (1 if ROWS[to] == 0 else 0)

    # White men
    for sq in iter_bits(wm):
        r = ROWS[sq]
        s = 100 + 6 * r + MAN_PST[sq]

        if black_men_n and r == 0:
            s += 6
        if r == 6:
            s += 12
        elif r == 5:
            s += 4

        atk = count_attackers_white(sq, occupied, bm, bk)
        if atk:
            s -= 16 * atk

        white_score += s

        for to in MAN_MOVES[WHITE][sq]:
            if not ((occupied >> to) & 1):
                white_mob += 1
                if ROWS[to] == 7:
                    white_score += 10

        for mid, to in MAN_CAPS[WHITE][sq]:
            if ((black_all >> mid) & 1) and not ((occupied >> to) & 1):
                white_threat += 1 + (1 if ((bk >> mid) & 1) else 0) + (1 if ROWS[to] == 7 else 0)

    # Black kings
    for sq in iter_bits(bk):
        s = king_val + KING_PST[sq]
        atk = count_attackers_black(sq, occupied, wm, wk)
        if atk:
            s -= 24 * atk
        black_score += s

        for to in KING_MOVES[sq]:
            if not ((occupied >> to) & 1):
                black_mob += 1

        for mid, to in KING_CAPS[sq]:
            if ((white_all >> mid) & 1) and not ((occupied >> to) & 1):
                black_threat += 2 + (2 if ((wk >> mid) & 1) else 0)

    # White kings
    for sq in iter_bits(wk):
        s = king_val + KING_PST[sq]
        atk = count_attackers_white(sq, occupied, bm, bk)
        if atk:
            s -= 24 * atk
        white_score += s

        for to in KING_MOVES[sq]:
            if not ((occupied >> to) & 1):
                white_mob += 1

        for mid, to in KING_CAPS[sq]:
            if ((black_all >> mid) & 1) and not ((occupied >> to) & 1):
                white_threat += 2 + (2 if ((bk >> mid) & 1) else 0)

    score = black_score - white_score
    score += mobility_wt * (black_mob - white_mob)
    score += 6 * (black_threat - white_threat)

    material_diff = (100 * black_men_n + king_val * black_kings_n) - (100 * white_men_n + king_val * white_kings_n)
    if material_diff > 0:
        score += (24 - total_pieces) * 2
    elif material_diff < 0:
        score -= (24 - total_pieces) * 2

    return score if side == BLACK else -score


class Timeout(Exception):
    pass


def maybe_timeout() -> None:
    global NODES
    NODES += 1
    if (NODES & 1023) == 0 and time.perf_counter() >= DEADLINE:
        raise Timeout


def quiescence(bm: int, bk: int, wm: int, wk: int, side: int, alpha: int, beta: int, qdepth: int = 8) -> int:
    maybe_timeout()

    moves = generate_moves(bm, bk, wm, wk, side)
    if not moves:
        return -MATE

    # If no captures are available, the position is quiet enough.
    if moves[0][2] == -1 or qdepth <= 0:
        return evaluate(bm, bk, wm, wk, side)

    order_moves(moves, None, side)

    best = -INF
    next_side = side ^ 1

    for move in moves:
        nbm, nbk, nwm, nwk, _ = apply_move(bm, bk, wm, wk, side, move)
        score = -quiescence(nbm, nbk, nwm, nwk, next_side, -beta, -alpha, qdepth - 1)

        if score > best:
            best = score
        if score > alpha:
            alpha = score
        if alpha >= beta:
            break

    return best


def search(bm: int, bk: int, wm: int, wk: int, side: int, depth: int, alpha: int, beta: int) -> int:
    maybe_timeout()

    if depth <= 0:
        return quiescence(bm, bk, wm, wk, side, alpha, beta)

    key = (bm, bk, wm, wk, side)
    alpha_orig = alpha
    beta_orig = beta

    tt_entry = TT.get(key)
    tt_move = None
    if tt_entry is not None:
        tt_depth, tt_flag, tt_score, tt_move = tt_entry
        if tt_depth >= depth:
            if tt_flag == EXACT:
                return tt_score
            if tt_flag == LOWER:
                if tt_score > alpha:
                    alpha = tt_score
            elif tt_flag == UPPER:
                if tt_score < beta:
                    beta = tt_score
            if alpha >= beta:
                return tt_score

    moves = generate_moves(bm, bk, wm, wk, side)
    if not moves:
        return -MATE

    order_moves(moves, tt_move, side)

    best_score = -INF
    best_move = moves[0]
    next_side = side ^ 1

    for i, move in enumerate(moves):
        nbm, nbk, nwm, nwk, _ = apply_move(bm, bk, wm, wk, side, move)

        if i == 0:
            score = -search(nbm, nbk, nwm, nwk, next_side, depth - 1, -beta, -alpha)
        else:
            score = -search(nbm, nbk, nwm, nwk, next_side, depth - 1, -alpha - 1, -alpha)
            if alpha < score < beta:
                score = -search(nbm, nbk, nwm, nwk, next_side, depth - 1, -beta, -alpha)

        if score > best_score:
            best_score = score
            best_move = move

        if score > alpha:
            alpha = score

        if alpha >= beta:
            HISTORY[(side, move[0], move[1])] = HISTORY.get((side, move[0], move[1]), 0) + depth * depth
            break

    flag = EXACT
    if best_score <= alpha_orig:
        flag = UPPER
    elif best_score >= beta_orig:
        flag = LOWER

    TT[key] = (depth, flag, best_score, best_move)
    return best_score


def root_search(bm: int, bk: int, wm: int, wk: int, side: int, depth: int):
    key = (bm, bk, wm, wk, side)
    tt_entry = TT.get(key)
    tt_move = tt_entry[3] if tt_entry is not None else None

    moves = generate_moves(bm, bk, wm, wk, side)
    if not moves:
        return -MATE, None

    order_moves(moves, tt_move, side)

    alpha = -INF
    beta = INF
    best_score = -INF
    best_move = moves[0]
    next_side = side ^ 1

    for i, move in enumerate(moves):
        maybe_timeout()
        nbm, nbk, nwm, nwk, _ = apply_move(bm, bk, wm, wk, side, move)

        if i == 0:
            score = -search(nbm, nbk, nwm, nwk, next_side, depth - 1, -beta, -alpha)
        else:
            score = -search(nbm, nbk, nwm, nwk, next_side, depth - 1, -alpha - 1, -alpha)
            if alpha < score < beta:
                score = -search(nbm, nbk, nwm, nwk, next_side, depth - 1, -beta, -alpha)

        if score > best_score:
            best_score = score
            best_move = move

        if score > alpha:
            alpha = score

    TT[key] = (depth, EXACT, best_score, best_move)
    return best_score, best_move


def policy(my_men, my_kings, opp_men, opp_kings, color) -> tuple[tuple[int, int], tuple[int, int]]:
    global DEADLINE, NODES, HISTORY

    if len(TT) > 200000:
        TT.clear()

    HISTORY = {}
    NODES = 0
    DEADLINE = time.perf_counter() + TIME_BUDGET

    side = BLACK if color == 'b' else WHITE

    if side == BLACK:
        bm = coords_to_bb(my_men)
        bk = coords_to_bb(my_kings)
        wm = coords_to_bb(opp_men)
        wk = coords_to_bb(opp_kings)
    else:
        wm = coords_to_bb(my_men)
        wk = coords_to_bb(my_kings)
        bm = coords_to_bb(opp_men)
        bk = coords_to_bb(opp_kings)

    moves = generate_moves(bm, bk, wm, wk, side)

    # Should not happen in normal play, but avoid crashing.
    if not moves:
        if my_men:
            return my_men[0], my_men[0]
        if my_kings:
            return my_kings[0], my_kings[0]
        return (0, 0), (0, 0)

    order_moves(moves, None, side)
    best_move = moves[0]

    if len(moves) == 1:
        return rc_from_sq(best_move[0]), rc_from_sq(best_move[1])

    total_pieces = popcount(bm | bk | wm | wk)
    if total_pieces <= 6:
        max_depth = 18
    elif total_pieces <= 10:
        max_depth = 16
    else:
        max_depth = 14

    depth = 1
    try:
        while depth <= max_depth:
            score, move = root_search(bm, bk, wm, wk, side, depth)
            if move is not None:
                best_move = move
            depth += 1
    except Timeout:
        pass

    return rc_from_sq(best_move[0]), rc_from_sq(best_move[1])
