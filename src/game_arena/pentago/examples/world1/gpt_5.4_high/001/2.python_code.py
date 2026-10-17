
import time

FULL_MASK = (1 << 36) - 1
INF = 10**9
WIN_SCORE = 10**6
LINE_VALUES = (0, 2, 12, 80, 500, 0)
QUAD_CENTERS = (7, 10, 25, 28)  # (2,2), (2,5), (5,2), (5,5) in 1-indexed terms


def _build_tables():
    # All 5-cell winning windows on 6x6 board
    win_masks = []

    # Horizontal
    for r in range(6):
        for c in range(2):
            mask = 0
            for k in range(5):
                mask |= 1 << (r * 6 + c + k)
            win_masks.append(mask)

    # Vertical
    for c in range(6):
        for r in range(2):
            mask = 0
            for k in range(5):
                mask |= 1 << ((r + k) * 6 + c)
            win_masks.append(mask)

    # Diagonal down-right
    for r in range(2):
        for c in range(2):
            mask = 0
            for k in range(5):
                mask |= 1 << ((r + k) * 6 + (c + k))
            win_masks.append(mask)

    # Diagonal down-left
    for r in range(2):
        for c in range(4, 6):
            mask = 0
            for k in range(5):
                mask |= 1 << ((r + k) * 6 + (c - k))
            win_masks.append(mask)

    # Quadrant positions and masks
    qpos = []
    qmask = []
    for q in range(4):
        qr = (q // 2) * 3
        qc = (q % 2) * 3
        pos = []
        mask = 0
        for r in range(qr, qr + 3):
            for c in range(qc, qc + 3):
                idx = r * 6 + c
                pos.append(idx)
                mask |= 1 << idx
        qpos.append(tuple(pos))
        qmask.append(mask)

    # Local 3x3 rotation tables: dir 0=L, 1=R
    rot_pat = [[0] * 512 for _ in range(2)]
    for pat in range(512):
        left = 0
        right = 0
        for i in range(9):
            if (pat >> i) & 1:
                r, c = divmod(i, 3)

                # Left
                nr, nc = 2 - c, r
                left |= 1 << (nr * 3 + nc)

                # Right
                nr, nc = c, 2 - r
                right |= 1 << (nr * 3 + nc)

        rot_pat[0][pat] = left
        rot_pat[1][pat] = right

    # Map local 9-bit pattern to global 36-bit board bits for each quadrant
    pat_bits = []
    for q in range(4):
        arr = [0] * 512
        pos = qpos[q]
        for pat in range(512):
            bits = 0
            for i in range(9):
                if (pat >> i) & 1:
                    bits |= 1 << pos[i]
            arr[pat] = bits
        pat_bits.append(tuple(arr))

    # Where a newly placed stone ends up after rotating a chosen quadrant
    place_after = [[[0] * 36 for _ in range(2)] for _ in range(4)]
    for q in range(4):
        qr = (q // 2) * 3
        qc = (q % 2) * 3
        for idx in range(36):
            r, c = divmod(idx, 6)
            in_quad = qr <= r < qr + 3 and qc <= c < qc + 3
            for d in (0, 1):
                if in_quad:
                    lr, lc = r - qr, c - qc
                    if d == 0:  # L
                        nr, nc = 2 - lc, lr
                    else:       # R
                        nr, nc = lc, 2 - lr
                    dest = (qr + nr) * 6 + (qc + nc)
                else:
                    dest = idx
                place_after[q][d][idx] = 1 << dest

    # Cell priority: number of win windows through cell + stable center bonus
    cell_priority = [0] * 36
    for mask in win_masks:
        for idx in range(36):
            if (mask >> idx) & 1:
                cell_priority[idx] += 1
    for idx in QUAD_CENTERS:
        cell_priority[idx] += 2

    def center_key(i):
        r, c = divmod(i, 6)
        return -((r - 2.5) ** 2 + (c - 2.5) ** 2)

    cell_order = tuple(
        sorted(range(36), key=lambda i: (cell_priority[i], center_key(i)), reverse=True)
    )

    quad_center_mask = 0
    for idx in QUAD_CENTERS:
        quad_center_mask |= 1 << idx

    return (
        tuple(win_masks),
        tuple(qpos),
        tuple(qmask),
        tuple(tuple(x) for x in rot_pat),
        tuple(pat_bits),
        tuple(tuple(tuple(x) for x in dirs) for dirs in place_after),
        tuple(cell_priority),
        cell_order,
        quad_center_mask,
    )


(
    WIN_MASKS,
    QPOS,
    QMASK,
    ROT_PAT,
    PAT_BITS,
    PLACE_AFTER_BITS,
    CELL_PRIORITY,
    CELL_ORDER,
    QUAD_CENTER_MASK,
) = _build_tables()


def _rotate_bb(bb, q, d):
    p = QPOS[q]
    pat = (
        ((bb >> p[0]) & 1)
        | (((bb >> p[1]) & 1) << 1)
        | (((bb >> p[2]) & 1) << 2)
        | (((bb >> p[3]) & 1) << 3)
        | (((bb >> p[4]) & 1) << 4)
        | (((bb >> p[5]) & 1) << 5)
        | (((bb >> p[6]) & 1) << 6)
        | (((bb >> p[7]) & 1) << 7)
        | (((bb >> p[8]) & 1) << 8)
    )
    return (bb & ~QMASK[q]) | PAT_BITS[q][ROT_PAT[d][pat]]


def _has_win(bb):
    for mask in WIN_MASKS:
        if (bb & mask) == mask:
            return True
    return False


def _static_eval(myb, oppb):
    score = 0
    my3 = my4 = 0
    opp3 = opp4 = 0

    for mask in WIN_MASKS:
        mb = myb & mask
        ob = oppb & mask
        if mb and ob:
            continue
        if mb:
            c = mb.bit_count()
            score += LINE_VALUES[c]
            if c == 4:
                my4 += 1
            elif c == 3:
                my3 += 1
        elif ob:
            c = ob.bit_count()
            score -= LINE_VALUES[c]
            if c == 4:
                opp4 += 1
            elif c == 3:
                opp3 += 1

    score += 450 * (my4 - opp4)
    score += 40 * (my3 - opp3)
    score += 8 * ((myb & QUAD_CENTER_MASK).bit_count() - (oppb & QUAD_CENTER_MASK).bit_count())
    return score


def _arrays_to_bits(you, opponent):
    myb = 0
    oppb = 0
    bit = 1
    for r in range(6):
        yr = you[r]
        orow = opponent[r]
        for c in range(6):
            if int(yr[c]):
                myb |= bit
            elif int(orow[c]):
                oppb |= bit
            bit <<= 1
    return myb, oppb


def _format_move(idx, q, d):
    r, c = divmod(idx, 6)
    return f"{r + 1},{c + 1},{q},{'L' if d == 0 else 'R'}"


def _fallback_move(occ):
    for idx in range(36):
        if not ((occ >> idx) & 1):
            return _format_move(idx, 0, 0)
    return "1,1,0,L"


def _move_cap(empties, depth, ply):
    # Root: full search for shallow depths, beam for deeper iterations
    if ply == 0:
        if depth <= 2:
            return 10**9
        if empties > 24:
            return 64
        if empties > 18:
            return 80
        if empties > 12:
            return 96
        return 10**9

    # Internal nodes: exact at depth 1, broader at depth 2, narrower deeper
    if depth <= 1:
        return 10**9

    if depth == 2:
        if empties > 24:
            return 24
        if empties > 18:
            return 28
        if empties > 12:
            return 36
        if empties > 8:
            return 48
        return 10**9

    # depth >= 3
    if empties > 24:
        return 12
    if empties > 18:
        return 14
    if empties > 12:
        return 18
    if empties > 8:
        return 24
    return 10**9


def policy(you, opponent) -> str:
    my_root, opp_root = _arrays_to_bits(you, opponent)
    occ_root = my_root | opp_root
    fallback = _fallback_move(occ_root)

    # Simple stable opening book: quadrant centers don't move under rotation
    stones = occ_root.bit_count()
    if stones <= 1:
        for idx in QUAD_CENTERS:
            if not ((occ_root >> idx) & 1):
                r, c = divmod(idx, 6)
                q = (r // 3) * 2 + (c // 3)
                return _format_move(idx, q, 0)

    deadline = time.perf_counter() + 0.95
    tt = {}
    node_counter = 0

    class Timeout(Exception):
        pass

    def check_time():
        nonlocal node_counter
        node_counter += 1
        if (node_counter & 511) == 0 and time.perf_counter() > deadline:
            raise Timeout

    def generate_moves(myb, oppb, depth, ply, tt_best=None):
        check_time()

        occ = myb | oppb
        empties_n = 36 - occ.bit_count()
        if empties_n <= 0:
            return []

        empty_cells = [idx for idx in CELL_ORDER if not ((occ >> idx) & 1)]
        moves = []
        seen = set()

        for q in range(4):
            for d in (0, 1):
                check_time()

                rot_my = _rotate_bb(myb, q, d)
                rot_opp = _rotate_bb(oppb, q, d)
                opp_win = _has_win(rot_opp)

                place_bits = PLACE_AFTER_BITS[q][d]

                for idx in empty_cells:
                    my2 = rot_my | place_bits[idx]
                    key = (my2, rot_opp)
                    if key in seen:
                        continue
                    seen.add(key)

                    my_win = _has_win(my2)

                    if my_win or opp_win or empties_n == 1:
                        if my_win and opp_win:
                            term = 0
                        elif my_win:
                            term = WIN_SCORE - ply
                        elif opp_win:
                            term = -WIN_SCORE + ply
                        else:
                            term = 0
                        score = term + CELL_PRIORITY[idx]
                    else:
                        term = None
                        score = _static_eval(my2, rot_opp) + CELL_PRIORITY[idx]

                    if tt_best is not None and (idx, q, d) == tt_best:
                        score += 5000

                    # child state is from next player's perspective
                    moves.append((score, idx, q, d, term, rot_opp, my2))

        if not moves:
            return []

        moves.sort(key=lambda x: x[0], reverse=True)

        # If we have immediate wins, only keep those
        if moves[0][4] is not None and moves[0][4] > 0:
            k = 0
            while k < len(moves) and moves[k][4] is not None and moves[k][4] > 0:
                k += 1
            return moves[:k]

        cap = _move_cap(empties_n, depth, ply)
        if len(moves) > cap:
            moves = moves[:cap]
        return moves

    EXACT, LOWER, UPPER = 0, 1, 2

    def negamax(myb, oppb, depth, alpha, beta, ply):
        check_time()

        occ = myb | oppb
        if occ == FULL_MASK:
            return 0
        if depth == 0:
            return _static_eval(myb, oppb)

        a0, b0 = alpha, beta
        key = (myb, oppb)
        entry = tt.get(key)
        tt_best = None

        if entry is not None:
            edepth, evalv, flag, emove = entry
            tt_best = emove
            if edepth >= depth:
                if flag == EXACT:
                    return evalv
                elif flag == LOWER:
                    alpha = max(alpha, evalv)
                else:
                    beta = min(beta, evalv)
                if alpha >= beta:
                    return evalv

        moves = generate_moves(myb, oppb, depth, ply, tt_best)
        if not moves:
            return 0

        best = -INF
        best_move = None

        for _, idx, q, d, term, child_my, child_opp in moves:
            if term is not None:
                score = term
            else:
                score = -negamax(child_my, child_opp, depth - 1, -beta, -alpha, ply + 1)

            if score > best:
                best = score
                best_move = (idx, q, d)

            if best > alpha:
                alpha = best
            if alpha >= beta:
                break

        if best <= a0:
            flag = UPPER
        elif best >= b0:
            flag = LOWER
        else:
            flag = EXACT
        tt[key] = (depth, best, flag, best_move)

        return best

    empties = 36 - occ_root.bit_count()
    if empties > 24:
        max_depth = 4
    elif empties > 18:
        max_depth = 5
    elif empties > 12:
        max_depth = 6
    elif empties > 8:
        max_depth = 7
    else:
        max_depth = 9

    best_move = None
    best_move_str = fallback
    pv_move = None

    for depth in range(1, max_depth + 1):
        try:
            root_moves = generate_moves(my_root, opp_root, depth, 0, pv_move)
            if not root_moves:
                return fallback

            alpha = -INF
            beta = INF
            local_best_score = -INF
            local_best_move = None

            for _, idx, q, d, term, child_my, child_opp in root_moves:
                check_time()

                if term is not None:
                    score = term
                else:
                    score = -negamax(child_my, child_opp, depth - 1, -beta, -alpha, 1)

                if score > local_best_score:
                    local_best_score = score
                    local_best_move = (idx, q, d)

                if score > alpha:
                    alpha = score

                if alpha >= beta:
                    break

            if local_best_move is not None:
                best_move = local_best_move
                best_move_str = _format_move(*best_move)
                pv_move = best_move

            if local_best_score >= WIN_SCORE - 10:
                break

        except Timeout:
            break
        except Exception:
            # Safety: never fail to return a legal move
            break

    return best_move_str
