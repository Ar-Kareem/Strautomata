
from time import perf_counter

# ---------- Constants and winning lines ----------

_ALL_MASK = (1 << 27) - 1
_CENTER_IDX = 13
_CENTER_BIT = 1 << _CENTER_IDX
_INF = 10**9
_WIN = 10**7

_COORDS = []
for _i in range(3):
    for _j in range(3):
        for _k in range(3):
            _COORDS.append((_i, _j, _k))


def _idx(i, j, k):
    return i * 9 + j * 3 + k


def _inside(i, j, k):
    return 0 <= i < 3 and 0 <= j < 3 and 0 <= k < 3


_DIRECTIONS = []
for _dx in (-1, 0, 1):
    for _dy in (-1, 0, 1):
        for _dz in (-1, 0, 1):
            if _dx == 0 and _dy == 0 and _dz == 0:
                continue
            # Keep one direction from each opposite pair.
            if _dx != 0:
                if _dx < 0:
                    continue
            elif _dy != 0:
                if _dy < 0:
                    continue
            else:
                if _dz < 0:
                    continue
            _DIRECTIONS.append((_dx, _dy, _dz))

_WIN_MASKS = []
_seen_masks = set()

for _i in range(3):
    for _j in range(3):
        for _k in range(3):
            for _dx, _dy, _dz in _DIRECTIONS:
                _pi, _pj, _pk = _i - _dx, _j - _dy, _k - _dz
                if _inside(_pi, _pj, _pk):
                    continue

                _ei, _ej, _ek = _i + 2 * _dx, _j + 2 * _dy, _k + 2 * _dz
                if not _inside(_ei, _ej, _ek):
                    continue

                _mask = 0
                for _t in range(3):
                    _ci = _i + _t * _dx
                    _cj = _j + _t * _dy
                    _ck = _k + _t * _dz
                    _mask |= 1 << _idx(_ci, _cj, _ck)

                if _mask not in _seen_masks:
                    _seen_masks.add(_mask)
                    _WIN_MASKS.append(_mask)

_CELL_WIN_MASKS = [[] for _ in range(27)]
for _m in _WIN_MASKS:
    for _n in range(27):
        if _m & (1 << _n):
            _CELL_WIN_MASKS[_n].append(_m)

_LINE_COUNT = [len(_CELL_WIN_MASKS[_n]) for _n in range(27)]

_POS = []
for _n, (_i, _j, _k) in enumerate(_COORDS):
    _dist = abs(_i - 1) + abs(_j - 1) + abs(_k - 1)
    _score = _LINE_COUNT[_n] * 32 - _dist * 5
    if _n == _CENTER_IDX:
        _score += 80
    if _dist == 3:  # corners
        _score += 10
    _POS.append(_score)

_FALLBACK_BITS = [
    1 << n for n in sorted(range(27), key=lambda x: _POS[x], reverse=True)
]


class _Timeout(Exception):
    pass


# ---------- Bitboard utilities ----------

def _has_win(bits):
    for m in _WIN_MASKS:
        if (bits & m) == m:
            return True
    return False


def _winning_bits(pbits, occ):
    """Empty cells where pbits can move and immediately complete a line."""
    res = 0
    for m in _WIN_MASKS:
        if (pbits & m).bit_count() == 2:
            e = m & ~occ
            if e and (e & (e - 1)) == 0:
                res |= e
    return res & _ALL_MASK


def _move_wins(pbits, bit):
    idx = bit.bit_length() - 1
    nb = pbits | bit
    for m in _CELL_WIN_MASKS[idx]:
        if (nb & m) == m:
            return True
    return False


def _select_best(mask):
    if not mask:
        return 0
    best = mask & -mask
    best_score = -_INF
    m = mask
    while m:
        bit = m & -m
        m ^= bit
        idx = bit.bit_length() - 1
        sc = _POS[idx]
        if sc > best_score:
            best_score = sc
            best = bit
    return best


def _pos_sum(bits):
    s = 0
    while bits:
        bit = bits & -bits
        bits ^= bit
        s += _POS[bit.bit_length() - 1]
    return s


def _evaluate(pbits, obits):
    """Heuristic from the perspective of the side represented by pbits."""
    occ = pbits | obits
    score = _pos_sum(pbits) - _pos_sum(obits)

    own_weights = (0, 12, 260, 0)
    opp_weights = (0, 14, 300, 0)

    for m in _WIN_MASKS:
        pc = (pbits & m).bit_count()
        oc = (obits & m).bit_count()
        if oc == 0:
            score += own_weights[pc]
        elif pc == 0:
            score -= opp_weights[oc]

    my_threats = _winning_bits(pbits, occ).bit_count()
    op_threats = _winning_bits(obits, occ).bit_count()

    score += 700 * my_threats
    score -= 850 * op_threats

    if my_threats >= 2:
        score += 7000 + 1000 * my_threats
    if op_threats >= 2:
        score -= 8500 + 1200 * op_threats

    return score


def _ordered_moves(pbits, obits, legal):
    """Threat-aware move ordering for alpha-beta efficiency."""
    occ = pbits | obits
    opp_immediate = _winning_bits(obits, occ)
    scored = []

    lm = legal
    while lm:
        bit = lm & -lm
        lm ^= bit
        idx = bit.bit_length() - 1

        sc = _POS[idx]

        if _move_wins(pbits, bit):
            sc += 1_000_000

        if bit & opp_immediate:
            sc += 700_000

        # Local line value around this cell.
        for line in _CELL_WIN_MASKS[idx]:
            pc = (pbits & line).bit_count()
            oc = (obits & line).bit_count()
            if oc == 0:
                sc += (0, 10, 120, 0)[pc + 1]
            if pc == 0:
                sc += (0, 4, 70, 0)[oc]

        np = pbits | bit
        nocc = occ | bit

        my_th = _winning_bits(np, nocc).bit_count()
        op_th = _winning_bits(obits, nocc).bit_count()

        if my_th >= 2:
            sc += 60000 + 4000 * my_th
        elif my_th == 1:
            sc += 2500

        if op_th >= 2:
            sc -= 8000 + 1000 * op_th
        elif op_th == 1:
            sc -= 1500

        scored.append((sc, bit))

    scored.sort(reverse=True)
    return [bit for _, bit in scored]


def _safe_fork_move(pbits, obits, legal):
    """Return a move creating at least two immediate wins while allowing no opponent immediate win."""
    occ = pbits | obits
    for bit in _ordered_moves(pbits, obits, legal):
        np = pbits | bit
        nocc = occ | bit
        if _winning_bits(obits, nocc):
            continue
        if _winning_bits(np, nocc).bit_count() >= 2:
            return bit
    return 0


def _bits_from_board(board):
    mybits = 0
    oppbits = 0
    for i in range(3):
        for j in range(3):
            for k in range(3):
                v = board[i][j][k]
                bit = 1 << _idx(i, j, k)
                if v == 1:
                    mybits |= bit
                elif v == -1:
                    oppbits |= bit
    return mybits, oppbits


def _fallback_legal(board):
    for i in range(3):
        for j in range(3):
            for k in range(3):
                try:
                    if board[i][j][k] == 0:
                        return (i, j, k)
                except Exception:
                    pass
    return (0, 0, 0)


# ---------- Main policy ----------

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    try:
        return _policy_impl(board)
    except Exception:
        return _fallback_legal(board)


def _policy_impl(board):
    mybits, oppbits = _bits_from_board(board)
    occ = mybits | oppbits
    legal = (~occ) & _ALL_MASK

    if not legal:
        return (0, 0, 0)

    fallback_bit = _select_best(legal)

    # If called after a terminal state, still return a legal move.
    if _has_win(mybits) or _has_win(oppbits):
        return _COORDS[fallback_bit.bit_length() - 1]

    # 1. Win immediately if possible.
    my_wins = _winning_bits(mybits, occ)
    if my_wins:
        bit = _select_best(my_wins)
        return _COORDS[bit.bit_length() - 1]

    # 2. Block opponent's immediate win. If there are multiple, the position is
    # likely lost, but still return a legal blocking move.
    opp_wins = _winning_bits(oppbits, occ)
    if opp_wins:
        bit = _select_best(opp_wins)
        return _COORDS[bit.bit_length() - 1]

    # 3. Opening principle: take the center if this is our first move.
    if mybits == 0 and (legal & _CENTER_BIT):
        return _COORDS[_CENTER_IDX]

    # 4. Take a clean fork if one exists.
    fork = _safe_fork_move(mybits, oppbits, legal)
    if fork:
        return _COORDS[fork.bit_length() - 1]

    # 5. Iterative-deepening negamax search.
    deadline = perf_counter() + 0.86
    tt = {}
    nodes = 0

    def negamax(pbits, obits, depth, alpha, beta):
        nonlocal nodes
        nodes += 1
        if (nodes & 2047) == 0 and perf_counter() > deadline:
            raise _Timeout()

        # Previous move by obits has already won.
        if _has_win(obits):
            return -_WIN - depth

        occ2 = pbits | obits
        if occ2 == _ALL_MASK:
            return 0

        # Tactical quiescence.
        cur_win = _winning_bits(pbits, occ2)
        if cur_win:
            return _WIN + depth

        opp_win = _winning_bits(obits, occ2)
        if opp_win.bit_count() >= 2:
            return -_WIN - depth

        if depth <= 0:
            return _evaluate(pbits, obits)

        alpha0, beta0 = alpha, beta
        key = (pbits, obits, depth)
        entry = tt.get(key)

        if entry is not None:
            flag, val = entry
            if flag == 0:  # exact
                return val
            elif flag == 1:  # lower bound
                if val >= beta:
                    return val
                if val > alpha:
                    alpha = val
            else:  # upper bound
                if val <= alpha:
                    return val
                if val < beta:
                    beta = val
            if alpha >= beta:
                return val

        # If opponent has one immediate win, blocking is forced.
        if opp_win:
            legal2 = opp_win
        else:
            legal2 = (~occ2) & _ALL_MASK

        best = -_INF
        for bit in _ordered_moves(pbits, obits, legal2):
            val = -negamax(obits, pbits | bit, depth - 1, -beta, -alpha)
            if val > best:
                best = val
            if val > alpha:
                alpha = val
            if alpha >= beta:
                break

        if best == -_INF:
            best = _evaluate(pbits, obits)

        if best <= alpha0:
            flag = 2  # upper
        elif best >= beta0:
            flag = 1  # lower
        else:
            flag = 0  # exact

        tt[key] = (flag, best)
        return best

    def root_search(depth, preferred):
        moves = _ordered_moves(mybits, oppbits, legal)
        if preferred:
            moves = [preferred] + [b for b in moves if b != preferred]

        best_bit = moves[0] if moves else fallback_bit
        best_val = -_INF
        alpha = -_INF

        for bit in moves:
            if perf_counter() > deadline:
                raise _Timeout()

            val = -negamax(oppbits, mybits | bit, depth - 1, -_INF, -alpha)

            if val > best_val:
                best_val = val
                best_bit = bit

            if val > alpha:
                alpha = val

        return best_bit, best_val

    ordered = _ordered_moves(mybits, oppbits, legal)
    best_bit = ordered[0] if ordered else fallback_bit

    empty = legal.bit_count()
    if empty <= 9:
        max_depth = empty
    elif empty <= 13:
        max_depth = 11
    elif empty <= 17:
        max_depth = 9
    elif empty <= 22:
        max_depth = 7
    else:
        max_depth = 6

    for depth in range(1, max_depth + 1):
        try:
            bit, val = root_search(depth, best_bit)
            best_bit = bit
            if val > _WIN // 2:
                break
        except _Timeout:
            break

    return _COORDS[best_bit.bit_length() - 1]
