
import time

# Pentago policy: bitboard tactical search + alpha-beta.
# Required API:
#     def policy(you, opponent) -> str

N = 6
CELLS = 36
FULL_BOARD = (1 << CELLS) - 1

WIN_SCORE = 100_000_000
INF = 1_000_000_000

# ---------------------------------------------------------------------------
# Precomputation
# ---------------------------------------------------------------------------

def _make_win_masks():
    masks = []
    directions = ((0, 1), (1, 0), (1, 1), (1, -1))
    for r in range(6):
        for c in range(6):
            for dr, dc in directions:
                r2 = r + 4 * dr
                c2 = c + 4 * dc
                if 0 <= r2 < 6 and 0 <= c2 < 6:
                    m = 0
                    for k in range(5):
                        rr = r + k * dr
                        cc = c + k * dc
                        m |= 1 << (rr * 6 + cc)
                    masks.append(m)
    return tuple(dict.fromkeys(masks))


_WIN_MASKS = _make_win_masks()


def _make_rotation_tables():
    qpos = []
    qmask = []

    for q in range(4):
        r0 = 0 if q < 2 else 3
        c0 = 0 if (q % 2) == 0 else 3
        ps = []
        m = 0
        for i in range(3):
            for j in range(3):
                p = (r0 + i) * 6 + (c0 + j)
                ps.append(p)
                m |= 1 << p
        qpos.append(tuple(ps))
        qmask.append(m)

    rot_pos = []
    inv_rot_pos = []
    rot_pairs = []
    rot_single = []
    out_masks = []
    move_strs = []

    # rot index = quad * 2 + direction, where direction 0=L, 1=R
    for q in range(4):
        r0 = 0 if q < 2 else 3
        c0 = 0 if (q % 2) == 0 else 3

        for d in range(2):
            dest = list(range(36))
            for i in range(3):
                for j in range(3):
                    old = (r0 + i) * 6 + (c0 + j)
                    if d == 0:      # L / anticlockwise
                        ni, nj = 2 - j, i
                    else:           # R / clockwise
                        ni, nj = j, 2 - i
                    new = (r0 + ni) * 6 + (c0 + nj)
                    dest[old] = new

            inv = [0] * 36
            for old, new in enumerate(dest):
                inv[new] = old

            rot_pos.append(tuple(dest))
            inv_rot_pos.append(tuple(inv))
            rot_pairs.append(tuple((1 << old, 1 << dest[old]) for old in qpos[q]))
            rot_single.append(tuple(1 << dest[p] for p in range(36)))
            out_masks.append(FULL_BOARD ^ qmask[q])

            dir_char = "L" if d == 0 else "R"
            move_strs.append(tuple(
                f"{p // 6 + 1},{p % 6 + 1},{q},{dir_char}" for p in range(36)
            ))

    return tuple(rot_pos), tuple(inv_rot_pos), tuple(rot_pairs), tuple(rot_single), tuple(out_masks), tuple(move_strs)


_ROT_POS, _INV_ROT_POS, _ROT_PAIRS, _ROT_SINGLE, _OUT_MASKS, _MOVE_STRS = _make_rotation_tables()


def _make_cell_weights():
    # Start from number of winning windows touching each cell.
    w = [0] * 36
    for m in _WIN_MASKS:
        b = m
        while b:
            lsb = b & -b
            p = lsb.bit_length() - 1
            w[p] += 2
            b ^= lsb

    # Quadrant centers are rotation-invariant and strategically stable.
    for p in (7, 10, 25, 28):
        w[p] += 10

    # Global central four are involved in many crossing lines.
    for p in (14, 15, 20, 21):
        w[p] += 5

    # Corners are a little less flexible.
    for p in (0, 5, 30, 35):
        w[p] -= 1

    return tuple(w)


_CELL_WEIGHT = _make_cell_weights()

_MY_LINE_SCORE = (0, 2, 18, 140, 2600, 0)
_OP_LINE_SCORE = (0, 3, 22, 170, 3200, 0)

# Per-call caches / search state.
_TT = {}
_EVAL_CACHE = {}
_WIN_CACHE = {}
_DEADLINE = 0.0
_NODE_COUNT = 0


class _SearchTimeout(Exception):
    pass


# ---------------------------------------------------------------------------
# Basic board operations
# ---------------------------------------------------------------------------

def _tick():
    global _NODE_COUNT
    _NODE_COUNT += 1
    if (_NODE_COUNT & 4095) == 0 and time.perf_counter() > _DEADLINE:
        raise _SearchTimeout()


def _arrays_to_bits(you, opponent):
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


def _array_fallback(you, opponent):
    for r in range(6):
        for c in range(6):
            try:
                if not you[r][c] and not opponent[r][c]:
                    return f"{r + 1},{c + 1},0,L"
            except Exception:
                pass
    return "1,1,0,L"


def _first_legal_string(side, other):
    empty = FULL_BOARD ^ (side | other)
    if empty:
        p = (empty & -empty).bit_length() - 1
        return _MOVE_STRS[0][p]
    return "1,1,0,L"


def _rot_bits(bits, rot):
    res = bits & _OUT_MASKS[rot]
    for old_bit, new_bit in _ROT_PAIRS[rot]:
        if bits & old_bit:
            res |= new_bit
    return res


def _is_win(bits):
    for m in _WIN_MASKS:
        if (bits & m) == m:
            return True
    return False


def _terminal_from_wins(mover_win, other_win, full, ply):
    if mover_win:
        if other_win:
            return 0
        return WIN_SCORE - ply
    if other_win:
        return -WIN_SCORE + ply
    if full:
        return 0
    return None


def _piece_weight(bits):
    s = 0
    while bits:
        lsb = bits & -bits
        s += _CELL_WEIGHT[lsb.bit_length() - 1]
        bits ^= lsb
    return s


# ---------------------------------------------------------------------------
# Tactical win detection
# ---------------------------------------------------------------------------

def _has_winning_move(side, other):
    """True iff side-to-move has a legal move that wins immediately, not draw."""
    key = (side, other)
    v = _WIN_CACHE.get(key)
    if v is not None:
        return v

    empty = FULL_BOARD ^ (side | other)
    if not empty:
        _WIN_CACHE[key] = False
        return False

    for rot in range(8):
        sb = _rot_bits(side, rot)
        ob = _rot_bits(other, rot)

        # If the rotation already gives the opponent a line, any side line is
        # at best a draw, not a winning move.
        if _is_win(ob):
            continue

        # Rotation alone can make side win; placement elsewhere keeps it.
        if _is_win(sb):
            _WIN_CACHE[key] = True
            return True

        empty_after = FULL_BOARD ^ (sb | ob)

        for m in _WIN_MASKS:
            missing = m & ~sb
            if missing and (missing & (missing - 1)) == 0 and (missing & empty_after):
                _WIN_CACHE[key] = True
                return True

    _WIN_CACHE[key] = False
    return False


def _find_winning_move(side, other):
    """Return an immediate winning move string for side, or None."""
    empty = FULL_BOARD ^ (side | other)
    if not empty:
        return None

    first_empty_p = (empty & -empty).bit_length() - 1

    for rot in range(8):
        sb = _rot_bits(side, rot)
        ob = _rot_bits(other, rot)

        if _is_win(ob):
            continue

        if _is_win(sb):
            return _MOVE_STRS[rot][first_empty_p]

        empty_after = FULL_BOARD ^ (sb | ob)
        targets = 0

        for m in _WIN_MASKS:
            missing = m & ~sb
            if missing and (missing & (missing - 1)) == 0:
                targets |= missing

        targets &= empty_after
        if targets:
            t = (targets & -targets).bit_length() - 1
            p = _INV_ROT_POS[rot][t]
            return _MOVE_STRS[rot][p]

    return None


def _count_winning_moves_limited(side, other, limit=5):
    """Count immediate winning placement/rotation choices up to limit."""
    empty = FULL_BOARD ^ (side | other)
    if not empty:
        return 0

    cnt = 0
    empty_count = empty.bit_count()

    for rot in range(8):
        sb = _rot_bits(side, rot)
        ob = _rot_bits(other, rot)

        if _is_win(ob):
            continue

        if _is_win(sb):
            cnt += empty_count
            if cnt >= limit:
                return cnt
            continue

        empty_after = FULL_BOARD ^ (sb | ob)
        targets = 0

        for m in _WIN_MASKS:
            missing = m & ~sb
            if missing and (missing & (missing - 1)) == 0:
                targets |= missing

        cnt += (targets & empty_after).bit_count()
        if cnt >= limit:
            return cnt

    return cnt


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------

def _static_eval(side, other):
    """Heuristic from the perspective of side-to-move."""
    key = (side, other)
    v = _EVAL_CACHE.get(key)
    if v is not None:
        return v

    sw = _is_win(side)
    ow = _is_win(other)
    if sw:
        v = 0 if ow else WIN_SCORE // 2
        _EVAL_CACHE[key] = v
        return v
    if ow:
        v = -WIN_SCORE // 2
        _EVAL_CACHE[key] = v
        return v

    score = 0
    my2 = my3 = my4 = 0
    op2 = op3 = op4 = 0

    for m in _WIN_MASKS:
        a = (side & m).bit_count()
        b = (other & m).bit_count()

        if b == 0:
            score += _MY_LINE_SCORE[a]
            if a == 2:
                my2 += 1
            elif a == 3:
                my3 += 1
            elif a == 4:
                my4 += 1
        elif a == 0:
            score -= _OP_LINE_SCORE[b]
            if b == 2:
                op2 += 1
            elif b == 3:
                op3 += 1
            elif b == 4:
                op4 += 1

    # Overlapping threats matter more than isolated lines.
    score += 220 * my3 * (my3 - 1)
    score -= 260 * op3 * (op3 - 1)
    score += 2200 * my4 * my4
    score -= 2600 * op4 * op4
    score += 20 * my2 * my3
    score -= 22 * op2 * op3

    # Positional stability / centrality.
    score += 3 * (_piece_weight(side) - _piece_weight(other))

    _EVAL_CACHE[key] = score
    return score


# ---------------------------------------------------------------------------
# Move generation and search
# ---------------------------------------------------------------------------

def _generate_root_moves(side, other):
    empty = FULL_BOARD ^ (side | other)
    moves = []
    seen = set()

    for rot in range(8):
        sb = _rot_bits(side, rot)
        ob = _rot_bits(other, rot)
        other_win = _is_win(ob)
        single = _ROT_SINGLE[rot]

        e = empty
        while e:
            lsb = e & -e
            p = lsb.bit_length() - 1
            e ^= lsb

            cs = sb | single[p]
            key = (cs, ob)
            if key in seen:
                continue
            seen.add(key)

            side_win = _is_win(cs)
            term = _terminal_from_wins(side_win, other_win, (cs | ob) == FULL_BOARD, 1)

            unsafe = False
            threats = 0
            if term is None:
                # Opponent to move after this child.
                unsafe = _has_winning_move(ob, cs)
                threats = _count_winning_moves_limited(cs, ob, 5)
                order = -_static_eval(ob, cs)
                order += 70_000 * threats + 20_000 * threats * threats
                if unsafe:
                    order -= WIN_SCORE // 2
            else:
                order = term

            moves.append([_MOVE_STRS[rot][p], cs, ob, term, order, unsafe, threats, order])

    moves.sort(key=lambda x: x[4], reverse=True)
    return moves


def _one_ply_best(side, other, alpha, beta, ply):
    empty = FULL_BOARD ^ (side | other)
    if not empty:
        return 0

    best = -INF
    seen = set()

    for rot in range(8):
        sb = _rot_bits(side, rot)
        ob = _rot_bits(other, rot)
        other_win = _is_win(ob)
        single = _ROT_SINGLE[rot]

        e = empty
        while e:
            _tick()
            lsb = e & -e
            p = lsb.bit_length() - 1
            e ^= lsb

            cs = sb | single[p]
            key = (cs, ob)
            if key in seen:
                continue
            seen.add(key)

            side_win = _is_win(cs)
            term = _terminal_from_wins(side_win, other_win, (cs | ob) == FULL_BOARD, ply + 1)

            if term is None:
                # After side moves, other is to move; negate other's evaluation.
                score = -_static_eval(ob, cs)
            else:
                score = term

            if score > best:
                best = score
            if score > alpha:
                alpha = score
                if alpha >= beta:
                    return best

    return best if best != -INF else 0


def _ordered_children(side, other, ply):
    empty = FULL_BOARD ^ (side | other)
    children = []
    seen = set()

    for rot in range(8):
        sb = _rot_bits(side, rot)
        ob = _rot_bits(other, rot)
        other_win = _is_win(ob)
        single = _ROT_SINGLE[rot]

        e = empty
        while e:
            _tick()
            lsb = e & -e
            p = lsb.bit_length() - 1
            e ^= lsb

            cs = sb | single[p]
            key = (cs, ob)
            if key in seen:
                continue
            seen.add(key)

            side_win = _is_win(cs)
            term = _terminal_from_wins(side_win, other_win, (cs | ob) == FULL_BOARD, ply + 1)

            if term is None:
                order = -_static_eval(ob, cs)
            else:
                order = term

            children.append((order, cs, ob, term))

    children.sort(key=lambda x: x[0], reverse=True)
    return children


def _negamax(side, other, depth, alpha, beta, ply):
    _tick()

    if depth <= 0:
        return _static_eval(side, other)

    if (side | other) == FULL_BOARD:
        return 0

    key = (side, other)
    alpha_orig = alpha
    beta_orig = beta

    entry = _TT.get(key)
    if entry is not None and entry[0] >= depth:
        _, val, flag = entry
        if flag == 0:       # exact
            return val
        if flag > 0:        # lower bound
            alpha = max(alpha, val)
        else:               # upper bound
            beta = min(beta, val)
        if alpha >= beta:
            return val

    if _has_winning_move(side, other):
        best = WIN_SCORE - (ply + 1)
    elif depth == 1:
        best = _one_ply_best(side, other, alpha, beta, ply)
    else:
        best = -INF
        children = _ordered_children(side, other, ply)

        if not children:
            best = 0
        else:
            for _, cs, ob, term in children:
                if term is None:
                    score = -_negamax(ob, cs, depth - 1, -beta, -alpha, ply + 1)
                else:
                    score = term

                if score > best:
                    best = score
                if score > alpha:
                    alpha = score
                    if alpha >= beta:
                        break

    if best <= alpha_orig:
        flag = -1       # upper bound
    elif best >= beta_orig:
        flag = 1        # lower bound
    else:
        flag = 0        # exact

    old = _TT.get(key)
    if old is None or depth >= old[0]:
        _TT[key] = (depth, best, flag)

    return best


def _root_search(root_moves, depth):
    root_moves.sort(key=lambda x: x[7], reverse=True)

    alpha = -INF
    beta = INF
    best_score = -INF
    best_move = root_moves[0][0]

    for m in root_moves:
        _tick()
        term = m[3]

        if term is not None:
            score = term
        elif depth <= 1:
            score = -_static_eval(m[2], m[1])
        else:
            score = -_negamax(m[2], m[1], depth - 1, -beta, -alpha, 1)

        m[7] = score

        if score > best_score:
            best_score = score
            best_move = m[0]

        if score > alpha:
            alpha = score

    return best_move, best_score


def _unavoidable_win_after_move(us, them):
    """
    Given a nonterminal state after our move, with opponent to move, return True
    if every opponent reply still lets us win immediately next turn, or loses
    immediately by rotating us into a win.
    """
    if _has_winning_move(them, us):
        return False

    empty = FULL_BOARD ^ (us | them)
    if not empty:
        return False

    seen = set()

    for rot in range(8):
        tb = _rot_bits(them, rot)
        ub = _rot_bits(us, rot)
        us_win = _is_win(ub)
        single = _ROT_SINGLE[rot]

        e = empty
        while e:
            _tick()
            lsb = e & -e
            p = lsb.bit_length() - 1
            e ^= lsb

            tc = tb | single[p]
            key = (tc, ub)
            if key in seen:
                continue
            seen.add(key)

            them_win = _is_win(tc)

            # Opponent can win or draw, so our win is not forced.
            if them_win:
                return False

            # Opponent accidentally rotates us into a sole win.
            if us_win:
                continue

            # Opponent can fill the board into a draw.
            if (tc | ub) == FULL_BOARD:
                return False

            # Otherwise we must have an immediate winning reply.
            if not _has_winning_move(ub, tc):
                return False

    return True


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def policy(you, opponent) -> str:
    global _DEADLINE, _NODE_COUNT

    fallback = "1,1,0,L"
    best_move = fallback

    try:
        side, other = _arrays_to_bits(you, opponent)
        fallback = _first_legal_string(side, other)
        best_move = fallback

        # Good standard opening: quadrant center, rotation-invariant.
        if (side | other) == 0:
            return "2,2,0,L"

        _TT.clear()
        _EVAL_CACHE.clear()
        _WIN_CACHE.clear()
        _NODE_COUNT = 0
        _DEADLINE = time.perf_counter() + 0.90

        # Exact immediate win.
        win_move = _find_winning_move(side, other)
        if win_move is not None:
            return win_move

        root = _generate_root_moves(side, other)
        if not root:
            return fallback

        # Initial safe heuristic fallback before any deeper search.
        best_move = root[0][0]
        for m in root:
            if m[3] == 0 or (m[3] is None and not m[5]):
                best_move = m[0]
                break

        # Main tactical search: exact opponent immediate replies + heuristic leaf.
        best_move, best_score = _root_search(root, 2)

        if best_score >= WIN_SCORE - 10:
            return best_move

        # Check promising moves for an unavoidable next-turn win.
        if time.perf_counter() < _DEADLINE - 0.08:
            root.sort(key=lambda x: (x[7], x[6], x[4]), reverse=True)
            checked = 0
            for m in root:
                if time.perf_counter() > _DEADLINE - 0.05:
                    break
                if m[3] is None and not m[5] and (m[6] >= 2 or checked < 3):
                    checked += 1
                    if _unavoidable_win_after_move(m[1], m[2]):
                        return m[0]
                    if checked >= 12:
                        break

        # Deeper full searches in smaller endgames.
        empties = (FULL_BOARD ^ (side | other)).bit_count()
        extra_depths = []
        if empties <= 16:
            extra_depths.append(3)
        if empties <= 10:
            extra_depths.append(4)
        if empties <= 6:
            extra_depths.append(5)

        for d in extra_depths:
            if time.perf_counter() > _DEADLINE - 0.05:
                break
            bm, bs = _root_search(root, d)
            best_move, best_score = bm, bs
            if best_score >= WIN_SCORE - 20:
                break

        return best_move

    except _SearchTimeout:
        return best_move or fallback
    except Exception:
        return _array_fallback(you, opponent)
