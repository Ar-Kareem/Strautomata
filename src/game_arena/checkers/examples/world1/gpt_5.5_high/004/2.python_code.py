
from __future__ import annotations

import time


# ---------- Board precomputation ----------

_ROWS = [i // 8 for i in range(64)]
_COLS = [i % 8 for i in range(64)]
_SINGLE = [frozenset((i,)) for i in range(64)]

_DIR_B = [(-1, -1), (-1, 1)]          # black moves toward lower row numbers
_DIR_W = [(1, -1), (1, 1)]            # white moves toward higher row numbers
_DIR_K = _DIR_B + _DIR_W

_STEP_B = [[] for _ in range(64)]
_STEP_W = [[] for _ in range(64)]
_STEP_K = [[] for _ in range(64)]
_CAP_B = [[] for _ in range(64)]
_CAP_W = [[] for _ in range(64)]
_CAP_K = [[] for _ in range(64)]
_ADJ = [[] for _ in range(64)]

_ADV_B = [7 - _ROWS[i] for i in range(64)]
_ADV_W = [_ROWS[i] for i in range(64)]
_EDGE = [1 if _ROWS[i] in (0, 7) or _COLS[i] in (0, 7) else 0 for i in range(64)]
# Centralization table: corners low, center high.
_CENTER = [
    14 - (abs(2 * _ROWS[i] - 7) + abs(2 * _COLS[i] - 7))
    for i in range(64)
]

_BACK_ROW = {"b": 7, "w": 0}
_PROMO_ROW = {"b": 0, "w": 7}

for i in range(64):
    r, c = _ROWS[i], _COLS[i]

    for dr, dc in _DIR_B:
        nr, nc = r + dr, c + dc
        if 0 <= nr < 8 and 0 <= nc < 8:
            _STEP_B[i].append(nr * 8 + nc)
            _ADJ[i].append(nr * 8 + nc)
        mr, mc = r + dr, c + dc
        lr, lc = r + 2 * dr, c + 2 * dc
        if 0 <= mr < 8 and 0 <= mc < 8 and 0 <= lr < 8 and 0 <= lc < 8:
            _CAP_B[i].append((mr * 8 + mc, lr * 8 + lc))

    for dr, dc in _DIR_W:
        nr, nc = r + dr, c + dc
        if 0 <= nr < 8 and 0 <= nc < 8:
            _STEP_W[i].append(nr * 8 + nc)
            if nr * 8 + nc not in _ADJ[i]:
                _ADJ[i].append(nr * 8 + nc)
        mr, mc = r + dr, c + dc
        lr, lc = r + 2 * dr, c + 2 * dc
        if 0 <= mr < 8 and 0 <= mc < 8 and 0 <= lr < 8 and 0 <= lc < 8:
            _CAP_W[i].append((mr * 8 + mc, lr * 8 + lc))

    for dr, dc in _DIR_K:
        nr, nc = r + dr, c + dc
        if 0 <= nr < 8 and 0 <= nc < 8:
            _STEP_K[i].append(nr * 8 + nc)
        mr, mc = r + dr, c + dc
        lr, lc = r + 2 * dr, c + 2 * dc
        if 0 <= mr < 8 and 0 <= mc < 8 and 0 <= lr < 8 and 0 <= lc < 8:
            _CAP_K[i].append((mr * 8 + mc, lr * 8 + lc))


_INF = 10**9
_WIN = 10**7

_EXACT = 0
_LOWER = 1
_UPPER = 2


class _Timeout(Exception):
    pass


# State is:
# (black_men, black_kings, white_men, white_kings, turn_color)
# each piece set is a frozenset of square indices 0..63.


def _other(color: str) -> str:
    return "w" if color == "b" else "b"


def _idx_list(coords) -> list[int]:
    out = []
    for r, c in coords:
        out.append(int(r) * 8 + int(c))
    return out


def _normalize_side(men, kings, color: str):
    """Treat any regular man already on its promotion row as a king."""
    kset = set(kings)
    mset = set()
    promo = _PROMO_ROW[color]
    for p in men:
        if p in kset:
            continue
        if _ROWS[p] == promo:
            kset.add(p)
        else:
            mset.add(p)
    return frozenset(mset), frozenset(kset)


def _is_capture(move) -> bool:
    return abs(_ROWS[move[0]] - _ROWS[move[1]]) == 2


def _format_move(move):
    a, b = move
    return ((_ROWS[a], _COLS[a]), (_ROWS[b], _COLS[b]))


def _side_sets(state, color: str):
    bm, bk, wm, wk, _ = state
    if color == "b":
        return bm, bk
    return wm, wk


def _generate_moves(state):
    bm, bk, wm, wk, turn = state

    if turn == "b":
        men, kings = bm, bk
        opp_men, opp_kings = wm, wk
        man_caps = _CAP_B
        man_steps = _STEP_B
    else:
        men, kings = wm, wk
        opp_men, opp_kings = bm, bk
        man_caps = _CAP_W
        man_steps = _STEP_W

    opp_all = opp_men | opp_kings
    occ = bm | bk | wm | wk

    captures = []

    for p in men:
        for mid, dst in man_caps[p]:
            if mid in opp_all and dst not in occ:
                captures.append((p, dst))

    for p in kings:
        for mid, dst in _CAP_K[p]:
            if mid in opp_all and dst not in occ:
                captures.append((p, dst))

    if captures:
        return captures

    moves = []

    for p in men:
        for dst in man_steps[p]:
            if dst not in occ:
                moves.append((p, dst))

    for p in kings:
        for dst in _STEP_K[p]:
            if dst not in occ:
                moves.append((p, dst))

    return moves


def _apply_move(state, move):
    bm, bk, wm, wk, turn = state
    src, dst = move
    s_src = _SINGLE[src]
    s_dst = _SINGLE[dst]
    capture = _is_capture(move)

    if turn == "b":
        if src in bk:
            nbm = bm
            nbk = (bk - s_src) | s_dst
        else:
            nbm = bm - s_src
            if _ROWS[dst] == 0:
                nbk = bk | s_dst
            else:
                nbm = nbm | s_dst
                nbk = bk

        nwm, nwk = wm, wk
        if capture:
            cap = (src + dst) // 2
            s_cap = _SINGLE[cap]
            if cap in nwk:
                nwk = nwk - s_cap
            else:
                nwm = nwm - s_cap

        return (nbm, nbk, nwm, nwk, "w")

    else:
        if src in wk:
            nwm = wm
            nwk = (wk - s_src) | s_dst
        else:
            nwm = wm - s_src
            if _ROWS[dst] == 7:
                nwk = wk | s_dst
            else:
                nwm = nwm | s_dst
                nwk = wk

        nbm, nbk = bm, bk
        if capture:
            cap = (src + dst) // 2
            s_cap = _SINGLE[cap]
            if cap in nbk:
                nbk = nbk - s_cap
            else:
                nbm = nbm - s_cap

        return (nbm, nbk, nwm, nwk, "b")


def _move_count(state, color: str) -> int:
    bm, bk, wm, wk, _ = state

    if color == "b":
        men, kings = bm, bk
        opp_all = wm | wk
        man_caps = _CAP_B
        man_steps = _STEP_B
    else:
        men, kings = wm, wk
        opp_all = bm | bk
        man_caps = _CAP_W
        man_steps = _STEP_W

    occ = bm | bk | wm | wk

    caps = 0
    for p in men:
        for mid, dst in man_caps[p]:
            if mid in opp_all and dst not in occ:
                caps += 1
    for p in kings:
        for mid, dst in _CAP_K[p]:
            if mid in opp_all and dst not in occ:
                caps += 1

    if caps:
        return caps

    steps = 0
    for p in men:
        for dst in man_steps[p]:
            if dst not in occ:
                steps += 1
    for p in kings:
        for dst in _STEP_K[p]:
            if dst not in occ:
                steps += 1

    return steps


def _capture_value(state, color: str) -> int:
    bm, bk, wm, wk, _ = state

    if color == "b":
        men, kings = bm, bk
        opp_all = wm | wk
        opp_kings = wk
        man_caps = _CAP_B
    else:
        men, kings = wm, wk
        opp_all = bm | bk
        opp_kings = bk
        man_caps = _CAP_W

    occ = bm | bk | wm | wk
    val = 0

    for p in men:
        for mid, dst in man_caps[p]:
            if mid in opp_all and dst not in occ:
                val += 185 if mid in opp_kings else 100

    for p in kings:
        for mid, dst in _CAP_K[p]:
            if mid in opp_all and dst not in occ:
                val += 185 if mid in opp_kings else 100

    return val


def _protected_count(men, kings) -> int:
    own = men | kings
    cnt = 0
    for p in own:
        for q in _ADJ[p]:
            if q in own:
                cnt += 1
                break
    return cnt


def _evaluate(state, root_color: str) -> int:
    bm, bk, wm, wk, turn = state
    opp_color = _other(root_color)

    my_men, my_kings = _side_sets(state, root_color)
    op_men, op_kings = _side_sets(state, opp_color)

    my_piece_count = len(my_men) + len(my_kings)
    op_piece_count = len(op_men) + len(op_kings)

    if my_piece_count == 0:
        return -_WIN
    if op_piece_count == 0:
        return _WIN

    total = my_piece_count + op_piece_count
    king_val = 190 if total <= 8 else 175

    score = 0

    # Material.
    score += 100 * (len(my_men) - len(op_men))
    score += king_val * (len(my_kings) - len(op_kings))

    # Promotion progress for men.
    my_adv = _ADV_B if root_color == "b" else _ADV_W
    op_adv = _ADV_B if opp_color == "b" else _ADV_W
    progress_weight = 11 if total <= 8 else 7
    score += progress_weight * (
        sum(my_adv[p] for p in my_men) - sum(op_adv[p] for p in op_men)
    )

    # Near-promotion men are tactically important.
    score += 18 * (
        sum(1 for p in my_men if my_adv[p] >= 6)
        - sum(1 for p in op_men if op_adv[p] >= 6)
    )

    # Centralization: especially for kings.
    score += (
        sum(_CENTER[p] for p in my_men)
        - sum(_CENTER[p] for p in op_men)
    )
    score += 2 * (
        sum(_CENTER[p] for p in my_kings)
        - sum(_CENTER[p] for p in op_kings)
    )

    # Men on edges are harder to capture; kings on edges are less mobile.
    score += 3 * (
        sum(_EDGE[p] for p in my_men) - sum(_EDGE[p] for p in op_men)
    )
    score -= 2 * (
        sum(_EDGE[p] for p in my_kings) - sum(_EDGE[p] for p in op_kings)
    )

    # Back-row guard is useful earlier in the game.
    if total > 12:
        score += 6 * (
            sum(1 for p in my_men if _ROWS[p] == _BACK_ROW[root_color])
            - sum(1 for p in op_men if _ROWS[p] == _BACK_ROW[opp_color])
        )

    # Connected/protected pieces.
    score += 7 * (
        _protected_count(my_men, my_kings) - _protected_count(op_men, op_kings)
    )

    # Mobility.
    my_mob = _move_count(state, root_color)
    op_mob = _move_count(state, opp_color)
    score += 2 * (my_mob - op_mob)
    if my_mob == 0:
        score -= 1000
    if op_mob == 0:
        score += 1000

    # Capture threats / vulnerability.
    my_cap = _capture_value(state, root_color)
    op_cap = _capture_value(state, opp_color)
    score += (my_cap - op_cap) // 3

    # Immediate tempo: captures available to the side to move matter more.
    if turn == root_color:
        score += my_cap // 10
    else:
        score -= op_cap // 10

    # In simplified endgames, mobility while ahead helps conversion.
    material_like = (len(my_men) + 2 * len(my_kings)) - (len(op_men) + 2 * len(op_kings))
    if total <= 8 and material_like > 0:
        score += 3 * (my_mob - op_mob)

    return score


def _order_moves(state, moves, tt_best=None):
    if not moves:
        return moves

    bm, bk, wm, wk, turn = state

    if turn == "b":
        own_kings = bk
        opp_kings = wk
        adv = _ADV_B
        promo = 0
    else:
        own_kings = wk
        opp_kings = bk
        adv = _ADV_W
        promo = 7

    scored = []

    for m in moves:
        src, dst = m
        score = 0

        if tt_best is not None and m == tt_best:
            score += 1_000_000

        if _is_capture(m):
            mid = (src + dst) // 2
            victim_val = 190 if mid in opp_kings else 100
            score += 10_000 + 10 * victim_val

            if src not in own_kings and _ROWS[dst] == promo:
                score += 1500

            score += _CENTER[dst]
            if _EDGE[dst]:
                score += 5

        else:
            if src in own_kings:
                score += 30 + 2 * _CENTER[dst] - 3 * _EDGE[dst]
            else:
                if _ROWS[dst] == promo:
                    score += 2000
                score += 20 * (adv[dst] - adv[src])
                score += _CENTER[dst] + 4 * _EDGE[dst]
                if _ROWS[src] == _BACK_ROW[turn]:
                    score -= 4

        scored.append((score, m))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [m for _, m in scored]


def policy(my_men, my_kings, opp_men, opp_kings, color) -> tuple[tuple[int, int], tuple[int, int]]:
    root_color = "b" if color == "b" else "w"

    my_men_i = _idx_list(my_men)
    my_kings_i = _idx_list(my_kings)
    opp_men_i = _idx_list(opp_men)
    opp_kings_i = _idx_list(opp_kings)

    if root_color == "b":
        bm, bk = _normalize_side(my_men_i, my_kings_i, "b")
        wm, wk = _normalize_side(opp_men_i, opp_kings_i, "w")
    else:
        wm, wk = _normalize_side(my_men_i, my_kings_i, "w")
        bm, bk = _normalize_side(opp_men_i, opp_kings_i, "b")

    root_state = (bm, bk, wm, wk, root_color)
    root_moves = _generate_moves(root_state)

    # The game engine should not ask for a move from a side with no legal moves.
    # This fallback is only for absolute robustness.
    if not root_moves:
        own_men, own_kings = _side_sets(root_state, root_color)
        pieces = list(own_kings) + list(own_men)
        if pieces:
            p = pieces[0]
            return ((_ROWS[p], _COLS[p]), (_ROWS[p], _COLS[p]))
        return ((0, 0), (0, 0))

    if len(root_moves) == 1:
        return _format_move(root_moves[0])

    deadline = time.perf_counter() + 0.88
    tt = {}
    nodes = 0

    def check_time():
        nonlocal nodes
        nodes += 1
        if (nodes & 127) == 0 and time.perf_counter() > deadline:
            raise _Timeout()

    def terminal_value(state, ply):
        turn = state[4]
        if turn == root_color:
            return -_WIN + ply
        return _WIN - ply

    def quiesce(state, alpha, beta, qdepth, ply):
        check_time()

        moves = _generate_moves(state)
        if not moves:
            return terminal_value(state, ply)

        if qdepth <= 0 or not _is_capture(moves[0]):
            return _evaluate(state, root_color)

        maxing = state[4] == root_color
        ordered = _order_moves(state, moves)

        if maxing:
            value = -_INF
            for m in ordered:
                child = _apply_move(state, m)
                val = quiesce(child, alpha, beta, qdepth - 1, ply + 1)
                if val > value:
                    value = val
                if value > alpha:
                    alpha = value
                if alpha >= beta:
                    break
            return value
        else:
            value = _INF
            for m in ordered:
                child = _apply_move(state, m)
                val = quiesce(child, alpha, beta, qdepth - 1, ply + 1)
                if val < value:
                    value = val
                if value < beta:
                    beta = value
                if alpha >= beta:
                    break
            return value

    def alphabeta(state, depth, alpha, beta, ply):
        check_time()

        moves = _generate_moves(state)
        if not moves:
            return terminal_value(state, ply)

        if depth <= 0:
            return quiesce(state, alpha, beta, 5, ply)

        alpha_start, beta_start = alpha, beta

        entry = tt.get(state)
        tt_best = None
        if entry is not None:
            e_depth, e_flag, e_val, e_best = entry
            tt_best = e_best
            if e_depth >= depth:
                if e_flag == _EXACT:
                    return e_val
                if e_flag == _LOWER:
                    alpha = max(alpha, e_val)
                elif e_flag == _UPPER:
                    beta = min(beta, e_val)
                if alpha >= beta:
                    return e_val

        ordered = _order_moves(state, moves, tt_best)
        maxing = state[4] == root_color
        best_move = ordered[0]

        if maxing:
            value = -_INF
            for m in ordered:
                child = _apply_move(state, m)
                val = alphabeta(child, depth - 1, alpha, beta, ply + 1)
                if val > value:
                    value = val
                    best_move = m
                if value > alpha:
                    alpha = value
                if alpha >= beta:
                    break
        else:
            value = _INF
            for m in ordered:
                child = _apply_move(state, m)
                val = alphabeta(child, depth - 1, alpha, beta, ply + 1)
                if val < value:
                    value = val
                    best_move = m
                if value < beta:
                    beta = value
                if alpha >= beta:
                    break

        if value <= alpha_start:
            flag = _UPPER
        elif value >= beta_start:
            flag = _LOWER
        else:
            flag = _EXACT

        tt[state] = (depth, flag, value, best_move)
        return value

    ordered_root = _order_moves(root_state, root_moves)

    # Legal one-ply fallback, also catches immediate wins.
    best_move = ordered_root[0]
    best_val = -_INF
    for m in ordered_root:
        child = _apply_move(root_state, m)
        if not _generate_moves(child):
            return _format_move(m)
        val = _evaluate(child, root_color)
        if val > best_val:
            best_val = val
            best_move = m

    total_pieces = len(bm) + len(bk) + len(wm) + len(wk)
    if total_pieces <= 6:
        max_depth = 18
    elif total_pieces <= 10:
        max_depth = 14
    elif total_pieces <= 16:
        max_depth = 11
    else:
        max_depth = 9

    try:
        for depth in range(1, max_depth + 1):
            if time.perf_counter() > deadline:
                break

            root_order = [best_move] + [m for m in ordered_root if m != best_move]
            alpha, beta = -_INF, _INF
            local_best = best_move
            local_val = -_INF

            for m in root_order:
                check_time()
                child = _apply_move(root_state, m)
                val = alphabeta(child, depth - 1, alpha, beta, 1)

                if val > local_val:
                    local_val = val
                    local_best = m

                if val > alpha:
                    alpha = val

            # Only update after a fully completed depth.
            best_move = local_best
            best_val = local_val
            ordered_root = [best_move] + [m for m in ordered_root if m != best_move]

            if best_val > _WIN - 1000:
                break

    except _Timeout:
        pass

    return _format_move(best_move)
