
ALL_MASK = (1 << 36) - 1
BITS = [1 << i for i in range(36)]

# ---------- Precompute win masks (all 5-long windows) ----------
_line_masks = []
_cell_line_count = [0] * 36
for r in range(6):
    for c in range(6):
        for dr, dc in ((1, 0), (0, 1), (1, 1), (1, -1)):
            r2 = r + 4 * dr
            c2 = c + 4 * dc
            if 0 <= r2 < 6 and 0 <= c2 < 6:
                mask = 0
                for k in range(5):
                    idx = (r + k * dr) * 6 + (c + k * dc)
                    mask |= 1 << idx
                _line_masks.append(mask)
                for k in range(5):
                    idx = (r + k * dr) * 6 + (c + k * dc)
                    _cell_line_count[idx] += 1
LINE_MASKS = tuple(_line_masks)

# Prefer cells that participate in more 5-windows, with a small center bias.
CELL_ORDER = sorted(
    range(36),
    key=lambda i: (
        _cell_line_count[i],
        -((i // 6) - 2.5) ** 2 - ((i % 6) - 2.5) ** 2,
    ),
    reverse=True,
)

# ---------- Precompute quadrant rotation maps ----------
QUAD_POS = []
for qr in (0, 3):
    for qc in (0, 3):
        pos = []
        for r in range(qr, qr + 3):
            for c in range(qc, qc + 3):
                pos.append(r * 6 + c)
        QUAD_POS.append(tuple(pos))

QMASKS = []
NOT_QMASKS = []
ROT_PAIRS = []

for q in range(4):
    pos = QUAD_POS[q]
    qmask = 0
    for p in pos:
        qmask |= 1 << p

    for dirbit in (0, 1):  # 0=L, 1=R
        pairs = []
        for i in range(9):
            r, c = divmod(i, 3)
            if dirbit == 1:  # R
                nr, nc = c, 2 - r
            else:            # L
                nr, nc = 2 - c, r
            j = nr * 3 + nc
            pairs.append((1 << pos[i], 1 << pos[j]))
        ROT_PAIRS.append(tuple(pairs))
        QMASKS.append(qmask)
        NOT_QMASKS.append(ALL_MASK ^ qmask)

# Rotation order: try rotating the marble's own quadrant first.
ROTIDS_BY_CELL = []
for idx in range(36):
    r, c = divmod(idx, 6)
    q = (r // 3) * 2 + (c // 3)
    order = [2 * q, 2 * q + 1]
    for qq in range(4):
        if qq != q:
            order.append(2 * qq)
            order.append(2 * qq + 1)
    ROTIDS_BY_CELL.append(tuple(order))

MOVE_STR = [
    [
        f"{idx // 6 + 1},{idx % 6 + 1},{rotid // 2},{'L' if rotid % 2 == 0 else 'R'}"
        for rotid in range(8)
    ]
    for idx in range(36)
]

# ---------- Heuristic parameters ----------
LINE_WEIGHTS = (0, 2, 18, 160, 5000, 100000)
WIN_SCORE = 1_000_000_000
WIN_NEXT_SCORE = 200_000_000

RQ, RIDX, RROT, RMY, ROPP, REXACT, RUNSAFE, RTHREAT = range(8)


def has_win(bb: int) -> bool:
    for mask in LINE_MASKS:
        if bb & mask == mask:
            return True
    return False


def rotate_pair(a: int, b: int, rotid: int):
    ra = a & NOT_QMASKS[rotid]
    rb = b & NOT_QMASKS[rotid]
    pairs = ROT_PAIRS[rotid]
    for sm, dm in pairs:
        if a & sm:
            ra |= dm
        if b & sm:
            rb |= dm
    return ra, rb


def apply_move(me: int, other: int, idx: int, rotid: int):
    return rotate_pair(me | BITS[idx], other, rotid)


def static_eval(me: int, other: int) -> int:
    score = 0
    for mask in LINE_MASKS:
        m = me & mask
        if m:
            if not (other & mask):
                score += LINE_WEIGHTS[m.bit_count()]
        else:
            o = other & mask
            if o:
                score -= LINE_WEIGHTS[o.bit_count()]
    return score


def any_immediate_strict_win(me: int, other: int) -> bool:
    occ = me | other
    for idx in CELL_ORDER:
        bit = BITS[idx]
        if occ & bit:
            continue
        me1 = me | bit
        for rotid in ROTIDS_BY_CELL[idx]:
            m2, o2 = rotate_pair(me1, other, rotid)
            if has_win(m2) and not has_win(o2):
                return True
    return False


def count_immediate_strict_wins(me: int, other: int, cap: int = 2) -> int:
    occ = me | other
    count = 0
    for idx in CELL_ORDER:
        bit = BITS[idx]
        if occ & bit:
            continue
        me1 = me | bit
        for rotid in ROTIDS_BY_CELL[idx]:
            m2, o2 = rotate_pair(me1, other, rotid)
            if has_win(m2) and not has_win(o2):
                count += 1
                if count >= cap:
                    return count
    return count


def evaluate_root_candidate(my_after: int, opp_after: int, alpha: int, leaf_checks: int) -> int:
    occ = my_after | opp_after
    responses = []

    for idx in CELL_ORDER:
        bit = BITS[idx]
        if occ & bit:
            continue
        for rotid in ROTIDS_BY_CELL[idx]:
            opp3, my3 = apply_move(opp_after, my_after, idx, rotid)

            if has_win(opp3):
                if not has_win(my3):
                    return -WIN_SCORE
                responses.append((0, True, my3, opp3))  # draw
            elif has_win(my3):
                responses.append((WIN_SCORE, True, my3, opp3))  # opponent blundered into our win
            elif (my3 | opp3) == ALL_MASK:
                responses.append((0, True, my3, opp3))  # full-board draw
            else:
                responses.append((static_eval(my3, opp3), False, my3, opp3))

    responses.sort(key=lambda x: x[0])  # opponent chooses the move worst for us
    worst = WIN_SCORE * 2
    checked = 0
    extra_cap = leaf_checks * 2

    for quick, exact, my3, opp3 in responses:
        if exact:
            val = quick
        else:
            # Tactically verify only the most dangerous replies.
            do_check = (checked < leaf_checks) or (worst >= WIN_NEXT_SCORE and checked < extra_cap)
            if do_check:
                checked += 1
                if any_immediate_strict_win(my3, opp3):
                    val = WIN_NEXT_SCORE
                else:
                    val = quick
            else:
                val = quick

        if val < worst:
            worst = val
        if worst <= alpha:
            break

    return worst


def boards_to_bitboards(you, opponent):
    my = 0
    opp = 0
    for r in range(6):
        yr = you[r]
        orow = opponent[r]
        base = r * 6
        for c in range(6):
            if yr[c]:
                my |= 1 << (base + c)
            elif orow[c]:
                opp |= 1 << (base + c)
    return my, opp


def first_legal_move_str(my: int, opp: int) -> str:
    occ = my | opp
    for idx in range(36):
        if not (occ & BITS[idx]):
            return MOVE_STR[idx][0]
    return "1,1,0,L"


def choose_move(my: int, opp: int) -> str:
    occ = my | opp
    empties = 36 - occ.bit_count()

    if empties > 24:
        root_keep = 24
        leaf_checks = 4
        threat_scan = 16
    elif empties > 16:
        root_keep = 32
        leaf_checks = 5
        threat_scan = 20
    elif empties > 10:
        root_keep = 40
        leaf_checks = 6
        threat_scan = 24
    else:
        root_keep = 64
        leaf_checks = 8
        threat_scan = 32

    roots = []

    # Generate all legal root moves. Take an immediate win instantly.
    for idx in CELL_ORDER:
        bit = BITS[idx]
        if occ & bit:
            continue

        for rotid in ROTIDS_BY_CELL[idx]:
            my2, opp2 = apply_move(my, opp, idx, rotid)

            if has_win(my2):
                if not has_win(opp2):
                    return MOVE_STR[idx][rotid]
                exact = 0  # simultaneous win = draw
                quick = 0
            elif has_win(opp2):
                exact = -WIN_SCORE
                quick = -WIN_SCORE
            elif (my2 | opp2) == ALL_MASK:
                exact = 0  # full-board draw
                quick = 0
            else:
                exact = None
                quick = static_eval(my2, opp2)

            roots.append([quick, idx, rotid, my2, opp2, exact, False, 0])

    if not roots:
        return first_legal_move_str(my, opp)

    # Safety screen: does this move allow an immediate opponent win?
    for root in roots:
        if root[REXACT] is None:
            root[RUNSAFE] = any_immediate_strict_win(root[ROPP], root[RMY])

    safe = []
    draws = []
    unsafe = []
    losses = []

    for root in roots:
        exact = root[REXACT]
        if exact == 0:
            draws.append(root)
        elif exact == -WIN_SCORE:
            losses.append(root)
        elif not root[RUNSAFE]:
            safe.append(root)
        else:
            unsafe.append(root)

    safe.sort(key=lambda r: r[RQ], reverse=True)

    # On the most promising safe moves, estimate how many immediate winning threats we create.
    for root in safe[:min(threat_scan, len(safe))]:
        root[RTHREAT] = count_immediate_strict_wins(root[RMY], root[ROPP], cap=2)

    safe.sort(key=lambda r: (r[RTHREAT], r[RQ]), reverse=True)
    draws.sort(key=lambda r: r[RQ], reverse=True)
    unsafe.sort(key=lambda r: r[RQ], reverse=True)
    losses.sort(key=lambda r: r[RQ], reverse=True)

    selected = []
    if safe:
        selected.extend(safe[:root_keep])
        selected.extend(draws)
    elif draws:
        selected.extend(draws)
        selected.extend(unsafe[:max(8, root_keep // 2)])
    else:
        selected.extend(unsafe[:root_keep])
        selected.extend(losses[:4])

    if not selected:
        selected = roots[:1]

    best = selected[0]
    best_val = -WIN_SCORE * 2
    alpha = -WIN_SCORE * 2

    for root in selected:
        if root[REXACT] is not None:
            val = root[REXACT]
        elif root[RUNSAFE]:
            val = -WIN_SCORE
        else:
            val = evaluate_root_candidate(root[RMY], root[ROPP], alpha, leaf_checks)

        if val > best_val:
            best_val = val
            best = root
            alpha = val

    return MOVE_STR[best[RIDX]][best[RROT]]


def policy(you, opponent) -> str:
    my, opp = boards_to_bitboards(you, opponent)
    fallback = first_legal_move_str(my, opp)
    try:
        move = choose_move(my, opp)
        return move if isinstance(move, str) else fallback
    except Exception:
        return fallback
