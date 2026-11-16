
from __future__ import annotations
from time import perf_counter as _perf_counter

WIDTH = 7
HEIGHT = 6
STRIDE = HEIGHT + 1
BOARD_CELLS = WIDTH * HEIGHT
KEY_SHIFT = WIDTH * STRIDE

# Center-first ordering.
COL_ORDER = (3, 2, 4, 1, 5, 0, 6)

BOTTOM_MASK = tuple(1 << (c * STRIDE) for c in range(WIDTH))
TOP_MASK = tuple(1 << (c * STRIDE + HEIGHT - 1) for c in range(WIDTH))
COLUMN_MASK = tuple(((1 << HEIGHT) - 1) << (c * STRIDE) for c in range(WIDTH))
BOTTOM_ALL = sum(BOTTOM_MASK)
BOARD_MASK = sum(COLUMN_MASK)

_SHIFT_H = STRIDE
_SHIFT_D1 = HEIGHT
_SHIFT_D2 = HEIGHT + 2

_COL_WEIGHT = (2, 4, 7, 10, 7, 4, 2)
_COL_ORDER_SCORE = (0, 4, 10, 18, 10, 4, 0)

_MY_WINDOW = (0, 2, 18, 120, 100000)
_OPP_WINDOW = (0, 2, 20, 145, 100000)

_LOCAL_MAKE = (0, 4, 24, 150, 10000)
_LOCAL_BLOCK = (0, 0, 12, 90, 0)

_WIN_SCORE = 1_000_000
_INF = 10_000_000

_TIME_LIMIT = 0.88
_TT_LIMIT = 300_000

_EXACT = 0
_LOWER = 1
_UPPER = 2

_GLOBAL_TT = {}


def _build_win_data():
    wins = []

    def bit(c: int, r: int) -> int:
        return 1 << (c * STRIDE + r)

    # Horizontal.
    for r in range(HEIGHT):
        for c in range(WIDTH - 3):
            m = 0
            for i in range(4):
                m |= bit(c + i, r)
            wins.append(m)

    # Vertical.
    for c in range(WIDTH):
        for r in range(HEIGHT - 3):
            m = 0
            for i in range(4):
                m |= bit(c, r + i)
            wins.append(m)

    # Diagonals.
    for c in range(WIDTH - 3):
        for r in range(HEIGHT - 3):
            m1 = 0
            m2 = 0
            for i in range(4):
                m1 |= bit(c + i, r + i)
                m2 |= bit(c + i, r + 3 - i)
            wins.append(m1)
            wins.append(m2)

    by_index = [[] for _ in range(WIDTH * STRIDE)]
    for m in wins:
        x = m
        while x:
            b = x & -x
            by_index[b.bit_length() - 1].append(m)
            x ^= b

    return tuple(wins), tuple(tuple(v) for v in by_index)


_WIN_MASKS, _LINES_BY_INDEX = _build_win_data()


class _Timeout(Exception):
    pass


def _possible(mask: int, bottom_all: int = BOTTOM_ALL, board_mask: int = BOARD_MASK) -> int:
    return (mask + bottom_all) & board_mask


def _is_win(pos: int, h: int = _SHIFT_H, d1: int = _SHIFT_D1, d2: int = _SHIFT_D2) -> bool:
    m = pos & (pos >> 1)
    if m & (m >> 2):
        return True

    m = pos & (pos >> h)
    if m & (m >> (2 * h)):
        return True

    m = pos & (pos >> d1)
    if m & (m >> (2 * d1)):
        return True

    m = pos & (pos >> d2)
    if m & (m >> (2 * d2)):
        return True

    return False


def _winning_position(
    pos: int,
    mask: int,
    board_mask: int = BOARD_MASK,
    h: int = _SHIFT_H,
    d1: int = _SHIFT_D1,
    d2: int = _SHIFT_D2,
) -> int:
    # Empty cells that would complete a four for pos.
    r = (pos << 1) & (pos << 2) & (pos << 3)

    p = (pos << h) & (pos << (2 * h))
    r |= p & (pos << (3 * h))
    r |= p & (pos >> h)
    p = (pos >> h) & (pos >> (2 * h))
    r |= p & (pos << h)
    r |= p & (pos >> (3 * h))

    p = (pos << d1) & (pos << (2 * d1))
    r |= p & (pos << (3 * d1))
    r |= p & (pos >> d1)
    p = (pos >> d1) & (pos >> (2 * d1))
    r |= p & (pos << d1)
    r |= p & (pos >> (3 * d1))

    p = (pos << d2) & (pos << (2 * d2))
    r |= p & (pos << (3 * d2))
    r |= p & (pos >> d2)
    p = (pos >> d2) & (pos >> (2 * d2))
    r |= p & (pos << d2)
    r |= p & (pos >> (3 * d2))

    return r & (board_mask & ~mask)


def _key(pos: int, opp: int) -> int:
    return pos | (opp << KEY_SHIFT)


def _score_win_after(mask: int, added: int) -> int:
    remaining = BOARD_CELLS - mask.bit_count() - added
    if remaining < 0:
        remaining = 0
    return _WIN_SCORE + remaining


def _col_from_bits(bits: int, order=COL_ORDER, col_masks=COLUMN_MASK) -> int:
    for c in order:
        if bits & col_masks[c]:
            return c
    return 0


def _to_bitboards(board) -> tuple[int, int, int]:
    pos = 0
    opp = 0
    for r in range(HEIGHT):
        br = HEIGHT - 1 - r
        row = board[r]
        for c in range(WIDTH):
            v = row[c]
            if v == 1:
                pos |= 1 << (c * STRIDE + br)
            elif v == -1:
                opp |= 1 << (c * STRIDE + br)
    return pos, opp, pos | opp


def _local_score(
    pos: int,
    opp: int,
    move: int,
    lines_by_index=_LINES_BY_INDEX,
    make=_LOCAL_MAKE,
    block=_LOCAL_BLOCK,
) -> int:
    idx = move.bit_length() - 1
    score = 0
    for line in lines_by_index[idx]:
        pc = (pos & line).bit_count()
        oc = (opp & line).bit_count()
        if oc == 0:
            score += make[pc + 1]
        elif pc == 0:
            score += block[oc]
    return score


def _evaluate(
    pos: int,
    opp: int,
    mask: int,
    win_masks=_WIN_MASKS,
    col_masks=COLUMN_MASK,
    col_weight=_COL_WEIGHT,
    my_window=_MY_WINDOW,
    opp_window=_OPP_WINDOW,
) -> int:
    score = 0

    for c in range(WIDTH):
        cm = col_masks[c]
        score += col_weight[c] * ((pos & cm).bit_count() - (opp & cm).bit_count())

    for wm in win_masks:
        pc = (pos & wm).bit_count()
        oc = (opp & wm).bit_count()
        if oc == 0:
            score += my_window[pc]
        elif pc == 0:
            score -= opp_window[oc]

    my_future = _winning_position(pos, mask).bit_count()
    opp_future = _winning_position(opp, mask).bit_count()
    score += 18 * my_future - 22 * opp_future

    return score


def _fallback_choice(pos: int, opp: int, mask: int) -> int:
    possible = _possible(mask)
    if not possible:
        return 0

    wins = _winning_position(pos, mask) & possible
    if wins:
        return _col_from_bits(wins)

    opp_all = _winning_position(opp, mask)
    opp_now = opp_all & possible
    if opp_now and not (opp_now & (opp_now - 1)):
        return _col_from_bits(opp_now)

    if opp_now:
        candidates = possible
    else:
        candidates = possible & ~(opp_all >> 1)
        if not candidates:
            candidates = possible

    # Prefer an immediate two-threat fork if available.
    for c in COL_ORDER:
        m = candidates & COLUMN_MASK[c]
        if m:
            nm = mask | m
            np = pos | m
            if not (_winning_position(opp, nm) & _possible(nm)):
                if ((_winning_position(np, nm) & _possible(nm)).bit_count()) >= 2:
                    return c

    best_col = _col_from_bits(candidates)
    best_score = -_INF

    for c in COL_ORDER:
        m = candidates & COLUMN_MASK[c]
        if not m:
            continue

        nm = mask | m
        np = pos | m
        s = _COL_ORDER_SCORE[c] * 8 + _local_score(pos, opp, m)

        if _winning_position(opp, nm) & _possible(nm):
            s -= 100000

        # Opponent-to-move evaluation after our move, negated.
        s -= _evaluate(opp, np, nm) // 4

        if s > best_score:
            best_score = s
            best_col = c

    return best_col


class _Solver:
    __slots__ = ("deadline", "nodes", "tt", "history")

    def __init__(self, deadline: float):
        self.deadline = deadline
        self.nodes = 0
        self.tt = _GLOBAL_TT
        self.history = [0] * WIDTH

    def _ordered_moves(self, pos: int, opp: int, mask: int, moves_bits: int, depth: int, hash_col: int):
        scored = []

        for c in COL_ORDER:
            m = moves_bits & COLUMN_MASK[c]
            if not m:
                continue

            s = _COL_ORDER_SCORE[c] + self.history[c]
            if c == hash_col:
                s += 1_000_000

            s += _local_score(pos, opp, m)

            if depth >= 2:
                nm = mask | m
                np = pos | m
                next_possible = _possible(nm)

                my_threats = _winning_position(np, nm) & next_possible
                tc = my_threats.bit_count()
                if tc == 1:
                    s += 800
                elif tc > 1:
                    s += 20000 + 2000 * tc

                opp_threats = _winning_position(opp, nm) & next_possible
                if opp_threats:
                    s -= 50000 * opp_threats.bit_count()

            scored.append((s, m, c))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [(m, c) for _, m, c in scored]

    def negamax(self, pos: int, opp: int, mask: int, depth: int, alpha: int, beta: int) -> int:
        self.nodes += 1
        if (self.nodes & 1023) == 0 and _perf_counter() > self.deadline:
            raise _Timeout()

        if _is_win(opp):
            return -_score_win_after(mask, 0)

        if mask == BOARD_MASK:
            return 0

        key = _key(pos, opp)
        alpha0 = alpha
        beta0 = beta
        hash_col = -1

        entry = self.tt.get(key)
        if entry is not None:
            edepth, flag, val, hcol = entry
            hash_col = hcol
            if edepth >= depth:
                if flag == _EXACT:
                    return val
                if flag == _LOWER:
                    if val > alpha:
                        alpha = val
                elif flag == _UPPER:
                    if val < beta:
                        beta = val
                if alpha >= beta:
                    return val

        possible = _possible(mask)
        if not possible:
            return 0

        win_bits = _winning_position(pos, mask) & possible
        if win_bits:
            val = _score_win_after(mask, 1)
            self.tt[key] = (depth, _EXACT, val, _col_from_bits(win_bits))
            return val

        opp_all = _winning_position(opp, mask)
        opp_now = opp_all & possible
        forced = False

        if opp_now:
            if opp_now & (opp_now - 1):
                val = -_score_win_after(mask, 2)
                self.tt[key] = (depth, _EXACT, val, _col_from_bits(opp_now))
                return val
            moves_bits = opp_now
            forced = True
        else:
            # Avoid playing directly below an opponent winning square.
            moves_bits = possible & ~(opp_all >> 1)
            if not moves_bits:
                val = -_score_win_after(mask, 2)
                self.tt[key] = (depth, _EXACT, val, -1)
                return val

        if depth <= 0 and not forced:
            val = _evaluate(pos, opp, mask)
            self.tt[key] = (depth, _EXACT, val, hash_col)
            return val

        ordered = self._ordered_moves(pos, opp, mask, moves_bits, depth, hash_col)
        value = -_INF
        best_col = -1
        next_depth = depth - 1 if depth > 0 else 0

        for m, c in ordered:
            score = -self.negamax(opp, pos | m, mask | m, next_depth, -beta, -alpha)

            if score > value:
                value = score
                best_col = c

            if score > alpha:
                alpha = score

            if alpha >= beta:
                if depth > 0:
                    self.history[c] += depth * depth
                break

        if best_col < 0:
            value = 0
            best_col = hash_col

        flag = _EXACT
        if value <= alpha0:
            flag = _UPPER
        elif value >= beta0:
            flag = _LOWER

        self.tt[key] = (depth, flag, value, best_col)
        return value

    def _search_root(self, pos: int, opp: int, mask: int, depth: int, root_bits: int, prev_col: int, fallback: int):
        alpha = -_INF
        beta = _INF
        best_col = fallback
        best_val = -_INF

        ordered = self._ordered_moves(pos, opp, mask, root_bits, depth, prev_col)
        if not ordered:
            return fallback, best_val

        next_depth = depth - 1

        for m, c in ordered:
            if _perf_counter() > self.deadline:
                raise _Timeout()

            val = -self.negamax(opp, pos | m, mask | m, next_depth, -beta, -alpha)

            if val > best_val:
                best_val = val
                best_col = c

            if val > alpha:
                alpha = val

        self.tt[_key(pos, opp)] = (depth, _EXACT, best_val, best_col)
        return best_col, best_val

    def best_move(self, pos: int, opp: int, mask: int, fallback: int) -> int:
        possible = _possible(mask)
        if not possible:
            return fallback

        wins = _winning_position(pos, mask) & possible
        if wins:
            return _col_from_bits(wins)

        opp_all = _winning_position(opp, mask)
        opp_now = opp_all & possible

        if opp_now:
            if not (opp_now & (opp_now - 1)):
                return _col_from_bits(opp_now)
            root_bits = possible
        else:
            root_bits = possible & ~(opp_all >> 1)
            if not root_bits:
                root_bits = possible

        if root_bits and not (root_bits & (root_bits - 1)):
            return _col_from_bits(root_bits)

        best = fallback
        prev = fallback
        empties = BOARD_CELLS - mask.bit_count()

        for depth in range(1, empties + 1):
            if _perf_counter() > self.deadline:
                break

            try:
                col, val = self._search_root(pos, opp, mask, depth, root_bits, prev, best)
            except _Timeout:
                break

            best = col
            prev = col

            if val >= _WIN_SCORE:
                break

        return best


def policy(board: list[list[int]]) -> int:
    legal_cols = []
    try:
        for c in COL_ORDER:
            if board[0][c] == 0:
                legal_cols.append(c)
        if not legal_cols:
            return 0
    except Exception:
        return 0

    try:
        if len(legal_cols) == 1:
            return int(legal_cols[0])

        pos, opp, mask = _to_bitboards(board)
        possible = _possible(mask)

        if not possible:
            return int(legal_cols[0])

        # Win immediately if possible.
        wins = _winning_position(pos, mask) & possible
        if wins:
            col = _col_from_bits(wins)
            if col in legal_cols:
                return int(col)

        # Block a single immediate opponent win.
        opp_all = _winning_position(opp, mask)
        opp_now = opp_all & possible
        if opp_now and not (opp_now & (opp_now - 1)):
            col = _col_from_bits(opp_now)
            if col in legal_cols:
                return int(col)

        # Strong opening rule.
        if mask.bit_count() <= 1 and 3 in legal_cols:
            return 3

        # If we can create two immediate winning threats safely, do it.
        if not opp_now:
            safe_bits = possible & ~(opp_all >> 1)
            if safe_bits:
                for c in COL_ORDER:
                    m = safe_bits & COLUMN_MASK[c]
                    if not m:
                        continue
                    nm = mask | m
                    np = pos | m
                    if not (_winning_position(opp, nm) & _possible(nm)):
                        if ((_winning_position(np, nm) & _possible(nm)).bit_count()) >= 2:
                            if c in legal_cols:
                                return int(c)

        fallback = _fallback_choice(pos, opp, mask)
        if fallback not in legal_cols:
            fallback = legal_cols[0]

        if len(_GLOBAL_TT) > _TT_LIMIT:
            _GLOBAL_TT.clear()

        deadline = _perf_counter() + _TIME_LIMIT
        solver = _Solver(deadline)
        best = solver.best_move(pos, opp, mask, fallback)

        if best in legal_cols:
            return int(best)
        return int(fallback)

    except Exception:
        return int(legal_cols[0])
