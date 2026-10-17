
import time

# Pentago policy for a standard 6x6 board.
# Required API:
#     policy(you, opponent) -> str

BOARD_N = 6
NUM_CELLS = 36
FULL_MASK = (1 << NUM_CELLS) - 1

WIN = 100000000
INF = 10 ** 12


class SearchTimeout(Exception):
    pass


def _idx(r, c):
    return r * 6 + c


def _build_win_masks():
    masks = []

    # Horizontal 5-in-a-row segments.
    for r in range(6):
        for c in range(2):
            m = 0
            for k in range(5):
                m |= 1 << _idx(r, c + k)
            masks.append(m)

    # Vertical 5-in-a-row segments.
    for r in range(2):
        for c in range(6):
            m = 0
            for k in range(5):
                m |= 1 << _idx(r + k, c)
            masks.append(m)

    # Down-right diagonals.
    for r in range(2):
        for c in range(2):
            m = 0
            for k in range(5):
                m |= 1 << _idx(r + k, c + k)
            masks.append(m)

    # Down-left diagonals.
    for r in range(2):
        for c in range(4, 6):
            m = 0
            for k in range(5):
                m |= 1 << _idx(r + k, c - k)
            masks.append(m)

    return tuple(masks)


WIN_MASKS = _build_win_masks()


# Rotation precomputation.
ROT_QUAD = []
ROT_DIR = []
ROT_PAIRS = []
ROT_CLEAR_MASK = []

for q in range(4):
    br = (q // 2) * 3
    bc = (q % 2) * 3

    qmask = 0
    for rr in range(3):
        for cc in range(3):
            qmask |= 1 << _idx(br + rr, bc + cc)

    for d in ("L", "R"):
        pairs = []
        for rr in range(3):
            for cc in range(3):
                old_pos = _idx(br + rr, bc + cc)
                if d == "R":
                    nr, nc = cc, 2 - rr
                else:
                    nr, nc = 2 - cc, rr
                new_pos = _idx(br + nr, bc + nc)
                pairs.append((1 << old_pos, 1 << new_pos))

        ROT_QUAD.append(q)
        ROT_DIR.append(d)
        ROT_PAIRS.append(tuple(pairs))
        ROT_CLEAR_MASK.append(FULL_MASK ^ qmask)


def _rotate_bits(bits, rid):
    res = bits & ROT_CLEAR_MASK[rid]
    for old_bit, new_bit in ROT_PAIRS[rid]:
        if bits & old_bit:
            res |= new_bit
    return res


# ROT_SINGLE[rid][pos] is the rotated location of a single stone at pos.
ROT_SINGLE = tuple(
    tuple(_rotate_bits(1 << pos, rid) for pos in range(NUM_CELLS))
    for rid in range(8)
)


def _build_cell_weights():
    cover = [0] * NUM_CELLS
    for m in WIN_MASKS:
        b = m
        while b:
            lsb = b & -b
            cover[lsb.bit_length() - 1] += 1
            b ^= lsb

    weights = []
    for r in range(6):
        for c in range(6):
            # Reward centrality and participation in many winning lines.
            dist = abs(r - 2.5) + abs(c - 2.5)
            center_bonus = max(0, int(8 - 2 * dist))
            weights.append(2 * cover[_idx(r, c)] + center_bonus)
    return tuple(weights)


CELL_W = _build_cell_weights()

# Unblocked line weights. Four-in-a-row is very important because it is
# usually an immediate placement threat.
LINE_W = (0, 2, 15, 120, 2500, 200000)


def _has_win(bits):
    for m in WIN_MASKS:
        if (bits & m) == m:
            return True
    return False


def _bit_weight(bits):
    s = 0
    while bits:
        lsb = bits & -bits
        s += CELL_W[lsb.bit_length() - 1]
        bits ^= lsb
    return s


def _evaluate(me, opp):
    # Positive means good for me.
    score = _bit_weight(me) - _bit_weight(opp)

    for m in WIN_MASKS:
        mb = me & m
        ob = opp & m

        if ob == 0:
            score += LINE_W[mb.bit_count()]
        if mb == 0:
            score -= LINE_W[ob.bit_count()]

    return score


def _arrays_to_bits(you, opponent):
    me = 0
    opp = 0
    for r in range(6):
        yr = you[r]
        orow = opponent[r]
        for c in range(6):
            bit = 1 << _idx(r, c)
            if int(yr[c]):
                me |= bit
            elif int(orow[c]):
                opp |= bit
    return me, opp


def _fallback_from_arrays(you, opponent):
    # Guaranteed legal under the problem statement if arrays are valid.
    for r in range(6):
        for c in range(6):
            try:
                if int(you[r][c]) == 0 and int(opponent[r][c]) == 0:
                    return f"{r + 1},{c + 1},0,L"
            except Exception:
                pass
    return "1,1,0,L"


def _format_move(pos, rid):
    return f"{pos // 6 + 1},{pos % 6 + 1},{ROT_QUAD[rid]},{ROT_DIR[rid]}"


def _iter_moves(me, opp):
    # Yields: pos, rotation_id, new_me_bits, new_opp_bits
    empty = FULL_MASK & ~(me | opp)

    # Rotation of existing stones is independent of the placement position.
    rot_me = tuple(_rotate_bits(me, rid) for rid in range(8))
    rot_opp = tuple(_rotate_bits(opp, rid) for rid in range(8))

    while empty:
        lsb = empty & -empty
        empty ^= lsb
        pos = lsb.bit_length() - 1

        for rid in range(8):
            nm = rot_me[rid] | ROT_SINGLE[rid][pos]
            no = rot_opp[rid]
            yield pos, rid, nm, no


def _count_clean_winning_placements(me, opp, cap=3):
    # Counts distinct placement cells from which the side to move has at least
    # one clean winning rotation. Capped for speed.
    empty = FULL_MASK & ~(me | opp)
    if not empty:
        return 0

    rot_me = tuple(_rotate_bits(me, rid) for rid in range(8))
    rot_opp = tuple(_rotate_bits(opp, rid) for rid in range(8))

    count = 0
    while empty:
        lsb = empty & -empty
        empty ^= lsb
        pos = lsb.bit_length() - 1

        for rid in range(8):
            nm = rot_me[rid] | ROT_SINGLE[rid][pos]
            if _has_win(nm):
                no = rot_opp[rid]
                if not _has_win(no):
                    count += 1
                    if count >= cap:
                        return count
                    break

    return count


def _negamax(me, opp, depth, alpha, beta, deadline, selective=False):
    if time.perf_counter() > deadline:
        raise SearchTimeout

    mw = _has_win(me)
    ow = _has_win(opp)
    if mw and ow:
        return 0
    if mw:
        return WIN
    if ow:
        return -WIN

    empty_mask = FULL_MASK & ~(me | opp)
    if empty_mask == 0:
        return 0

    if depth <= 0:
        return _evaluate(me, opp)

    last_move = (empty_mask & (empty_mask - 1)) == 0

    # Selective deeper search: scan all moves for immediate wins, then search
    # the most plausible non-terminal candidates.
    if selective and depth >= 2:
        candidates = []

        for _, _, nm, no in _iter_moves(me, opp):
            nmw = _has_win(nm)
            now = _has_win(no)

            if nmw and not now:
                return WIN + depth
            elif nmw and now:
                candidates.append((0, 0, nm, no, True))
            elif now:
                candidates.append((-WIN - depth, -WIN - depth, nm, no, True))
            elif last_move:
                candidates.append((0, 0, nm, no, True))
            else:
                q = _evaluate(nm, no)
                candidates.append((q, 0, nm, no, False))

        if not candidates:
            return 0

        candidates.sort(key=lambda x: x[0], reverse=True)

        # Search more broadly in late game, selectively in early game.
        move_count = len(candidates)
        if move_count <= 112:
            limit = move_count
        else:
            limit = 112

        best = -INF
        for _, terminal_value, nm, no, is_terminal in candidates[:limit]:
            if is_terminal:
                val = terminal_value
            else:
                val = -_negamax(no, nm, depth - 1, -beta, -alpha, deadline, selective)

            if val > best:
                best = val
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break

        return best

    # Exact shallow search.
    best = -INF

    for _, _, nm, no in _iter_moves(me, opp):
        nmw = _has_win(nm)
        now = _has_win(no)

        if nmw and not now:
            val = WIN + depth
        elif nmw and now:
            val = 0
        elif now:
            val = -WIN - depth
        elif last_move:
            val = 0
        elif depth == 1:
            # Equivalent to -evaluate(no, nm), because evaluation is symmetric.
            val = _evaluate(nm, no)
        else:
            val = -_negamax(no, nm, depth - 1, -beta, -alpha, deadline, selective)

        if val > best:
            best = val
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break

    return best


def _choose_move(me, opp, fallback):
    deadline = time.perf_counter() + 0.88

    root_records = []
    seen_states = set()

    # Generate root moves, deduplicating identical final states.
    for pos, rid, nm, no in _iter_moves(me, opp):
        key = (nm, no)
        if key in seen_states:
            continue
        seen_states.add(key)

        nmw = _has_win(nm)
        now = _has_win(no)

        # Always take a clean immediate win.
        if nmw and not now:
            return _format_move(pos, rid)

        if nmw and now:
            quick = 0
        elif now:
            quick = -WIN
        else:
            quick = _evaluate(nm, no)

        root_records.append((quick, pos, rid, nm, no, nmw, now))

    if not root_records:
        return fallback

    # Good move ordering helps if time becomes tight.
    root_records.sort(key=lambda x: x[0], reverse=True)

    best_move = fallback
    best_score = -INF
    scored = []

    for quick, pos, rid, nm, no, nmw, now in root_records:
        if time.perf_counter() > deadline:
            break

        move_str = _format_move(pos, rid)

        if nmw and now:
            score = 0
        elif now:
            score = -WIN
        else:
            try:
                # Exact opponent reply search.
                opp_value = _negamax(no, nm, 1, -INF, INF, deadline, selective=False)
                score = -opp_value
            except SearchTimeout:
                break

            # Reward positions that create immediate clean threats for us.
            # Multiple distinct winning placements are especially valuable.
            if score > -WIN // 2:
                threats = _count_clean_winning_placements(nm, no, cap=3)
                if threats == 1:
                    score += 8000
                elif threats >= 2:
                    score += 90000 + 25000 * threats

            # Tiny root-position tiebreaker.
            score += quick // 50

        scored.append((score, pos, rid, nm, no))

        if score > best_score:
            best_score = score
            best_move = move_str

    # If time remains, try a selective deeper search on the best candidates.
    # This is conservative: it only replaces the current choice if it finds
    # a clearly better deeper score.
    if scored and time.perf_counter() < deadline - 0.04:
        scored.sort(key=lambda x: x[0], reverse=True)
        for base_score, pos, rid, nm, no in scored[:10]:
            if time.perf_counter() > deadline - 0.02:
                break

            # Terminal root states need no deeper analysis.
            if _has_win(nm) or _has_win(no):
                continue

            try:
                deep_score = -_negamax(no, nm, 2, -INF, INF, deadline, selective=True)
            except SearchTimeout:
                break

            combined = deep_score + base_score // 100
            if combined > best_score:
                best_score = combined
                best_move = _format_move(pos, rid)

    return best_move


def policy(you, opponent) -> str:
    fallback = _fallback_from_arrays(you, opponent)

    try:
        me, opp = _arrays_to_bits(you, opponent)
        return _choose_move(me, opp, fallback)
    except Exception:
        # Never risk returning an illegal/non-string move because of an
        # unexpected runtime issue.
        return fallback
