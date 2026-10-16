
from __future__ import annotations

import time

INF = 10**9
MATE = 10**6

DIRS_B = ((-1, -1), (-1, 1))
DIRS_W = ((1, -1), (1, 1))
DIRS_K = ((-1, -1), (-1, 1), (1, -1), (1, 1))

# Transposition table: key -> (depth, flag, value, best_move)
# flag: 0 exact, 1 lowerbound, 2 upperbound
_TT: dict[tuple[int, int, int, int, str], tuple[int, int, int, tuple | None]] = {}


class SearchTimeout(Exception):
    pass


def _idx(r: int, c: int) -> int:
    return (r << 3) | c


def _rc(i: int) -> tuple[int, int]:
    return (i >> 3, i & 7)


def _list_to_bb(squares: list[tuple[int, int]]) -> int:
    bb = 0
    for r, c in squares:
        bb |= 1 << _idx(r, c)
    return bb


def _iter_bits(bb: int):
    while bb:
        lsb = bb & -bb
        i = lsb.bit_length() - 1
        yield i
        bb ^= lsb


def _generate_moves(
    bm: int, bk: int, wm: int, wk: int, turn: str
) -> list[tuple[int, int, int, bool, bool, bool]]:
    """
    Move tuple:
      (from_idx, to_idx, captured_idx, captured_is_king, promotes, mover_is_king)
    captured_idx == -1 for non-captures.
    """
    if turn == "b":
        own_m, own_k = bm, bk
        opp_occ, opp_k = wm | wk, wk
        man_dirs = DIRS_B
    else:
        own_m, own_k = wm, wk
        opp_occ, opp_k = bm | bk, bk
        man_dirs = DIRS_W

    occ = bm | bk | wm | wk
    captures: list[tuple[int, int, int, bool, bool, bool]] = []
    simples: list[tuple[int, int, int, bool, bool, bool]] = []

    # Men
    for frm in _iter_bits(own_m):
        r, c = frm >> 3, frm & 7
        for dr, dc in man_dirs:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 8 and 0 <= nc < 8:
                nidx = _idx(nr, nc)
                nmask = 1 << nidx
                if (occ & nmask) == 0:
                    promotes = (turn == "b" and nr == 0) or (turn == "w" and nr == 7)
                    simples.append((frm, nidx, -1, False, promotes, False))
                elif opp_occ & nmask:
                    jr, jc = nr + dr, nc + dc
                    if 0 <= jr < 8 and 0 <= jc < 8:
                        jidx = _idx(jr, jc)
                        jmask = 1 << jidx
                        if (occ & jmask) == 0:
                            promotes = (turn == "b" and jr == 0) or (turn == "w" and jr == 7)
                            capk = bool(opp_k & nmask)
                            captures.append((frm, jidx, nidx, capk, promotes, False))

    # Kings
    for frm in _iter_bits(own_k):
        r, c = frm >> 3, frm & 7
        for dr, dc in DIRS_K:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 8 and 0 <= nc < 8:
                nidx = _idx(nr, nc)
                nmask = 1 << nidx
                if (occ & nmask) == 0:
                    simples.append((frm, nidx, -1, False, False, True))
                elif opp_occ & nmask:
                    jr, jc = nr + dr, nc + dc
                    if 0 <= jr < 8 and 0 <= jc < 8:
                        jidx = _idx(jr, jc)
                        jmask = 1 << jidx
                        if (occ & jmask) == 0:
                            capk = bool(opp_k & nmask)
                            captures.append((frm, jidx, nidx, capk, False, True))

    return captures if captures else simples


def _apply_move(
    bm: int,
    bk: int,
    wm: int,
    wk: int,
    turn: str,
    move: tuple[int, int, int, bool, bool, bool],
) -> tuple[int, int, int, int, str]:
    frm, to, cap, capk, promotes, mover_is_king = move
    fmask = 1 << frm
    tmask = 1 << to

    if turn == "b":
        if mover_is_king:
            bk = (bk ^ fmask) | tmask
        else:
            bm ^= fmask
            if promotes:
                bk |= tmask
            else:
                bm |= tmask
        if cap != -1:
            cmask = 1 << cap
            if capk:
                wk ^= cmask
            else:
                wm ^= cmask
        return bm, bk, wm, wk, "w"

    else:
        if mover_is_king:
            wk = (wk ^ fmask) | tmask
        else:
            wm ^= fmask
            if promotes:
                wk |= tmask
            else:
                wm |= tmask
        if cap != -1:
            cmask = 1 << cap
            if capk:
                bk ^= cmask
            else:
                bm ^= cmask
        return bm, bk, wm, wk, "b"


def _move_priority(move, tt_move=None) -> int:
    frm, to, cap, capk, promotes, mover_is_king = move
    r, c = _rc(to)
    score = 0
    if tt_move is not None and move == tt_move:
        score += 1_000_000
    if cap != -1:
        score += 5000
        score += 900 if capk else 500
    if promotes:
        score += 800
    if mover_is_king:
        score += 50
    if 2 <= r <= 5 and 2 <= c <= 5:
        score += 40
    elif c == 0 or c == 7:
        score += 10
    # Slight preference for longer displacement in tactical spots
    score += abs((to >> 3) - (frm >> 3)) * 2
    return score


def _order_moves(moves, tt_move=None):
    if len(moves) <= 1:
        return moves
    return sorted(moves, key=lambda m: _move_priority(m, tt_move), reverse=True)


def _side_score(own_m: int, own_k: int, color: str) -> int:
    own_occ = own_m | own_k
    score = own_m.bit_count() * 100 + own_k.bit_count() * 185

    # Men
    for sq in _iter_bits(own_m):
        r, c = _rc(sq)

        adv = (7 - r) if color == "b" else r
        score += adv * 6

        if 2 <= r <= 5 and 2 <= c <= 5:
            score += 5
        elif c == 0 or c == 7:
            score += 2

        # Back-rank guard
        if (color == "b" and r == 7) or (color == "w" and r == 0):
            score += 4

        # Close to promotion
        if (color == "b" and r == 1) or (color == "w" and r == 6):
            score += 10

        # Simple structural support from behind
        br = r + 1 if color == "b" else r - 1
        if 0 <= br < 8:
            supported = False
            if c > 0 and (own_occ & (1 << _idx(br, c - 1))):
                supported = True
            if c < 7 and (own_occ & (1 << _idx(br, c + 1))):
                supported = True
            if supported:
                score += 3

    # Kings
    for sq in _iter_bits(own_k):
        r, c = _rc(sq)
        if 2 <= r <= 5 and 2 <= c <= 5:
            score += 10
        elif c == 0 or c == 7:
            score -= 2

    return score


def _evaluate(bm: int, bk: int, wm: int, wk: int, turn: str) -> int:
    diff = _side_score(bm, bk, "b") - _side_score(wm, wk, "w")

    total_pieces = (bm | bk).bit_count() + (wm | wk).bit_count()
    if total_pieces <= 14:
        b_moves = _generate_moves(bm, bk, wm, wk, "b")
        w_moves = _generate_moves(bm, bk, wm, wk, "w")
        diff += 2 * (len(b_moves) - len(w_moves))
        if b_moves and b_moves[0][2] != -1:
            diff += 12
        if w_moves and w_moves[0][2] != -1:
            diff -= 12

    return diff if turn == "b" else -diff


def _negamax(
    bm: int,
    bk: int,
    wm: int,
    wk: int,
    turn: str,
    depth: int,
    alpha: int,
    beta: int,
    deadline: float,
    qdepth: int = 0,
) -> int:
    if time.perf_counter() >= deadline:
        raise SearchTimeout

    key = (bm, bk, wm, wk, turn)
    alpha_orig = alpha
    tt_move = None

    if depth > 0:
        entry = _TT.get(key)
        if entry is not None:
            e_depth, e_flag, e_val, e_move = entry
            if e_depth >= depth:
                if e_flag == 0:
                    return e_val
                elif e_flag == 1:
                    alpha = max(alpha, e_val)
                else:
                    beta = min(beta, e_val)
                if alpha >= beta:
                    return e_val
            tt_move = e_move

    moves = _generate_moves(bm, bk, wm, wk, turn)
    if not moves:
        return -MATE + (8 - depth)

    if depth <= 0:
        # Quiescence: continue through forced captures a bit more
        if qdepth < 4 and moves[0][2] != -1:
            best = -INF
            for mv in _order_moves(moves):
                nbm, nbk, nwm, nwk, nturn = _apply_move(bm, bk, wm, wk, turn, mv)
                val = -_negamax(nbm, nbk, nwm, nwk, nturn, 0, -beta, -alpha, deadline, qdepth + 1)
                if val > best:
                    best = val
                if best > alpha:
                    alpha = best
                if alpha >= beta:
                    break
            return best
        return _evaluate(bm, bk, wm, wk, turn)

    ordered = _order_moves(moves, tt_move)
    best_val = -INF
    best_move = ordered[0]

    for mv in ordered:
        nbm, nbk, nwm, nwk, nturn = _apply_move(bm, bk, wm, wk, turn, mv)
        val = -_negamax(nbm, nbk, nwm, nwk, nturn, depth - 1, -beta, -alpha, deadline, 0)

        if val > best_val:
            best_val = val
            best_move = mv
        if val > alpha:
            alpha = val
        if alpha >= beta:
            break

    flag = 0
    if best_val <= alpha_orig:
        flag = 2
    elif best_val >= beta:
        flag = 1

    _TT[key] = (depth, flag, best_val, best_move)
    return best_val


def _root_search(
    bm: int,
    bk: int,
    wm: int,
    wk: int,
    turn: str,
    depth: int,
    deadline: float,
):
    key = (bm, bk, wm, wk, turn)
    tt_move = _TT.get(key, (0, 0, 0, None))[3]
    moves = _order_moves(_generate_moves(bm, bk, wm, wk, turn), tt_move)

    if not moves:
        return -MATE, None

    alpha = -INF
    beta = INF
    best_val = -INF
    best_move = moves[0]

    for mv in moves:
        if time.perf_counter() >= deadline:
            raise SearchTimeout
        nbm, nbk, nwm, nwk, nturn = _apply_move(bm, bk, wm, wk, turn, mv)
        val = -_negamax(nbm, nbk, nwm, nwk, nturn, depth - 1, -beta, -alpha, deadline, 0)

        if val > best_val:
            best_val = val
            best_move = mv
        if val > alpha:
            alpha = val

    _TT[key] = (depth, 0, best_val, best_move)
    return best_val, best_move


def _fallback_legal(
    bm: int, bk: int, wm: int, wk: int, color: str
) -> tuple[tuple[int, int], tuple[int, int]]:
    moves = _generate_moves(bm, bk, wm, wk, color)
    if moves:
        frm, to = moves[0][0], moves[0][1]
        return _rc(frm), _rc(to)

    # Terminal position should normally not be queried.
    own = (bm | bk) if color == "b" else (wm | wk)
    if own:
        sq = (own & -own).bit_length() - 1
        rc = _rc(sq)
        return rc, rc
    return (0, 0), (0, 0)


def policy(
    my_men, my_kings, opp_men, opp_kings, color
) -> tuple[tuple[int, int], tuple[int, int]]:
    global _TT

    # Keep TT bounded
    if len(_TT) > 250000:
        _TT.clear()

    if color == "b":
        bm = _list_to_bb(my_men)
        bk = _list_to_bb(my_kings)
        wm = _list_to_bb(opp_men)
        wk = _list_to_bb(opp_kings)
    else:
        wm = _list_to_bb(my_men)
        wk = _list_to_bb(my_kings)
        bm = _list_to_bb(opp_men)
        bk = _list_to_bb(opp_kings)

    root_moves = _generate_moves(bm, bk, wm, wk, color)
    if not root_moves:
        return _fallback_legal(bm, bk, wm, wk, color)
    if len(root_moves) == 1:
        frm, to = root_moves[0][0], root_moves[0][1]
        return _rc(frm), _rc(to)

    total_pieces = (bm | bk).bit_count() + (wm | wk).bit_count()
    # Stay safely below the 1s limit.
    budget = 0.92 if total_pieces > 8 else 0.96
    deadline = time.perf_counter() + budget

    tt_move = _TT.get((bm, bk, wm, wk, color), (0, 0, 0, None))[3]
    best_move = _order_moves(root_moves, tt_move)[0]

    # Iterative deepening
    max_depth = 12 if total_pieces <= 8 else 10
    for depth in range(1, max_depth + 1):
        try:
            _, mv = _root_search(bm, bk, wm, wk, color, depth, deadline)
            if mv is not None:
                best_move = mv
        except SearchTimeout:
            break
        except Exception:
            # Safety: never fail to return a legal move
            break

    frm, to = best_move[0], best_move[1]
    return _rc(frm), _rc(to)
