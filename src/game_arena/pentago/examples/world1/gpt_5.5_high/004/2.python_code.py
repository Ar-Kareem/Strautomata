
import time

WIN_SCORE = 10_000_000
INF = 1_000_000_000
FULL_MASK = (1 << 36) - 1

_DIRS = ("L", "R")
_BASES = (0, 3, 18, 21)

_INIT = False
_LINES = ()
_ROT_TABLE = None
_QUAD_MASK = ()
_QUAD_NOT_MASK = ()
_POS = ()

_WIN_CACHE = {}
_EVAL_CACHE = {}
_TT = {}
_DEADLINE = 0.0


class _TimeUp(Exception):
    pass


def _init():
    global _INIT, _LINES, _ROT_TABLE, _QUAD_MASK, _QUAD_NOT_MASK, _POS

    if _INIT:
        return

    def bit(r, c):
        return 1 << (r * 6 + c)

    lines = []

    # Horizontal length-5 segments.
    for r in range(6):
        for c in range(2):
            m = 0
            for k in range(5):
                m |= bit(r, c + k)
            lines.append(m)

    # Vertical length-5 segments.
    for c in range(6):
        for r in range(2):
            m = 0
            for k in range(5):
                m |= bit(r + k, c)
            lines.append(m)

    # Down-right diagonals.
    for r in range(2):
        for c in range(2):
            m = 0
            for k in range(5):
                m |= bit(r + k, c + k)
            lines.append(m)

    # Down-left diagonals.
    for r in range(2):
        for c in range(4, 6):
            m = 0
            for k in range(5):
                m |= bit(r + k, c - k)
            lines.append(m)

    _LINES = tuple(lines)

    quad_masks = []
    quad_not_masks = []
    rot_table = []

    for q, base in enumerate(_BASES):
        qm = 0
        for rr in range(3):
            qm |= 0b111 << (base + 6 * rr)
        quad_masks.append(qm)
        quad_not_masks.append(FULL_MASK ^ qm)

        qtables = []
        for d in range(2):  # 0 = L, 1 = R
            arr = [0] * 512
            for occ in range(512):
                out = 0
                for i in range(9):
                    if occ & (1 << i):
                        r = i // 3
                        c = i % 3
                        if d == 0:      # anticlockwise
                            nr, nc = 2 - c, r
                        else:           # clockwise
                            nr, nc = c, 2 - r
                        out |= 1 << (base + nr * 6 + nc)
                arr[occ] = out
            qtables.append(arr)
        rot_table.append(qtables)

    _QUAD_MASK = tuple(quad_masks)
    _QUAD_NOT_MASK = tuple(quad_not_masks)
    _ROT_TABLE = rot_table

    # Positional weights: cells occurring in many 5-lines, central cells,
    # and quadrant centers get small bonuses.
    line_count = [0] * 36
    for m in _LINES:
        x = m
        while x:
            lsb = x & -x
            p = lsb.bit_length() - 1
            line_count[p] += 1
            x ^= lsb

    pos = []
    for p in range(36):
        r, c = divmod(p, 6)
        dist2 = abs(2 * r - 5) + abs(2 * c - 5)
        central_bonus = max(0, 20 - 2 * dist2)
        val = line_count[p] * 5 + central_bonus
        if r % 3 == 1 and c % 3 == 1:
            val += 8
        pos.append(val)
    _POS = tuple(pos)

    _INIT = True


def _to_bits(board):
    bb = 0
    for r in range(6):
        row = board[r]
        for c in range(6):
            if row[c]:
                bb |= 1 << (r * 6 + c)
    return bb


def _rotate(bb, q, d):
    base = _BASES[q]
    occ = ((bb >> base) & 7) | (((bb >> (base + 6)) & 7) << 3) | (((bb >> (base + 12)) & 7) << 6)
    return (bb & _QUAD_NOT_MASK[q]) | _ROT_TABLE[q][d][occ]


def _has_win(bb):
    cached = _WIN_CACHE.get(bb)
    if cached is not None:
        return cached

    for m in _LINES:
        if (bb & m) == m:
            _WIN_CACHE[bb] = True
            return True

    _WIN_CACHE[bb] = False
    return False


def _terminal_score(us_after, them_after):
    uw = _has_win(us_after)
    tw = _has_win(them_after)

    if uw:
        return 0 if tw else WIN_SCORE
    if tw:
        return -WIN_SCORE
    if (us_after | them_after) == FULL_MASK:
        return 0
    return None


def _evaluate(us, them):
    key = (us, them)
    cached = _EVAL_CACHE.get(key)
    if cached is not None:
        return cached

    uw = _has_win(us)
    tw = _has_win(them)
    if uw:
        val = 0 if tw else WIN_SCORE
        _EVAL_CACHE[key] = val
        return val
    if tw:
        _EVAL_CACHE[key] = -WIN_SCORE
        return -WIN_SCORE

    # Open-line weights. Four-in-a-row is intentionally very valuable.
    weights = (0, 1, 10, 90, 4000, 100000)

    score = 0
    for m in _LINES:
        uc = (us & m).bit_count()
        tc = (them & m).bit_count()

        if tc == 0:
            score += weights[uc]
        if uc == 0:
            score -= weights[tc]

    x = us
    while x:
        lsb = x & -x
        p = lsb.bit_length() - 1
        score += _POS[p]
        x ^= lsb

    x = them
    while x:
        lsb = x & -x
        p = lsb.bit_length() - 1
        score -= _POS[p]
        x ^= lsb

    _EVAL_CACHE[key] = score
    return score


def _children(us, them, want_move=False, unique=True):
    empty = FULL_MASK & ~(us | them)
    seen = set() if unique else None

    while empty:
        lsb = empty & -empty
        p = lsb.bit_length() - 1
        empty ^= lsb

        placed = us | lsb

        for q in range(4):
            for d in range(2):
                ru = _rotate(placed, q, d)
                rt = _rotate(them, q, d)

                if unique:
                    k = ru | (rt << 36)
                    if k in seen:
                        continue
                    seen.add(k)

                if want_move:
                    yield p, q, d, ru, rt
                else:
                    yield ru, rt


def _negamax(us, them, depth, alpha, beta, beam):
    if time.perf_counter() > _DEADLINE:
        raise _TimeUp()

    if depth <= 0:
        return _evaluate(us, them)

    key_beam = 0 if depth <= 1 else beam
    key = (us, them, depth, key_beam)
    cached = _TT.get(key)
    if cached is not None:
        return cached

    best = -INF
    nonterminal = []
    checked = 0

    for ru, rt in _children(us, them, want_move=False, unique=True):
        checked += 1
        if (checked & 63) == 0 and time.perf_counter() > _DEADLINE:
            raise _TimeUp()

        term = _terminal_score(ru, rt)

        if term is not None:
            val = term
            if val > best:
                best = val

            # A clean immediate win is the maximum possible result.
            if val >= WIN_SCORE:
                _TT[key] = val
                return val

            if val > alpha:
                alpha = val
            if alpha >= beta:
                return best

        elif depth == 1:
            val = -_evaluate(rt, ru)
            if val > best:
                best = val
            if val > alpha:
                alpha = val
            if alpha >= beta:
                return best

        else:
            prelim = -_evaluate(rt, ru)
            nonterminal.append((prelim, ru, rt))

    if depth > 1 and nonterminal:
        nonterminal.sort(key=lambda x: x[0], reverse=True)
        if beam and len(nonterminal) > beam:
            nonterminal = nonterminal[:beam]

        for _, ru, rt in nonterminal:
            if time.perf_counter() > _DEADLINE:
                raise _TimeUp()

            val = -_negamax(rt, ru, depth - 1, -beta, -alpha, beam)

            if val > best:
                best = val
            if val > alpha:
                alpha = val
            if alpha >= beta:
                return best

    if best == -INF:
        best = 0

    _TT[key] = best
    return best


def _format_move(p, q, d):
    return f"{p // 6 + 1},{p % 6 + 1},{q},{_DIRS[d]}"


def _first_legal(us, them):
    empty = FULL_MASK & ~(us | them)
    if empty:
        lsb = empty & -empty
        p = lsb.bit_length() - 1
        return _format_move(p, 0, 0)
    return "1,1,0,L"


def policy(you, opponent) -> str:
    global _DEADLINE, _TT, _EVAL_CACHE

    _init()

    us = _to_bits(you)
    them = _to_bits(opponent)
    fallback = _first_legal(us, them)

    if len(_WIN_CACHE) > 250000:
        _WIN_CACHE.clear()

    _EVAL_CACHE = {}
    _TT = {}
    _DEADLINE = time.perf_counter() + 0.86

    root = []

    try:
        # Generate root moves. Return a clean immediate win instantly.
        for p, q, d, ru, rt in _children(us, them, want_move=True, unique=True):
            mv = _format_move(p, q, d)
            term = _terminal_score(ru, rt)

            if term == WIN_SCORE:
                return mv

            prelim = term if term is not None else _evaluate(ru, rt)
            root.append([mv, ru, rt, term, prelim, prelim])

        if not root:
            return fallback

        root.sort(key=lambda e: (e[5], e[4]), reverse=True)

        # Full one-reply search: this is the important safety pass that
        # avoids allowing an immediate opponent win whenever possible.
        for e in root:
            if time.perf_counter() > _DEADLINE:
                raise _TimeUp()

            if e[3] is None:
                e[5] = -_negamax(e[2], e[1], 1, -INF, INF, 0)
            else:
                e[5] = e[3]

        root.sort(key=lambda e: (e[5], e[4]), reverse=True)

        if root[0][5] >= WIN_SCORE // 2:
            return root[0][0]

        # Selective deeper search while time remains.
        for depth, beam, max_candidates in ((2, 42, 36), (3, 18, 10)):
            ordered = sorted(root, key=lambda e: (e[5], e[4]), reverse=True)

            for e in ordered[:max_candidates]:
                if time.perf_counter() > _DEADLINE:
                    raise _TimeUp()

                if e[3] is None:
                    e[5] = -_negamax(e[2], e[1], depth, -INF, INF, beam)
                else:
                    e[5] = e[3]

            root.sort(key=lambda e: (e[5], e[4]), reverse=True)

            if root[0][5] >= WIN_SCORE // 2:
                break

        return root[0][0]

    except _TimeUp:
        if root:
            root.sort(key=lambda e: (e[5], e[4]), reverse=True)
            return root[0][0]
        return fallback

    except Exception:
        return fallback
