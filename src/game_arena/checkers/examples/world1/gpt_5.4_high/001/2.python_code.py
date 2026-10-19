
import time

INF = 10**9
MATE = 10**7

DIRS_B = ((-1, -1), (-1, 1))  # black moves downward: lower row values
DIRS_W = ((1, -1), (1, 1))    # white moves upward: higher row values
DIRS_K = DIRS_B + DIRS_W

ROW = [i >> 3 for i in range(64)]
COL = [i & 7 for i in range(64)]

ROW_MASKS = []
for r in range(8):
    mask = 0
    for c in range(8):
        mask |= 1 << (r * 8 + c)
    ROW_MASKS.append(mask)

MAN_B_TABLE = [0] * 64
MAN_W_TABLE = [0] * 64
KING_TABLE = [0] * 64
KING_END_TABLE = [0] * 64
CENTER_ORDER = [0] * 64

for idx in range(64):
    r = ROW[idx]
    c = COL[idx]

    if 2 <= r <= 5 and 2 <= c <= 5:
        center = 6
    elif 1 <= r <= 6 and 1 <= c <= 6:
        center = 3
    else:
        center = 0

    edge_man = 1 if c in (0, 7) else 0
    MAN_B_TABLE[idx] = 6 * (7 - r) + center + edge_man
    MAN_W_TABLE[idx] = 6 * r + center + edge_man

    if 2 <= r <= 5 and 2 <= c <= 5:
        kpos = 10
    elif 1 <= r <= 6 and 1 <= c <= 6:
        kpos = 5
    else:
        kpos = -2
    if r in (0, 7) or c in (0, 7):
        kpos -= 2

    KING_TABLE[idx] = kpos
    KING_END_TABLE[idx] = int(12 - 2 * (abs(r - 3.5) + abs(c - 3.5)))
    CENTER_ORDER[idx] = center

_GLOBAL_HISTORY = {}


def _bit_count(x: int) -> int:
    return x.bit_count()


def _inside(r: int, c: int) -> bool:
    return 0 <= r < 8 and 0 <= c < 8


def _to_bits(pieces) -> int:
    bb = 0
    for r, c in pieces:
        bb |= 1 << (r * 8 + c)
    return bb


def _iter_bits(bb: int):
    while bb:
        lsb = bb & -bb
        yield lsb.bit_length() - 1
        bb ^= lsb


def _gen_captures(bm: int, bk: int, wm: int, wk: int, turn: str):
    occ = bm | bk | wm | wk
    caps = []

    if turn == 'b':
        own_men, own_kings = bm, bk
        opp_occ = wm | wk
        men_dirs = DIRS_B
    else:
        own_men, own_kings = wm, wk
        opp_occ = bm | bk
        men_dirs = DIRS_W

    for frm in _iter_bits(own_men):
        r = ROW[frm]
        c = COL[frm]
        for dr, dc in men_dirs:
            r1 = r + dr
            c1 = c + dc
            r2 = r1 + dr
            c2 = c1 + dc
            if 0 <= r2 < 8 and 0 <= c2 < 8:
                mid = r1 * 8 + c1
                to = r2 * 8 + c2
                midb = 1 << mid
                tob = 1 << to
                if (opp_occ & midb) and not (occ & tob):
                    caps.append((frm, to, mid))

    for frm in _iter_bits(own_kings):
        r = ROW[frm]
        c = COL[frm]
        for dr, dc in DIRS_K:
            r1 = r + dr
            c1 = c + dc
            r2 = r1 + dr
            c2 = c1 + dc
            if 0 <= r2 < 8 and 0 <= c2 < 8:
                mid = r1 * 8 + c1
                to = r2 * 8 + c2
                midb = 1 << mid
                tob = 1 << to
                if (opp_occ & midb) and not (occ & tob):
                    caps.append((frm, to, mid))

    return caps


def _gen_quiet(bm: int, bk: int, wm: int, wk: int, turn: str):
    occ = bm | bk | wm | wk
    moves = []

    if turn == 'b':
        own_men, own_kings = bm, bk
        men_dirs = DIRS_B
    else:
        own_men, own_kings = wm, wk
        men_dirs = DIRS_W

    for frm in _iter_bits(own_men):
        r = ROW[frm]
        c = COL[frm]
        for dr, dc in men_dirs:
            r1 = r + dr
            c1 = c + dc
            if 0 <= r1 < 8 and 0 <= c1 < 8:
                to = r1 * 8 + c1
                tob = 1 << to
                if not (occ & tob):
                    moves.append((frm, to, -1))

    for frm in _iter_bits(own_kings):
        r = ROW[frm]
        c = COL[frm]
        for dr, dc in DIRS_K:
            r1 = r + dr
            c1 = c + dc
            if 0 <= r1 < 8 and 0 <= c1 < 8:
                to = r1 * 8 + c1
                tob = 1 << to
                if not (occ & tob):
                    moves.append((frm, to, -1))

    return moves


def _move_summary(bm: int, bk: int, wm: int, wk: int, turn: str):
    caps = _gen_captures(bm, bk, wm, wk, turn)
    if caps:
        return len(caps), True
    return len(_gen_quiet(bm, bk, wm, wk, turn)), False


def _apply_move(bm: int, bk: int, wm: int, wk: int, turn: str, move):
    frm, to, cap = move
    fromb = 1 << frm
    tob = 1 << to

    if turn == 'b':
        if bk & fromb:
            bk = (bk ^ fromb) | tob
        else:
            bm ^= fromb
            if ROW[to] == 0:
                bk |= tob
            else:
                bm |= tob

        if cap != -1:
            capb = 1 << cap
            wm &= ~capb
            wk &= ~capb

        return bm, bk, wm, wk, 'w'

    else:
        if wk & fromb:
            wk = (wk ^ fromb) | tob
        else:
            wm ^= fromb
            if ROW[to] == 7:
                wk |= tob
            else:
                wm |= tob

        if cap != -1:
            capb = 1 << cap
            bm &= ~capb
            bk &= ~capb

        return bm, bk, wm, wk, 'b'


def _evaluate_root(bm: int, bk: int, wm: int, wk: int, root: str) -> int:
    total = _bit_count(bm) + _bit_count(bk) + _bit_count(wm) + _bit_count(wk)
    black_occ = bm | bk
    white_occ = wm | wk

    black = 100 * _bit_count(bm) + 182 * _bit_count(bk)
    white = 100 * _bit_count(wm) + 182 * _bit_count(wk)

    if wm:
        black += 5 * _bit_count(bm & ROW_MASKS[7])  # black home row
    if bm:
        white += 5 * _bit_count(wm & ROW_MASKS[0])  # white home row

    for idx in _iter_bits(bm):
        black += MAN_B_TABLE[idx]
        r = ROW[idx]
        c = COL[idx]
        if r < 7:
            if c > 0 and (black_occ & (1 << ((r + 1) * 8 + (c - 1)))):
                black += 2
            if c < 7 and (black_occ & (1 << ((r + 1) * 8 + (c + 1)))):
                black += 2

    for idx in _iter_bits(wm):
        white += MAN_W_TABLE[idx]
        r = ROW[idx]
        c = COL[idx]
        if r > 0:
            if c > 0 and (white_occ & (1 << ((r - 1) * 8 + (c - 1)))):
                white += 2
            if c < 7 and (white_occ & (1 << ((r - 1) * 8 + (c + 1)))):
                white += 2

    endgame = total <= 8
    for idx in _iter_bits(bk):
        black += KING_TABLE[idx]
        if endgame:
            black += KING_END_TABLE[idx]

    for idx in _iter_bits(wk):
        white += KING_TABLE[idx]
        if endgame:
            white += KING_END_TABLE[idx]

    if total <= 12:
        bcount, bcap = _move_summary(bm, bk, wm, wk, 'b')
        wcount, wcap = _move_summary(bm, bk, wm, wk, 'w')
        black += 2 * bcount + (6 if bcap else 0)
        white += 2 * wcount + (6 if wcap else 0)

    score = black - white
    return score if root == 'b' else -score


def _emergency_move(my_men, my_kings, opp_men, opp_kings, color):
    my_men = [tuple(x) for x in my_men]
    my_kings = [tuple(x) for x in my_kings]
    opp_men = [tuple(x) for x in opp_men]
    opp_kings = [tuple(x) for x in opp_kings]

    pieces = my_men + my_kings
    kings = set(my_kings)
    occ = set(pieces + opp_men + opp_kings)
    opp = set(opp_men + opp_kings)

    forward = DIRS_B if color == 'b' else DIRS_W

    for fr in pieces:
        dirs = DIRS_K if fr in kings else forward
        for dr, dc in dirs:
            mid = (fr[0] + dr, fr[1] + dc)
            to = (fr[0] + 2 * dr, fr[1] + 2 * dc)
            if _inside(*to) and mid in opp and to not in occ:
                return fr, to

    for fr in pieces:
        dirs = DIRS_K if fr in kings else forward
        for dr, dc in dirs:
            to = (fr[0] + dr, fr[1] + dc)
            if _inside(*to) and to not in occ:
                return fr, to

    if pieces:
        return pieces[0], pieces[0]
    return (0, 0), (0, 0)


def policy(my_men, my_kings, opp_men, opp_kings, color) -> tuple[tuple[int, int], tuple[int, int]]:
    if color == 'b':
        bm = _to_bits(my_men)
        bk = _to_bits(my_kings)
        wm = _to_bits(opp_men)
        wk = _to_bits(opp_kings)
    else:
        wm = _to_bits(my_men)
        wk = _to_bits(my_kings)
        bm = _to_bits(opp_men)
        bk = _to_bits(opp_kings)

    gen_caps = _gen_captures
    gen_quiet = _gen_quiet
    apply_move = _apply_move
    eval_root = _evaluate_root

    legal_moves = gen_caps(bm, bk, wm, wk, color)
    if not legal_moves:
        legal_moves = gen_quiet(bm, bk, wm, wk, color)

    if not legal_moves:
        return _emergency_move(my_men, my_kings, opp_men, opp_kings, color)

    if len(legal_moves) == 1:
        frm, to, _ = legal_moves[0]
        return (ROW[frm], COL[frm]), (ROW[to], COL[to])

    total_pieces = _bit_count(bm) + _bit_count(bk) + _bit_count(wm) + _bit_count(wk)
    if total_pieces >= 20:
        max_depth = 7
    elif total_pieces >= 14:
        max_depth = 8
    elif total_pieces >= 8:
        max_depth = 10
    else:
        max_depth = 12

    start = time.perf_counter()
    deadline = start + 0.92

    tt = {}
    history = _GLOBAL_HISTORY
    if len(history) > 50000:
        history.clear()

    nodes = 0

    def maybe_timeout():
        nonlocal nodes
        nodes += 1
        if (nodes & 1023) == 0 and time.perf_counter() >= deadline:
            raise TimeoutError

    def order_score(move, bm_, bk_, wm_, wk_, turn_, tt_move=None):
        frm, to, cap = move
        s = history.get((turn_, frm, to), 0)

        if tt_move is not None and move == tt_move:
            s += 1_000_000

        if turn_ == 'b':
            own_men, own_kings, opp_men, opp_kings = bm_, bk_, wm_, wk_
            promote_row = 0
        else:
            own_men, own_kings, opp_men, opp_kings = wm_, wk_, bm_, bk_
            promote_row = 7

        fromb = 1 << frm

        if cap != -1:
            capb = 1 << cap
            s += 50_000
            s += 600 if (opp_kings & capb) else 300

        if (own_men & fromb) and ROW[to] == promote_row:
            s += 800

        s += CENTER_ORDER[to]

        if (own_kings & fromb) and (ROW[to] in (0, 7) or COL[to] in (0, 7)):
            s -= 5

        return s

    def quiescence(bm_, bk_, wm_, wk_, turn_, alpha, beta, sign, ply):
        maybe_timeout()

        caps = gen_caps(bm_, bk_, wm_, wk_, turn_)
        if caps:
            tt_entry = tt.get((bm_, bk_, wm_, wk_, turn_))
            tt_move = tt_entry[3] if tt_entry is not None else None
            if len(caps) > 1:
                caps = sorted(
                    caps,
                    key=lambda m: order_score(m, bm_, bk_, wm_, wk_, turn_, tt_move),
                    reverse=True,
                )

            best = -INF
            for mv in caps:
                nbm, nbk, nwm, nwk, nturn = apply_move(bm_, bk_, wm_, wk_, turn_, mv)
                score = -quiescence(nbm, nbk, nwm, nwk, nturn, -beta, -alpha, -sign, ply + 1)
                if score > best:
                    best = score
                if score >= beta:
                    return score
                if score > alpha:
                    alpha = score
            return best

        quiet = gen_quiet(bm_, bk_, wm_, wk_, turn_)
        if not quiet:
            return -MATE + ply

        return sign * eval_root(bm_, bk_, wm_, wk_, color)

    def negamax(bm_, bk_, wm_, wk_, turn_, depth, alpha, beta, sign, ply):
        maybe_timeout()

        key = (bm_, bk_, wm_, wk_, turn_)
        orig_alpha = alpha
        orig_beta = beta

        tt_move = None
        entry = tt.get(key)
        if entry is not None:
            e_depth, e_score, e_flag, e_move = entry
            tt_move = e_move
            if e_depth >= depth:
                if e_flag == 0:
                    return e_score
                elif e_flag == 1:
                    alpha = max(alpha, e_score)
                else:
                    beta = min(beta, e_score)
                if alpha >= beta:
                    return e_score

        caps = gen_caps(bm_, bk_, wm_, wk_, turn_)
        if caps:
            moves = caps
        else:
            moves = gen_quiet(bm_, bk_, wm_, wk_, turn_)

        if not moves:
            return -MATE + ply

        if depth <= 0:
            return quiescence(bm_, bk_, wm_, wk_, turn_, alpha, beta, sign, ply)

        if len(moves) > 1:
            moves = sorted(
                moves,
                key=lambda m: order_score(m, bm_, bk_, wm_, wk_, turn_, tt_move),
                reverse=True,
            )

        best = -INF
        best_move = moves[0]

        for mv in moves:
            nbm, nbk, nwm, nwk, nturn = apply_move(bm_, bk_, wm_, wk_, turn_, mv)
            score = -negamax(nbm, nbk, nwm, nwk, nturn, depth - 1, -beta, -alpha, -sign, ply + 1)

            if score > best:
                best = score
                best_move = mv

            if score > alpha:
                alpha = score

            if alpha >= beta:
                history[(turn_, mv[0], mv[1])] = history.get((turn_, mv[0], mv[1]), 0) + depth * depth
                break

        if best <= orig_alpha:
            flag = 2  # upper bound
        elif best >= orig_beta:
            flag = 1  # lower bound
        else:
            flag = 0  # exact

        tt[key] = (depth, best, flag, best_move)
        return best

    fallback_move = max(
        legal_moves,
        key=lambda m: order_score(m, bm, bk, wm, wk, color, None),
    )

    best_move = fallback_move
    root_moves = list(legal_moves)
    previous_best = fallback_move

    for depth in range(1, max_depth + 1):
        if time.perf_counter() >= deadline:
            break

        try:
            ordered = sorted(
                root_moves,
                key=lambda m: order_score(m, bm, bk, wm, wk, color, previous_best),
                reverse=True,
            )

            current_best = ordered[0]
            current_score = -INF
            alpha = -INF
            beta = INF

            for mv in ordered:
                nbm, nbk, nwm, nwk, nturn = apply_move(bm, bk, wm, wk, color, mv)
                score = -negamax(nbm, nbk, nwm, nwk, nturn, depth - 1, -beta, -alpha, -1, 1)

                if score > current_score:
                    current_score = score
                    current_best = mv

                if score > alpha:
                    alpha = score

            best_move = current_best
            previous_best = current_best
            root_moves = ordered

        except TimeoutError:
            break

    frm, to, _ = best_move
    return (ROW[frm], COL[frm]), (ROW[to], COL[to])
