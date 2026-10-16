
import time

BOARD_CELLS = 36
ALL_MASK = (1 << BOARD_CELLS) - 1
WIN_SCORE = 1_000_000
INF = 1_000_000_000

# Heuristic weights for uncontested 5-cell lines with n stones.
_LINE_WEIGHTS = (0, 3, 14, 85, 1200, 50000)


class _SearchTimeout(Exception):
    pass


def _build_line_masks():
    masks = []
    for dr, dc in ((0, 1), (1, 0), (1, 1), (1, -1)):
        for r in range(6):
            for c in range(6):
                r2 = r + 4 * dr
                c2 = c + 4 * dc
                if 0 <= r2 < 6 and 0 <= c2 < 6:
                    m = 0
                    for k in range(5):
                        m |= 1 << ((r + k * dr) * 6 + (c + k * dc))
                    masks.append(m)
    return tuple(dict.fromkeys(masks))


_LINE_MASKS = _build_line_masks()

_H_START = sum(1 << (r * 6 + c) for r in range(6) for c in (0, 1))
_V_START = sum(1 << (r * 6 + c) for r in (0, 1) for c in range(6))
_DR_START = sum(1 << (r * 6 + c) for r in (0, 1) for c in (0, 1))
_DL_START = sum(1 << (r * 6 + c) for r in (0, 1) for c in (4, 5))


def _has_win(bb, H=_H_START, V=_V_START, DR=_DR_START, DL=_DL_START):
    x = bb & (bb >> 1) & (bb >> 2) & (bb >> 3) & (bb >> 4)
    if x & H:
        return True
    x = bb & (bb >> 6) & (bb >> 12) & (bb >> 18) & (bb >> 24)
    if x & V:
        return True
    x = bb & (bb >> 7) & (bb >> 14) & (bb >> 21) & (bb >> 28)
    if x & DR:
        return True
    x = bb & (bb >> 5) & (bb >> 10) & (bb >> 15) & (bb >> 20)
    return bool(x & DL)


def _build_rotations():
    tables = []
    masks = []
    outs = []

    for q in range(4):
        r0 = 0 if q < 2 else 3
        c0 = 0 if (q % 2) == 0 else 3

        qmask = 0
        for rr in range(3):
            for cc in range(3):
                qmask |= 1 << ((r0 + rr) * 6 + (c0 + cc))

        left = {}
        right = {}
        for pat in range(512):
            abs_in = 0
            abs_l = 0
            abs_r = 0
            for rr in range(3):
                for cc in range(3):
                    i = rr * 3 + cc
                    if (pat >> i) & 1:
                        old_idx = (r0 + rr) * 6 + (c0 + cc)
                        abs_in |= 1 << old_idx

                        # L: anticlockwise, old local (rr, cc) -> (2-cc, rr)
                        nl_r = 2 - cc
                        nl_c = rr
                        abs_l |= 1 << ((r0 + nl_r) * 6 + (c0 + nl_c))

                        # R: clockwise, old local (rr, cc) -> (cc, 2-rr)
                        nr_r = cc
                        nr_c = 2 - rr
                        abs_r |= 1 << ((r0 + nr_r) * 6 + (c0 + nr_c))

            left[abs_in] = abs_l
            right[abs_in] = abs_r

        tables.append(left)
        masks.append(qmask)
        outs.append(ALL_MASK ^ qmask)

        tables.append(right)
        masks.append(qmask)
        outs.append(ALL_MASK ^ qmask)

    return tuple(tables), tuple(masks), tuple(outs)


_ROT_TABLES, _ROT_MASKS, _ROT_OUTS = _build_rotations()

_MOVE_STRINGS = tuple(
    tuple(
        f"{idx // 6 + 1},{idx % 6 + 1},{rot // 2},{'L' if (rot & 1) == 0 else 'R'}"
        for rot in range(8)
    )
    for idx in range(36)
)

_QUAD_CENTER_MASK = (
    (1 << (1 * 6 + 1)) |
    (1 << (1 * 6 + 4)) |
    (1 << (4 * 6 + 1)) |
    (1 << (4 * 6 + 4))
)

_BOARD_CENTER_MASK = (
    (1 << (2 * 6 + 2)) |
    (1 << (2 * 6 + 3)) |
    (1 << (3 * 6 + 2)) |
    (1 << (3 * 6 + 3))
)

_INNER_MASK = sum(1 << (r * 6 + c) for r in range(1, 5) for c in range(1, 5))

_FALLBACK_PREFS = (
    (1 * 6 + 1, 0),  # quadrant centers
    (1 * 6 + 4, 2),
    (4 * 6 + 1, 4),
    (4 * 6 + 4, 6),
    (2 * 6 + 2, 2),  # board-center cells, rotating another quadrant
    (2 * 6 + 3, 0),
    (3 * 6 + 2, 0),
    (3 * 6 + 3, 0),
)


def _fallback_move(p, q):
    empty = ALL_MASK ^ (p | q)
    for idx, rot in _FALLBACK_PREFS:
        if empty & (1 << idx):
            return _MOVE_STRINGS[idx][rot]
    if empty:
        bit = empty & -empty
        idx = bit.bit_length() - 1
        return _MOVE_STRINGS[idx][0]
    return "1,1,0,L"


def _bits_from_arrays(you, opponent):
    y = 0
    o = 0
    for r in range(6):
        yr = you[r]
        orow = opponent[r]
        base = r * 6
        for c in range(6):
            bit = 1 << (base + c)
            if yr[c]:
                y |= bit
            elif orow[c]:
                o |= bit
    return y, o


def _static_eval_side(p, q):
    score = 0
    p2 = p3 = p4 = 0
    q2 = q3 = q4 = 0
    weights = _LINE_WEIGHTS

    for m in _LINE_MASKS:
        pc = (p & m).bit_count()
        qc = (q & m).bit_count()

        if qc == 0:
            score += weights[pc]
            if pc == 2:
                p2 += 1
            elif pc == 3:
                p3 += 1
            elif pc == 4:
                p4 += 1
        elif pc == 0:
            score -= weights[qc]
            if qc == 2:
                q2 += 1
            elif qc == 3:
                q3 += 1
            elif qc == 4:
                q4 += 1

    # Multiple threats are much stronger than isolated threats.
    score += 5 * (p2 - q2)
    score += 35 * (p3 * p3 - q3 * q3)
    score += 250 * (p4 * p4 - q4 * q4)

    # Tempo: if both sides have threats, the side to move has the initiative.
    if p4:
        score += 1600 + 250 * p4
    if q4:
        score -= 1100 + 220 * q4
    if p4 and q4:
        score += 900

    if p3:
        score += 70 + 15 * p3
    if q3:
        score -= 55 + 12 * q3
    if p3 and q3:
        score += 25

    # Stable and central stones are useful in Pentago.
    score += 24 * ((p & _QUAD_CENTER_MASK).bit_count() - (q & _QUAD_CENTER_MASK).bit_count())
    score += 10 * ((p & _BOARD_CENTER_MASK).bit_count() - (q & _BOARD_CENTER_MASK).bit_count())
    score += 3 * ((p & _INNER_MASK).bit_count() - (q & _INNER_MASK).bit_count())

    return score


def policy(you, opponent) -> str:
    p = q = 0
    best_string = None

    try:
        p, q = _bits_from_arrays(you, opponent)
        best_string = _fallback_move(p, q)

        occ = p | q
        if occ == 0:
            return "2,2,0,L"

        now = time.perf_counter
        start = now()
        deadline = start + 0.88

        eval_cache = {}
        winmove_cache = {}
        tt = {}
        nodes = 0
        selective_mode = False

        def eval_side(a, b):
            key = (a, b)
            try:
                return eval_cache[key]
            except KeyError:
                v = _static_eval_side(a, b)
                eval_cache[key] = v
                return v

        def ordered_moves(a, b, limit=0):
            empty = ALL_MASK ^ (a | b)
            if not empty:
                return []

            will_fill = (empty & (empty - 1)) == 0
            tables = _ROT_TABLES
            masks = _ROT_MASKS
            outs = _ROT_OUTS
            has_win = _has_win
            eval_local = eval_side

            b_rots = [0] * 8
            for rot in range(8):
                mask = masks[rot]
                b_rots[rot] = (b & outs[rot]) | tables[rot][b & mask]

            seen = set()
            moves = []
            e = empty

            while e:
                bit = e & -e
                e ^= bit
                idx = bit.bit_length() - 1
                a_place = a | bit

                for rot in range(8):
                    mask = masks[rot]
                    aa = (a_place & outs[rot]) | tables[rot][a_place & mask]
                    bb = b_rots[rot]

                    state = (aa, bb)
                    if state in seen:
                        continue
                    seen.add(state)

                    aw = has_win(aa)
                    bw = has_win(bb)

                    term = None
                    if aw or bw or will_fill:
                        if aw and not bw:
                            term = WIN_SCORE
                        elif bw and not aw:
                            term = -WIN_SCORE
                        else:
                            term = 0
                        score = term
                    else:
                        # After our move, opponent is to move.
                        score = -eval_local(bb, aa)

                    moves.append((score, idx, rot, aa, bb, term))

            moves.sort(key=lambda x: x[0], reverse=True)
            if limit and len(moves) > limit:
                del moves[limit:]
            return moves

        def has_immediate_win(a, b):
            key = (a, b)
            try:
                return winmove_cache[key]
            except KeyError:
                pass

            empty = ALL_MASK ^ (a | b)
            if not empty:
                winmove_cache[key] = False
                return False

            tables = _ROT_TABLES
            masks = _ROT_MASKS
            outs = _ROT_OUTS
            has_win = _has_win

            b_rots = [0] * 8
            for rot in range(8):
                mask = masks[rot]
                b_rots[rot] = (b & outs[rot]) | tables[rot][b & mask]

            seen = set()
            e = empty
            while e:
                bit = e & -e
                e ^= bit
                a_place = a | bit

                for rot in range(8):
                    mask = masks[rot]
                    aa = (a_place & outs[rot]) | tables[rot][a_place & mask]
                    bb = b_rots[rot]
                    state = (aa, bb)
                    if state in seen:
                        continue
                    seen.add(state)

                    if has_win(aa) and not has_win(bb):
                        winmove_cache[key] = True
                        return True

            winmove_cache[key] = False
            return False

        def search_limit(depth, empty_count):
            if (not selective_mode) or depth <= 1:
                return 0
            if empty_count <= 10:
                return 0
            if empty_count > 26:
                return 16 if depth >= 3 else 24
            if empty_count > 20:
                return 22 if depth >= 3 else 32
            if empty_count > 14:
                return 30 if depth >= 3 else 44
            return 48

        def negamax(a, b, depth, alpha, beta, ply):
            nonlocal nodes

            nodes += 1
            if (nodes & 31) == 0 and now() > deadline:
                raise _SearchTimeout()

            if depth <= 0:
                return eval_side(a, b)

            empty_count = (ALL_MASK ^ (a | b)).bit_count()
            if empty_count <= 0:
                return 0

            limit = search_limit(depth, empty_count)
            tt_key = (a, b, depth, limit)
            try:
                return tt[tt_key]
            except KeyError:
                pass

            moves = ordered_moves(a, b, limit)
            if not moves:
                return 0

            best = -INF
            dist = ply + 1

            for score, idx, rot, aa, bb, term in moves:
                if term is not None:
                    if term > 0:
                        val = term - dist
                    elif term < 0:
                        val = term + dist
                    else:
                        val = 0
                elif depth == 1:
                    val = score
                else:
                    val = -negamax(bb, aa, depth - 1, -beta, -alpha, dist)

                if val > best:
                    best = val
                if best > alpha:
                    alpha = best
                if alpha >= beta:
                    return best

            tt[tt_key] = best
            return best

        root_moves = ordered_moves(p, q, 0)
        if not root_moves:
            return best_string

        # Take an immediate non-drawing win.
        for m in root_moves:
            if m[5] is not None and m[5] > 0:
                return _MOVE_STRINGS[m[1]][m[2]]

        best_move = root_moves[0]
        best_string = _MOVE_STRINGS[best_move[1]][best_move[2]]

        # Quick safe fallback: prefer a move that does not allow an immediate opponent win.
        safe_deadline = start + 0.08
        for m in root_moves:
            if now() > safe_deadline:
                break
            term = m[5]
            if term is not None:
                if term >= 0:
                    best_move = m
                    best_string = _MOVE_STRINGS[m[1]][m[2]]
                    break
                continue

            # After our root move, m[4] is opponent's bitboard and m[3] is ours.
            if not has_immediate_win(m[4], m[3]):
                best_move = m
                best_string = _MOVE_STRINGS[m[1]][m[2]]
                break

        empties = (ALL_MASK ^ occ).bit_count()
        if empties > 28:
            max_depth = 3
        elif empties > 21:
            max_depth = 4
        elif empties > 15:
            max_depth = 5
        elif empties > 10:
            max_depth = 6
        else:
            max_depth = empties
        max_depth = max(1, min(max_depth, empties))

        # Depth 2 is exhaustive; deeper searches are selective and time-limited.
        for total_depth in range(2, max_depth + 1):
            if now() > deadline:
                break

            selective_mode = total_depth >= 3
            alpha = -INF
            best_val = -INF
            best_this = None
            score_map = {}

            root_i = 0
            for m in root_moves:
                root_i += 1
                if (root_i & 7) == 0 and now() > deadline:
                    raise _SearchTimeout()

                score, idx, rot, aa, bb, term = m

                if term is not None:
                    if term > 0:
                        val = term - 1
                    elif term < 0:
                        val = term + 1
                    else:
                        val = 0
                else:
                    val = -negamax(bb, aa, total_depth - 1, -INF, -alpha, 1)

                score_map[(aa, bb)] = val

                if val > best_val:
                    best_val = val
                    best_this = m
                if val > alpha:
                    alpha = val

            if best_this is not None:
                best_move = best_this
                best_string = _MOVE_STRINGS[best_move[1]][best_move[2]]

                updated = []
                for m in root_moves:
                    updated_score = score_map.get((m[3], m[4]), m[0])
                    updated.append((updated_score, m[1], m[2], m[3], m[4], m[5]))
                updated.sort(key=lambda x: x[0], reverse=True)
                root_moves = updated

                if (not selective_mode) and best_val > WIN_SCORE // 2:
                    break

        return best_string

    except _SearchTimeout:
        if best_string is not None:
            return best_string
        return _fallback_move(p, q)
    except Exception:
        if best_string is not None:
            return best_string
        try:
            return _fallback_move(p, q)
        except Exception:
            return "1,1,0,L"
