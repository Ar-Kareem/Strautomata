
import time

_FULL = (1 << 36) - 1
_MATE = 10_000_000
_INF = 100_000_000


def _index(r, c):
    return ((r // 3) * 2 + c // 3) * 9 + (r % 3) * 3 + c % 3


_COORD = [None] * 36
for _r in range(6):
    for _c in range(6):
        _COORD[_index(_r, _c)] = (_r, _c)


def _rotation_table(clockwise):
    table = []
    for mask in range(512):
        result = 0
        for r in range(3):
            for c in range(3):
                if mask & (1 << (3 * r + c)):
                    if clockwise:
                        nr, nc = c, 2 - r
                    else:
                        nr, nc = 2 - c, r
                    result |= 1 << (3 * nr + nc)
        table.append(result)
    return table


_LEFT = _rotation_table(False)
_RIGHT = _rotation_table(True)
_SHIFT = []
_KEEP = []
_ROT = []

# Rotation numbers are 0L, 0R, 1L, 1R, 2L, 2R, 3L, 3R.
for _q in range(4):
    for _table in (_LEFT, _RIGHT):
        _s = 9 * _q
        _SHIFT.append(_s)
        _KEEP.append(_FULL ^ (511 << _s))
        _ROT.append(tuple(x << _s for x in _table))


def _rotate(board, rotation):
    return (
        (board & _KEEP[rotation])
        | _ROT[rotation][(board >> _SHIFT[rotation]) & 511]
    )


# Convert a placement on the rotated board back to its legal input square.
_ACTION = []
for _t in range(8):
    _actions = []
    for _i in range(36):
        _source = _rotate(1 << _i, _t ^ 1).bit_length() - 1
        _r, _c = _COORD[_source]
        _actions.append(
            f"{_r + 1},{_c + 1},{_t // 2},{'L' if _t % 2 == 0 else 'R'}"
        )
    _ACTION.append(tuple(_actions))


def _mask(cells):
    result = 0
    for r, c in cells:
        result |= 1 << _index(r, c)
    return result


_WIN = []
for _r in range(6):
    for _c in range(2):
        _WIN.append(_mask((_r, _c + k) for k in range(5)))
for _c in range(6):
    for _r in range(2):
        _WIN.append(_mask((_r + k, _c) for k in range(5)))
for _r in range(2):
    for _c in range(2):
        _WIN.append(_mask((_r + k, _c + k) for k in range(5)))
    for _c in (4, 5):
        _WIN.append(_mask((_r + k, _c - k) for k in range(5)))
_WIN = tuple(_WIN)

_LONG_WEIGHTS = (0, 2, 14, 90, 650, 100_000)
_SHORT_WEIGHTS = (0, 0, 5, 32)
_EVAL_LINES = [(m, _LONG_WEIGHTS) for m in _WIN]

for _q in range(4):
    _r0, _c0 = 3 * (_q // 2), 3 * (_q % 2)
    for _k in range(3):
        _EVAL_LINES.append((
            _mask((_r0 + _k, _c0 + j) for j in range(3)),
            _SHORT_WEIGHTS
        ))
        _EVAL_LINES.append((
            _mask((_r0 + j, _c0 + _k) for j in range(3)),
            _SHORT_WEIGHTS
        ))
    _EVAL_LINES.append((
        _mask((_r0 + j, _c0 + j) for j in range(3)),
        _SHORT_WEIGHTS
    ))
    _EVAL_LINES.append((
        _mask((_r0 + j, _c0 + 2 - j) for j in range(3)),
        _SHORT_WEIGHTS
    ))
_EVAL_LINES = tuple(_EVAL_LINES)

# These bonuses are invariant under quadrant rotations.
_LOCAL_POS = (1, 0, 1, 0, 4, 0, 1, 0, 1)
_POS = list(_LOCAL_POS) * 4
_POS_SUM = tuple(
    sum(_LOCAL_POS[i] for i in range(9) if m & (1 << i))
    for m in range(512)
)


def _position(board):
    return (
        _POS_SUM[board & 511]
        + _POS_SUM[(board >> 9) & 511]
        + _POS_SUM[(board >> 18) & 511]
        + _POS_SUM[(board >> 27) & 511]
    )


class _Timeout(Exception):
    pass


class _Engine:
    def __init__(self, deadline):
        self.deadline = deadline
        self.pattern_cache = {}
        self.info_cache = {}
        self.tt = {}
        self.hints = {}
        self.nodes = 0

    def check_time(self):
        if time.perf_counter() >= self.deadline:
            raise _Timeout

    def patterns(self, a, b):
        """Existing wins and empty squares completing an unblocked five."""
        key = (a, b)
        cached = self.pattern_cache.get(key)
        if cached is not None:
            return cached

        flags = 0
        a_gaps = 0
        b_gaps = 0

        for line in _WIN:
            aa = a & line
            bb = b & line
            if aa and bb:
                continue

            if aa:
                missing = line ^ aa
                if not missing:
                    flags |= 1
                elif not (missing & (missing - 1)):
                    a_gaps |= missing
            elif bb:
                missing = line ^ bb
                if not missing:
                    flags |= 2
                elif not (missing & (missing - 1)):
                    b_gaps |= missing

        result = (flags, a_gaps, b_gaps)
        self.pattern_cache[key] = result
        return result

    def scored_placements(self, a, b, targets, rotation):
        """Score every target using incremental line-score updates."""
        base = _position(a) - _position(b)
        delta = _POS[:]

        for line, weights in _EVAL_LINES:
            aa = a & line
            bb = b & line
            if aa and bb:
                continue

            available = line & targets
            if not bb:
                n = aa.bit_count()
                base += weights[n]
                if not available:
                    continue
                gain = weights[n + 1] - weights[n]
            else:
                value = weights[bb.bit_count()]
                base -= value
                if not available:
                    continue
                gain = value

            if gain:
                while available:
                    bit = available & -available
                    available ^= bit
                    delta[bit.bit_length() - 1] += gain

        result = []
        actions = _ACTION[rotation]
        while targets:
            bit = targets & -targets
            targets ^= bit
            i = bit.bit_length() - 1
            result.append((base + delta[i], a | bit, b, actions[i]))
        return result

    def info(self, a, b, root=False):
        """
        Return:
          (status, action, moves, leaf_value, drawing_move)

        status: 0 normal, 1 immediate win, 2 draw,
                -1 unavoidable immediate loss, -2 loss next turn.
        """
        key = (a, b)
        cached = self.info_cache.get(key)
        if cached is not None:
            return cached
        self.check_time()

        empty = _FULL ^ (a | b)
        count_empty = empty.bit_count()
        count_a = a.bit_count()
        count_b = b.bit_count()

        if not empty:
            result = (2, None, (), 0, None)
            self.info_cache[key] = result
            return result

        first = (empty & -empty).bit_length() - 1
        fallback = _ACTION[0][
            _rotate(1 << first, 0).bit_length() - 1
        ]

        viable = []
        draw = None

        # First examine all immediate terminal outcomes.
        for t in range(8):
            ar = _rotate(a, t)
            br = _rotate(b, t)
            er = _FULL ^ (ar | br)

            if count_a >= 4 or count_b >= 5:
                flags, gaps, _ = self.patterns(ar, br)
            else:
                flags, gaps = 0, 0

            if not (flags & 2):
                winning = er if flags & 1 else gaps
                if winning:
                    bit = winning & -winning
                    action = _ACTION[t][bit.bit_length() - 1]
                    result = (1, action, (), _MATE, None)
                    self.info_cache[key] = result
                    return result

            if flags & 2:
                drawing = er if flags & 1 else gaps
                if drawing and draw is None:
                    bit = drawing & -drawing
                    draw = (0, -1, -1, _ACTION[t][bit.bit_length() - 1])
                continue

            if count_empty == 1:
                bit = er & -er
                if draw is None:
                    draw = (0, -1, -1, _ACTION[t][bit.bit_length() - 1])
                continue

            viable.append((t, ar, br, er))
            if len(viable) == 1:
                bit = er & -er
                fallback = _ACTION[t][bit.bit_length() - 1]

        moves = []
        seen = set()

        for t, ar, br, er in viable:
            self.check_time()
            safe = er

            if count_b >= 4:
                # For every possible opponent rotation, derive all placements
                # that prevent a decisive opponent win.
                for next_t in range(8):
                    aa = _rotate(ar, next_t)
                    bb = _rotate(br, next_t)
                    flags, our_gaps, their_gaps = self.patterns(aa, bb)

                    # Our existing five makes their win at most a draw.
                    if flags & 1:
                        continue

                    if flags & 2:
                        good = our_gaps
                    elif their_gaps:
                        good = our_gaps
                        # One marble can block a unique winning square.
                        if not (their_gaps & (their_gaps - 1)):
                            good |= their_gaps
                    else:
                        continue

                    safe &= _rotate(good, next_t ^ 1)
                    if not safe:
                        break

            if safe:
                for move in self.scored_placements(ar, br, safe, t):
                    state = (move[1], move[2])
                    if state not in seen:
                        seen.add(state)
                        moves.append(move)

        if draw is not None:
            moves.append(draw)

        if not moves:
            # In a proven losing position, still choose a legal, constructive
            # nonterminal move when one exists.
            if root and viable:
                best = None
                for t, ar, br, er in viable:
                    self.check_time()
                    for move in self.scored_placements(ar, br, er, t):
                        if best is None or move[0] > best[0]:
                            best = move
                if best is not None:
                    fallback = best[3]

            status = -2 if viable else -1
            result = (status, fallback, (), -_MATE, None)
        elif len(moves) == 1 and moves[0][1] == -1:
            result = (2, moves[0][3], (), 0, moves[0])
        else:
            moves.sort(key=lambda m: m[0], reverse=True)
            result = (0, moves[0][3], moves, moves[0][0], draw)

        self.info_cache[key] = result
        return result

    def search(self, a, b, depth, alpha, beta, ply):
        self.nodes += 1
        if not (self.nodes & 63):
            self.check_time()

        info = self.info(a, b)
        status = info[0]
        if status == 1:
            return _MATE - ply - 1
        if status == 2:
            return 0
        if status < 0:
            return -_MATE + ply - status

        # The leaf includes one complete, tactically filtered move.
        if depth <= 0:
            return info[3]

        original_alpha = alpha
        original_beta = beta
        tt_key = (a, b, depth)
        entry = self.tt.get(tt_key)
        if entry is not None:
            value, flag = entry
            if flag == 0:
                return value
            if flag > 0:
                alpha = max(alpha, value)
            else:
                beta = min(beta, value)
            if alpha >= beta:
                return value

        moves = info[2]
        empty_count = 36 - (a | b).bit_count()
        if empty_count <= 6:
            limit = len(moves)
        elif empty_count <= 12:
            limit = 20
        elif depth >= 3:
            limit = 10
        else:
            limit = 14

        hint = self.hints.get((a, b))
        ordered = moves
        if hint is not None and moves[0][3] != hint:
            for i, move in enumerate(moves):
                if move[3] == hint:
                    ordered = [move] + moves[:i] + moves[i + 1:]
                    break

        draw = info[4]
        best = 0 if draw is not None else -_INF
        best_action = draw[3] if draw is not None else ordered[0][3]
        alpha = max(alpha, best)

        if alpha >= beta:
            return best

        searched = 0
        for move in ordered:
            if move[1] == -1:
                continue

            # Widen the search rather than declaring a mate loss solely
            # because all selected moves lose.
            if searched >= limit and best > -_MATE // 2:
                break

            value = -self.search(
                move[2], move[1], depth - 1,
                -beta, -alpha, ply + 1
            )
            searched += 1

            if value > best:
                best = value
                best_action = move[3]
            if value > alpha:
                alpha = value
            if alpha >= beta:
                break

        self.hints[(a, b)] = best_action
        if best <= original_alpha:
            flag = -1
        elif best >= original_beta:
            flag = 1
        else:
            flag = 0
        self.tt[tt_key] = (best, flag)
        return best


def policy(you, opponent) -> str:
    started = time.perf_counter()
    a = 0
    b = 0
    fallback = None

    for r in range(6):
        for c in range(6):
            bit = 1 << _index(r, c)
            if you[r][c]:
                a |= bit
            elif opponent[r][c]:
                b |= bit
            elif fallback is None:
                fallback = f"{r + 1},{c + 1},0,L"

    # A stable, central opening; all quadrant centers are equivalent here.
    if not (a | b):
        return "2,2,0,L"

    best_action = fallback
    engine = _Engine(started + 0.90)

    try:
        root = engine.info(a, b, root=True)
        best_action = root[1] or fallback
        if root[0] != 0:
            return best_action

        moves = root[2]
        ranked = []
        best_value = -_INF

        # Exhaustively assess every safe root move. This also detects
        # forced wins in three plies without a selective root beam.
        for move in moves:
            engine.check_time()
            if move[1] == -1:
                value = 0
            else:
                value = -engine.search(
                    move[2], move[1], 0, -_INF, _INF, 1
                )
            ranked.append((value, move))

            if value > best_value:
                best_value = value
                best_action = move[3]

            if value > _MATE // 2:
                return best_action

        ranked.sort(key=lambda item: item[0], reverse=True)
        ordered = [item[1] for item in ranked]
        empty_count = 36 - (a | b).bit_count()

        # Additional iterative-deepening passes use selective ordering,
        # while immediate tactical checks remain exhaustive at every node.
        for depth in range(2, min(empty_count, 12) + 1):
            engine.check_time()
            if empty_count <= 8:
                limit = len(ordered)
            else:
                limit = 32 if depth == 2 else 24

            draw = root[4]
            iteration_best = 0 if draw is not None else -_INF
            iteration_move = draw
            alpha = iteration_best
            searched = 0

            for move in ordered:
                if move[1] == -1:
                    continue
                if searched >= limit and iteration_best > -_MATE // 2:
                    break

                engine.check_time()
                value = -engine.search(
                    move[2], move[1], depth - 1,
                    -_INF, -alpha, 1
                )
                searched += 1

                if value > iteration_best:
                    iteration_best = value
                    iteration_move = move
                if value > alpha:
                    alpha = value

                # Keep improvements from completed root branches even if
                # the next branch runs out of time.
                if iteration_move is not None:
                    best_action = iteration_move[3]

                if iteration_best > _MATE // 2:
                    return best_action

            if iteration_move is not None:
                best_action = iteration_move[3]
                ordered = [iteration_move] + [
                    m for m in ordered if m[3] != best_action
                ]

    except _Timeout:
        pass
    except Exception:
        # The already selected action always comes from an empty input
        # square, so unexpected failures cannot produce an illegal move.
        pass

    return best_action
