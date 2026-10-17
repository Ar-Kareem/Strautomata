
import time

# ----------------------------------------------------------------------
# Bitboard-based alpha-beta policy for 4x4 Tic-Tac-Toe (4-in-a-row wins).
# Bit i of a bitboard corresponds to cell (i // 4, i % 4).
# ----------------------------------------------------------------------

_FULL = (1 << 16) - 1          # all 16 cells occupied
_NLINES = 10                   # 4 rows + 4 cols + 2 diagonals

# All ten winning lines as 16-bit masks.
_LINES = []
for _r in range(4):
    _m = 0
    for _c in range(4):
        _m |= 1 << (_r * 4 + _c)
    _LINES.append(_m)
for _c in range(4):
    _m = 0
    for _r in range(4):
        _m |= 1 << (_r * 4 + _c)
    _LINES.append(_m)
_m = 0
for _i in range(4):
    _m |= 1 << (_i * 4 + _i)
_LINES.append(_m)
_m = 0
for _i in range(4):
    _m |= 1 << (_i * 4 + 3 - _i)
_LINES.append(_m)

# Lines passing through each cell.
_CELL_LINES = [[] for _ in range(16)]
for _li in range(_NLINES):
    _bits = _LINES[_li]
    while _bits:
        _b = _bits & -_bits
        _CELL_LINES[_b.bit_length() - 1].append(_li)
        _bits ^= _b
_CELL_LINEMASKS = [tuple(_LINES[li] for li in lst) for lst in _CELL_LINES]

_POSW = tuple(len(_CELL_LINES[i]) for i in range(16))  # cells on more lines are stronger

_LINEVAL = (0, 3, 40, 500, 0)   # eval value of an uncontested line with k stones
_ATT = (0, 10, 100, 10000)      # ordering bonus: extends our uncontested line
_DEF = (0, 5, 80, 9000)         # ordering bonus: contests an opponent line
_KILLER_BONUS = 5000
_TT_BONUS = 1 << 20
_HIST_CAP = 3000

_WIN = 1 << 24
_INF = 1 << 30
_MAXPLY = 32

_TT = {}                                    # (my,opp) -> (depth, value, flag, best_move)
_KILLERS = [[-1, -1] for _ in range(_MAXPLY)]
_HISTORY = [0] * 16
_nodes = 0
_deadline = 0.0


class _Abort(Exception):
    """Raised when the time budget is exhausted."""
    pass


def _evaluate(my, opp):
    """Static evaluation from the perspective of the side to move."""
    s = 0
    lv = _LINEVAL
    pw = _POSW
    for mask in _LINES:
        m = (my & mask).bit_count()
        if m:
            if not (mask & opp):
                s += lv[m]
        else:
            o = (opp & mask).bit_count()
            if o:
                s -= lv[o]
    b = my
    while b:
        lb = b & -b
        s += pw[lb.bit_length() - 1]
        b ^= lb
    b = opp
    while b:
        lb = b & -b
        s -= pw[lb.bit_length() - 1]
        b ^= lb
    return s


def _ordered_moves(my, opp, tt_move, ply):
    """Generate empty cells ordered by tactical promise (best first)."""
    # Per-line ordering weights depend only on the current position.
    lw = [0] * _NLINES
    for i in range(_NLINES):
        mask = _LINES[i]
        m = (my & mask).bit_count()
        o = (opp & mask).bit_count()
        if m:
            if o == 0:
                lw[i] = _ATT[m]
        elif o:
            lw[i] = _DEF[o]
    k0, k1 = _KILLERS[ply]
    hist = _HISTORY
    pw = _POSW
    scored = []
    ap = scored.append
    e = _FULL ^ (my | opp)
    while e:
        b = e & -e
        cell = b.bit_length() - 1
        e ^= b
        if cell == tt_move:
            ap((_TT_BONUS, cell))
        else:
            sc = pw[cell] + hist[cell]
            for li in _CELL_LINES[cell]:
                sc += lw[li]
            if cell == k0 or cell == k1:
                sc += _KILLER_BONUS
            ap((sc, cell))
    scored.sort(reverse=True)
    return scored


def _search(my, opp, depth, alpha, beta, ply):
    """Negamax with alpha-beta, transposition table and tactical quiescence."""
    global _nodes

    if depth <= 0:
        # Quiescence: resolve immediate winning threats before evaluating.
        for mask in _LINES:
            if (mask & my).bit_count() == 3 and not (mask & opp):
                return _WIN - ply                 # we win on the spot
        t = 0
        for mask in _LINES:
            if (mask & opp).bit_count() == 3 and not (mask & my):
                t |= mask & ~opp                  # empty cell(s) that lose now
        if t == 0:
            return _evaluate(my, opp)             # quiet position
        if t & (t - 1):
            return ply - _WIN                     # two threats: lost
        depth = 1                                 # one threat: forced answer

    _nodes += 1
    if (_nodes & 1023) == 0 and time.perf_counter() >= _deadline:
        raise _Abort()

    occ = my | opp
    if occ == _FULL:
        return 0                                  # board full: draw

    key = (my << 16) | opp
    alpha0 = alpha
    tt_move = -1
    ent = _TT.get(key)
    if ent is not None:
        d, v, f, bm = ent
        if d >= depth:
            if f == 0:                            # exact
                return v
            if f == 1:                            # lower bound
                if v > alpha:
                    alpha = v
            elif v < beta:                        # upper bound
                beta = v
            if alpha >= beta:
                return v
        tt_move = bm

    best_val = -_INF
    best_move = -1
    for _, cell in _ordered_moves(my, opp, tt_move, ply):
        nmy = my | (1 << cell)
        won = False
        for lm in _CELL_LINEMASKS[cell]:
            if lm & nmy == lm:
                won = True
                break
        if won:
            val = _WIN - ply
        else:
            val = -_search(opp, nmy, depth - 1, -beta, -alpha, ply + 1)
        if val > best_val:
            best_val = val
            best_move = cell
            if val > alpha:
                alpha = val
                if alpha >= beta:
                    kl = _KILLERS[ply]
                    if kl[0] != cell:
                        kl[1] = kl[0]
                        kl[0] = cell
                    h = _HISTORY[cell] + depth * depth
                    _HISTORY[cell] = h if h < _HIST_CAP else _HIST_CAP
                    break

    if best_val <= alpha0:
        f = 2                                     # upper bound
    elif best_val >= beta:
        f = 1                                     # lower bound
    else:
        f = 0                                     # exact
    _TT[key] = (depth, best_val, f, best_move)
    return best_val


def _root(my, opp, depth):
    """One iterative-deepening iteration at the root. Returns (value, move)."""
    key = (my << 16) | opp
    tt_move = -1
    ent = _TT.get(key)
    if ent is not None:
        tt_move = ent[3]
    best_val = -_INF
    best_move = None
    alpha = -_INF
    for _, cell in _ordered_moves(my, opp, tt_move, 0):
        nmy = my | (1 << cell)
        won = False
        for lm in _CELL_LINEMASKS[cell]:
            if lm & nmy == lm:
                won = True
                break
        if won:
            val = _WIN
        else:
            val = -_search(opp, nmy, depth - 1, -_INF, -alpha, 1)
        if val > best_val:
            best_val = val
            best_move = cell
            if val > alpha:
                alpha = val
    if best_move is not None:
        _TT[key] = (depth, best_val, 0, best_move)
    return best_val, best_move


def policy(board):
    """Return a legal (row, col) move for the side marked 1."""
    global _nodes, _deadline, _TT, _HISTORY

    # --- Parse the board robustly -------------------------------------
    my = 0
    opp = 0
    empties = []
    try:
        for r in range(4):
            row = board[r]
            base = r * 4
            for c in range(4):
                v = row[c]
                if v == 1:
                    my |= 1 << (base + c)
                elif v == -1:
                    opp |= 1 << (base + c)
                else:
                    empties.append(base + c)
    except Exception:
        return (0, 0)

    if not empties:
        return (0, 0)  # no legal move exists; the arena should never ask this

    try:
        if len(empties) == 1:
            cell = empties[0]
            return (cell >> 2, cell & 3)

        # Immediate winning move: always take it.
        for cell in empties:
            nmy = my | (1 << cell)
            for lm in _CELL_LINEMASKS[cell]:
                if lm & nmy == lm:
                    return (cell >> 2, cell & 3)

        # Opening move: claim a strong central square.
        if not (my | opp):
            return (1, 1)

        # --- Iterative-deepening alpha-beta ---------------------------
        if len(_TT) > 400000:
            _TT = {}
        _HISTORY = [h >> 1 for h in _HISTORY]     # age history entries
        _nodes = 0
        _deadline = time.perf_counter() + 0.9

        best_cell = empties[0]
        max_depth = len(empties)
        try:
            for depth in range(1, max_depth + 1):
                val, mv = _root(my, opp, depth)
                if mv is not None:
                    best_cell = mv
                if val >= _WIN - 64 or val <= 64 - _WIN:
                    break                          # forced result found
        except _Abort:
            pass

        if ((my | opp) >> best_cell) & 1:          # final legality guard
            best_cell = empties[0]
        return (best_cell >> 2, best_cell & 3)
    except Exception:
        cell = empties[0]
        return (cell >> 2, cell & 3)
