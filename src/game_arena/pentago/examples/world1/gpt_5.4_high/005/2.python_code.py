
import time

# =========================
# Constants and precompute
# =========================

FULL_MASK = (1 << 36) - 1
WIN_SCORE = 1_000_000
INF = 10 ** 12

# Heuristic values for uncontested 5-cell segments.
# Index = number of marbles in that segment.
LINE_VALUE = (0, 3, 18, 120, 2000, 0)

# Global timing state
_DEADLINE = 0.0
_NODE_COUNT = 0


def _build_win_masks():
    masks = []

    # Horizontal 5-segments
    for r in range(6):
        for c in range(2):
            m = 0
            for k in range(5):
                idx = r * 6 + (c + k)
                m |= 1 << idx
            masks.append(m)

    # Vertical 5-segments
    for c in range(6):
        for r in range(2):
            m = 0
            for k in range(5):
                idx = (r + k) * 6 + c
                m |= 1 << idx
            masks.append(m)

    # Diagonal down-right 5-segments
    for r in range(2):
        for c in range(2):
            m = 0
            for k in range(5):
                idx = (r + k) * 6 + (c + k)
                m |= 1 << idx
            masks.append(m)

    # Diagonal down-left 5-segments
    for r in range(2):
        for c in range(4, 6):
            m = 0
            for k in range(5):
                idx = (r + k) * 6 + (c - k)
                m |= 1 << idx
            masks.append(m)

    return tuple(masks)


WIN_MASKS = _build_win_masks()


def _build_rotation_data():
    # ROT_MASK[q] = bitmask of cells in quadrant q
    # ROT_PAIRS[q][d] = tuple of (src_bit, dst_bit) for rotating that quadrant
    # BIT_AFTER_ROT[q][d][pos] = bitmask of where a newly placed stone at pos ends up
    # d: 0 = L, 1 = R
    rot_mask = [0] * 4
    rot_pairs = [[None, None] for _ in range(4)]
    bit_after = [[None, None] for _ in range(4)]

    for q in range(4):
        r0 = 0 if q < 2 else 3
        c0 = 0 if (q % 2) == 0 else 3

        mask = 0
        for i in range(3):
            for j in range(3):
                src = (r0 + i) * 6 + (c0 + j)
                mask |= 1 << src
        rot_mask[q] = mask

        for d in (0, 1):
            pairs = []
            pos_map = list(range(36))

            for i in range(3):
                for j in range(3):
                    src = (r0 + i) * 6 + (c0 + j)
                    if d == 0:  # L
                        ni, nj = 2 - j, i
                    else:       # R
                        ni, nj = j, 2 - i
                    dst = (r0 + ni) * 6 + (c0 + nj)
                    pairs.append((1 << src, 1 << dst))
                    pos_map[src] = dst

            rot_pairs[q][d] = tuple(pairs)
            bit_after[q][d] = tuple(1 << pos_map[p] for p in range(36))

    return rot_mask, rot_pairs, bit_after


ROT_MASK, ROT_PAIRS, BIT_AFTER_ROT = _build_rotation_data()


def _build_position_priority():
    counts = [0] * 36
    for m in WIN_MASKS:
        mm = m
        while mm:
            lsb = mm & -mm
            pos = lsb.bit_length() - 1
            counts[pos] += 1
            mm ^= lsb

    def key(p):
        r, c = divmod(p, 6)
        # Prefer cells that lie in more winning segments, then closer to center
        center_bonus = -(abs(r - 2.5) + abs(c - 2.5))
        return (counts[p], center_bonus, -p)

    order = sorted(range(36), key=key, reverse=True)
    return tuple(order)


POSITION_PRIORITY = _build_position_priority()


# =========================
# Core board operations
# =========================

def _rotate_bb(bb, q, d):
    sub = bb & ROT_MASK[q]
    res = bb & ~ROT_MASK[q]
    for src_bit, dst_bit in ROT_PAIRS[q][d]:
        if sub & src_bit:
            res |= dst_bit
    return res


def _rotated_variants(bb):
    return (
        (_rotate_bb(bb, 0, 0), _rotate_bb(bb, 0, 1)),
        (_rotate_bb(bb, 1, 0), _rotate_bb(bb, 1, 1)),
        (_rotate_bb(bb, 2, 0), _rotate_bb(bb, 2, 1)),
        (_rotate_bb(bb, 3, 0), _rotate_bb(bb, 3, 1)),
    )


def _has_win(bb):
    for mask in WIN_MASKS:
        if (bb & mask) == mask:
            return True
    return False


def _terminal_score(cur2, oth2, empties_left_before_move, depth):
    cur_win = _has_win(cur2)
    oth_win = _has_win(oth2)

    if cur_win:
        if oth_win:
            return 0
        return WIN_SCORE + depth

    if oth_win:
        return -WIN_SCORE - depth

    if empties_left_before_move == 1:
        return 0

    return None


def _evaluate(cur, oth):
    score = 0
    for mask in WIN_MASKS:
        a = (cur & mask).bit_count()
        b = (oth & mask).bit_count()
        if a and b:
            continue
        if a:
            score += LINE_VALUE[a]
        elif b:
            score -= LINE_VALUE[b]
    return score


def _to_bitboards(you, opponent):
    cur = 0
    oth = 0
    for r in range(6):
        yr = you[r]
        orow = opponent[r]
        base = r * 6
        for c in range(6):
            bit = 1 << (base + c)
            if yr[c]:
                cur |= bit
            elif orow[c]:
                oth |= bit
    return cur, oth


def _move_to_string(move):
    pos, q, d = move
    r, c = divmod(pos, 6)
    return f"{r+1},{c+1},{q},{'L' if d == 0 else 'R'}"


def _fallback_from_mask(occ):
    for pos in POSITION_PRIORITY:
        if (occ & (1 << pos)) == 0:
            return (pos, 0, 0)
    return (0, 0, 0)


def _simple_legal_move_from_arrays(you, opponent):
    for r in range(6):
        for c in range(6):
            if not you[r][c] and not opponent[r][c]:
                return f"{r+1},{c+1},0,L"
    return "1,1,0,L"


def _check_time():
    global _NODE_COUNT
    _NODE_COUNT += 1
    if (_NODE_COUNT & 1023) == 0 and time.perf_counter() > _DEADLINE:
        raise TimeoutError


# =========================
# Search
# =========================

def _search(cur, oth, depth, alpha, beta, empties_left):
    _check_time()

    if depth == 0:
        return _evaluate(cur, oth)

    occ = cur | oth
    empties_mask = FULL_MASK ^ occ
    positions = [p for p in POSITION_PRIORITY if empties_mask & (1 << p)]

    rot_cur = _rotated_variants(cur)
    rot_oth = _rotated_variants(oth)

    best = -INF

    if depth > 1:
        move_infos = []

        for pos in positions:
            for q in range(4):
                # L
                cur2 = rot_cur[q][0] | BIT_AFTER_ROT[q][0][pos]
                oth2 = rot_oth[q][0]
                term = _terminal_score(cur2, oth2, empties_left, depth)
                if term is not None and term >= WIN_SCORE:
                    return term
                order = term if term is not None else _evaluate(cur2, oth2)
                move_infos.append((order, cur2, oth2, term))

                # R
                cur2 = rot_cur[q][1] | BIT_AFTER_ROT[q][1][pos]
                oth2 = rot_oth[q][1]
                term = _terminal_score(cur2, oth2, empties_left, depth)
                if term is not None and term >= WIN_SCORE:
                    return term
                order = term if term is not None else _evaluate(cur2, oth2)
                move_infos.append((order, cur2, oth2, term))

        move_infos.sort(key=lambda x: x[0], reverse=True)

        for _, cur2, oth2, term in move_infos:
            if term is None:
                val = -_search(oth2, cur2, depth - 1, -beta, -alpha, empties_left - 1)
            else:
                val = term

            if val > best:
                best = val
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break

    else:
        for pos in positions:
            for q in range(4):
                # L
                cur2 = rot_cur[q][0] | BIT_AFTER_ROT[q][0][pos]
                oth2 = rot_oth[q][0]
                term = _terminal_score(cur2, oth2, empties_left, depth)
                if term is not None:
                    if term >= WIN_SCORE:
                        return term
                    val = term
                else:
                    val = _evaluate(cur2, oth2)

                if val > best:
                    best = val
                if best > alpha:
                    alpha = best
                if alpha >= beta:
                    return best

                # R
                cur2 = rot_cur[q][1] | BIT_AFTER_ROT[q][1][pos]
                oth2 = rot_oth[q][1]
                term = _terminal_score(cur2, oth2, empties_left, depth)
                if term is not None:
                    if term >= WIN_SCORE:
                        return term
                    val = term
                else:
                    val = _evaluate(cur2, oth2)

                if val > best:
                    best = val
                if best > alpha:
                    alpha = best
                if alpha >= beta:
                    return best

    if best == -INF:
        return 0
    return best


def _root_search(cur, oth, depth, empties_left):
    occ = cur | oth
    empties_mask = FULL_MASK ^ occ
    positions = [p for p in POSITION_PRIORITY if empties_mask & (1 << p)]

    rot_cur = _rotated_variants(cur)
    rot_oth = _rotated_variants(oth)

    best = -INF
    best_move = None
    alpha = -INF
    beta = INF

    if depth > 1:
        move_infos = []

        for pos in positions:
            for q in range(4):
                # L
                cur2 = rot_cur[q][0] | BIT_AFTER_ROT[q][0][pos]
                oth2 = rot_oth[q][0]
                term = _terminal_score(cur2, oth2, empties_left, depth)
                if term is not None and term >= WIN_SCORE:
                    return term, (pos, q, 0)
                order = term if term is not None else _evaluate(cur2, oth2)
                move_infos.append((order, pos, q, 0, cur2, oth2, term))

                # R
                cur2 = rot_cur[q][1] | BIT_AFTER_ROT[q][1][pos]
                oth2 = rot_oth[q][1]
                term = _terminal_score(cur2, oth2, empties_left, depth)
                if term is not None and term >= WIN_SCORE:
                    return term, (pos, q, 1)
                order = term if term is not None else _evaluate(cur2, oth2)
                move_infos.append((order, pos, q, 1, cur2, oth2, term))

        move_infos.sort(key=lambda x: x[0], reverse=True)

        for _, pos, q, d, cur2, oth2, term in move_infos:
            if term is None:
                val = -_search(oth2, cur2, depth - 1, -beta, -alpha, empties_left - 1)
            else:
                val = term

            if val > best:
                best = val
                best_move = (pos, q, d)
            if best > alpha:
                alpha = best

    else:
        for pos in positions:
            for q in range(4):
                # L
                cur2 = rot_cur[q][0] | BIT_AFTER_ROT[q][0][pos]
                oth2 = rot_oth[q][0]
                term = _terminal_score(cur2, oth2, empties_left, depth)
                if term is not None:
                    if term >= WIN_SCORE:
                        return term, (pos, q, 0)
                    val = term
                else:
                    val = _evaluate(cur2, oth2)

                if val > best:
                    best = val
                    best_move = (pos, q, 0)
                if best > alpha:
                    alpha = best

                # R
                cur2 = rot_cur[q][1] | BIT_AFTER_ROT[q][1][pos]
                oth2 = rot_oth[q][1]
                term = _terminal_score(cur2, oth2, empties_left, depth)
                if term is not None:
                    if term >= WIN_SCORE:
                        return term, (pos, q, 1)
                    val = term
                else:
                    val = _evaluate(cur2, oth2)

                if val > best:
                    best = val
                    best_move = (pos, q, 1)
                if best > alpha:
                    alpha = best

    if best_move is None:
        best_move = _fallback_from_mask(occ)
        best = 0

    return best, best_move


# =========================
# Required API
# =========================

def policy(you, opponent) -> str:
    best_move = None
    try:
        cur, oth = _to_bitboards(you, opponent)
        occ = cur | oth
        empties_left = 36 - occ.bit_count()

        best_move = _fallback_from_mask(occ)

        global _DEADLINE, _NODE_COUNT
        _DEADLINE = time.perf_counter() + 0.95
        _NODE_COUNT = 0

        # Depth schedule:
        # - depth 2 is the main tactical workhorse
        # - depth 3 only in smaller late-game positions
        max_depth = 3 if empties_left <= 10 else 2

        for depth in range(1, max_depth + 1):
            val, move = _root_search(cur, oth, depth, empties_left)
            if move is not None:
                best_move = move
            if val >= WIN_SCORE:
                break

        return _move_to_string(best_move)

    except TimeoutError:
        if best_move is not None:
            return _move_to_string(best_move)
        return _simple_legal_move_from_arrays(you, opponent)
    except Exception:
        if best_move is not None:
            return _move_to_string(best_move)
        return _simple_legal_move_from_arrays(you, opponent)
