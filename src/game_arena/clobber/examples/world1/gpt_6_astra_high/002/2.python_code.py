
import time

ROWS = 5
COLS = 6
FULL = (1 << 30) - 1
LEFT = sum(1 << (6 * r) for r in range(5))
RIGHT = LEFT << 5
NOT_LEFT = FULL ^ LEFT
NOT_RIGHT = FULL ^ RIGHT
WIN = 100000

STAR_MOVE = 960
UP_MOVE = 961

SOURCE = [0] * 1024
TARGET = [0] * 1024
NEIGHBORS = [0] * 30

for _s in range(30):
    for _t in range(30):
        SOURCE[(_s << 5) | _t] = 1 << _s
        TARGET[(_s << 5) | _t] = 1 << _t

for _i in range(30):
    _r, _c = divmod(_i, 6)
    for _dr, _dc in ((-1, 0), (0, 1), (1, 0), (0, -1)):
        _rr, _cc = _r + _dr, _c + _dc
        if 0 <= _rr < 5 and 0 <= _cc < 6:
            NEIGHBORS[_i] |= 1 << (6 * _rr + _cc)

REV6 = [int(format(i, "06b")[::-1], 2) for i in range(64)]

# These caches can also be reused when the arena retains the module.
_SMALL_RAW = {}
_SMALL_VALUES = {}
_TINY_TT = {}


def adjacent(x):
    return (
        (x << 6)
        | (x >> 6)
        | ((x & NOT_RIGHT) << 1)
        | ((x & NOT_LEFT) >> 1)
    ) & FULL


def legal_moves(a, b):
    result = []

    targets = (a >> 6) & b
    while targets:
        t = targets & -targets
        targets ^= t
        j = t.bit_length() - 1
        result.append(((j + 6) << 5) | j)

    targets = ((a & NOT_RIGHT) << 1) & b
    while targets:
        t = targets & -targets
        targets ^= t
        j = t.bit_length() - 1
        result.append(((j - 1) << 5) | j)

    targets = (a << 6) & b
    while targets:
        t = targets & -targets
        targets ^= t
        j = t.bit_length() - 1
        result.append(((j - 6) << 5) | j)

    targets = ((a & NOT_LEFT) >> 1) & b
    while targets:
        t = targets & -targets
        targets ^= t
        j = t.bit_length() - 1
        result.append(((j + 1) << 5) | j)

    return result


def move_string(move):
    s, t = move >> 5, move & 31
    direction = {-6: "U", 1: "R", 6: "D", -1: "L"}[t - s]
    return f"{s // 6},{s % 6},{direction}"


def flip_horizontal(x):
    return (
        REV6[x & 63]
        | (REV6[(x >> 6) & 63] << 6)
        | (REV6[(x >> 12) & 63] << 12)
        | (REV6[(x >> 18) & 63] << 18)
        | (REV6[(x >> 24) & 63] << 24)
    )


def flip_vertical(x):
    return (
        ((x & 63) << 24)
        | (((x >> 6) & 63) << 18)
        | (x & (63 << 12))
        | (((x >> 18) & 63) << 6)
        | ((x >> 24) & 63)
    )


def rectangle_key(a, b):
    ah, bh = flip_horizontal(a), flip_horizontal(b)
    return min(
        (a, b),
        (ah, bh),
        (flip_vertical(a), flip_vertical(b)),
        (flip_vertical(ah), flip_vertical(bh)),
    )


def small_key(a, b):
    """Canonicalize a component of at most five cells."""
    cells = []
    u = a | b
    while u:
        bit = u & -u
        u ^= bit
        i = bit.bit_length() - 1
        cells.append((i // 6, i % 6, bool(a & bit)))

    r0 = min(x[0] for x in cells)
    c0 = min(x[1] for x in cells)
    h = max(x[0] for x in cells) - r0
    w = max(x[1] for x in cells) - c0
    cells = [(r - r0, c - c0, own) for r, c, own in cells]

    boards = [[0, 0] for _ in range(8)]
    for r, c, own in cells:
        positions = (
            (r, c),
            (r, w - c),
            (h - r, c),
            (h - r, w - c),
            (c, r),
            (c, h - r),
            (w - c, r),
            (w - c, h - r),
        )
        side = 0 if own else 1
        for k, (rr, cc) in enumerate(positions):
            boards[k][side] |= 1 << (rr * 6 + cc)

    best = (FULL + 1, FULL + 1)
    sign = 1
    for aa, bb in boards:
        if (aa, bb) < best:
            best = (aa, bb)
            sign = 1
        if (bb, aa) < best:
            best = (bb, aa)
            sign = -1
    return best, sign


def pure_win(n, p):
    # Exact outcome for n * up + p * star, from the mover's viewpoint.
    return n > 0 or (bool(p) and n >= -1)


class SearchTimeout(Exception):
    pass


class Engine:
    def __init__(self, deadline):
        self.deadline = deadline
        self.nodes = 0
        self.tt = {}
        self.normalized = {}
        self.history = [[0] * 1024 for _ in range(2)]
        self.killers = [[-1, -1] for _ in range(64)]

    def touch(self):
        self.nodes += 1
        if not (self.nodes & 127):
            if time.perf_counter() >= self.deadline:
                raise SearchTimeout

    def tiny_win(self, a, b, n, p):
        """Exact solver used to identify small combinatorial games."""
        self.touch()
        if not (a & adjacent(b)):
            return pure_win(n, p)

        key = (a, b, n, p)
        cached = _TINY_TT.get(key)
        if cached is not None:
            return cached

        if n > 0 and not self.tiny_win(b, a, 1 - n, p):
            _TINY_TT[key] = True
            return True

        if p and not self.tiny_win(b, a, -n, 0):
            _TINY_TT[key] = True
            return True

        for move in legal_moves(a, b):
            s, t = SOURCE[move], TARGET[move]
            if not self.tiny_win(b ^ t, (a ^ s) | t, -n, p):
                _TINY_TT[key] = True
                return True

        if n < 0 and not self.tiny_win(b, a, -n - 1, p ^ 1):
            _TINY_TT[key] = True
            return True

        _TINY_TT[key] = False
        return False

    def classify(self, a, b):
        """
        Identify exact values 0, *, and n*up + p*star.
        Equality is verified by solving the difference game.
        """
        left = self.tiny_win(a, b, 0, 0)
        right = self.tiny_win(b, a, 0, 0)

        if not left and not right:
            return (0, 0)

        if left and right:
            ls = self.tiny_win(a, b, 0, 1)
            rs = self.tiny_win(b, a, 0, 1)
            if not ls and not rs:
                return (0, 1)
            if ls and not rs:
                candidates = ((1, 1),)
            elif rs and not ls:
                candidates = ((-1, 1),)
            else:
                return None
        elif left:
            candidates = ((1, 0), (2, 0), (2, 1))
        else:
            candidates = ((-1, 0), (-2, 0), (-2, 1))

        for n, p in candidates:
            if (
                not self.tiny_win(a, b, -n, p)
                and not self.tiny_win(b, a, n, p)
            ):
                return (n, p)
        return None

    def component_value(self, a, b):
        raw = (a, b)
        if raw in _SMALL_RAW:
            return _SMALL_RAW[raw]

        canonical, sign = small_key(a, b)
        if canonical not in _SMALL_VALUES:
            _SMALL_VALUES[canonical] = self.classify(*canonical)

        value = _SMALL_VALUES[canonical]
        if value is not None:
            value = (sign * value[0], value[1])

        _SMALL_RAW[raw] = value
        _SMALL_RAW[(b, a)] = (
            None if value is None else (-value[0], value[1])
        )
        return value

    def reduce(self, a, b, n, p):
        if (a | b).bit_count() > 20:
            return a, b, n, p

        key = (a, b)
        cached = self.normalized.get(key)
        if cached is None:
            remaining = a | b
            aa = bb = nn = pp = 0

            while remaining:
                component = remaining & -remaining
                while True:
                    expanded = component | (adjacent(component) & remaining)
                    if expanded == component:
                        break
                    component = expanded
                remaining ^= component

                ca, cb = a & component, b & component
                if not ca or not cb:
                    continue

                value = None
                if component.bit_count() <= 5:
                    value = self.component_value(ca, cb)

                if value is None:
                    aa |= ca
                    bb |= cb
                else:
                    nn += value[0]
                    pp ^= value[1]

            cached = (aa, bb, nn, pp)
            self.normalized[key] = cached
            self.normalized[(b, a)] = (bb, aa, -nn, pp)
            self.normalized[(aa, bb)] = (aa, bb, 0, 0)
            self.normalized[(bb, aa)] = (bb, aa, 0, 0)

        aa, bb, nn, pp = cached
        return aa, bb, n + nn, p ^ pp

    @staticmethod
    def evaluate(a, b, n, p):
        na, nb = adjacent(a), adjacent(b)
        active_a = a & nb
        if not active_a:
            return WIN if pure_win(n, p) else -WIN

        active_b = b & na
        friendly_a = a & na
        friendly_b = b & nb

        # Legal edge counts are identical for both players in Clobber.
        # Instead, value supported frontiers and useful reserves.
        return (
            80 * n
            + 12 * (a.bit_count() - b.bit_count())
            + 6 * (active_a.bit_count() - active_b.bit_count())
            + 40 * (
                (active_a & na).bit_count()
                - (active_b & nb).bit_count()
            )
            + 8 * (friendly_a.bit_count() - friendly_b.bit_count())
            + 4 * p
        )

    @staticmethod
    def child(a, b, n, p, move):
        if move == STAR_MOVE:
            return b, a, -n, 0
        if move == UP_MOVE:
            if n > 0:
                return b, a, 1 - n, p
            return b, a, -n - 1, p ^ 1
        s, t = SOURCE[move], TARGET[move]
        return b ^ t, (a ^ s) | t, -n, p

    def ordered(self, a, b, n, p, depth, ply, tt_move):
        moves = legal_moves(a, b)
        if p:
            moves.append(STAR_MOVE)
        if n:
            moves.append(UP_MOVE)

        killers = self.killers[min(ply, 63)]
        history = self.history[ply & 1]
        ordered = []

        for move in moves:
            child = self.child(a, b, n, p, move)

            if move == tt_move:
                score = 100000000
            else:
                score = history[move]
                if move == killers[0]:
                    score += 20000
                elif move == killers[1]:
                    score += 15000

                if depth >= 2 or move >= STAR_MOVE:
                    score -= 4 * self.evaluate(*child)
                else:
                    s, t = move >> 5, move & 31
                    score += 32 * (
                        (NEIGHBORS[t] & a).bit_count()
                        - (NEIGHBORS[s] & a).bit_count()
                        + (NEIGHBORS[t] & b).bit_count()
                    )

            ordered.append((score, move, child))

        ordered.sort(key=lambda item: item[0], reverse=True)
        return ordered

    def search(self, a, b, n, p, depth, alpha, beta, ply):
        self.touch()
        a, b, n, p = self.reduce(a, b, n, p)

        if not (a & adjacent(b)):
            return WIN if pure_win(n, p) else -WIN

        key = (a, b, n, p)
        entry = self.tt.get(key)
        tt_move = -1

        if entry is not None:
            stored_depth, flag, value, tt_move = entry
            if stored_depth >= depth:
                if flag == 0:
                    return value
                if flag == 1 and value >= beta:
                    return value
                if flag == 2 and value <= alpha:
                    return value

        if depth <= 0:
            return self.evaluate(a, b, n, p)

        original_alpha = alpha
        best = -WIN
        best_move = -1
        ordered = self.ordered(a, b, n, p, depth, ply, tt_move)
        large_position = (a | b).bit_count() >= 14
        non_pv = beta == alpha + 1

        for index, (_, move, child) in enumerate(ordered):
            if index == 0:
                value = -self.search(
                    *child, depth - 1, -beta, -alpha, ply + 1
                )
            else:
                reduction = 0
                if (
                    non_pv
                    and depth >= 4
                    and index >= 5
                    and large_position
                    and move < STAR_MOVE
                    and move not in self.killers[min(ply, 63)]
                ):
                    reduction = 1

                value = -self.search(
                    *child,
                    depth - 1 - reduction,
                    -alpha - 1,
                    -alpha,
                    ply + 1
                )

                if reduction and value > alpha:
                    value = -self.search(
                        *child, depth - 1, -alpha - 1, -alpha, ply + 1
                    )

                if alpha < value < beta:
                    value = -self.search(
                        *child, depth - 1, -beta, -alpha, ply + 1
                    )

            if value > best or best_move == -1:
                best, best_move = value, move

            if value > alpha:
                alpha = value

            if alpha >= beta:
                killers = self.killers[min(ply, 63)]
                if killers[0] != move:
                    killers[1] = killers[0]
                    killers[0] = move

                history = self.history[ply & 1]
                bonus = min(512, 4 * depth * depth)
                old = history[move]
                history[move] = old + bonus - old * bonus // 4096
                break

        if best <= original_alpha:
            flag = 2
        elif best >= beta:
            flag = 1
        else:
            flag = 0

        stored_depth = 99 if abs(best) == WIN else depth
        self.tt[key] = (stored_depth, flag, best, best_move)
        return best


def _read_board(board):
    bits = 0
    if len(board) == 30:
        for i in range(30):
            if board[i]:
                bits |= 1 << i
    else:
        for r in range(5):
            for c in range(6):
                if board[r][c]:
                    bits |= 1 << (6 * r + c)
    return bits


def policy(you: list[int], opponent: list[int]) -> str:
    start = time.perf_counter()
    a = _read_board(you)
    b = _read_board(opponent)
    moves = legal_moves(a, b)

    # A terminal position has no legal action; arenas normally do not call
    # the policy there.
    if not moves:
        return "0,0,U"

    fallback = moves[0]
    if len(moves) == 1:
        return move_string(fallback)

    if len(_SMALL_RAW) > 20000:
        _SMALL_RAW.clear()
    if len(_TINY_TT) > 150000:
        _TINY_TT.clear()

    engine = Engine(start + 0.91)
    best_move = fallback

    try:
        roots = []
        seen = set()

        for move in moves:
            if time.perf_counter() >= engine.deadline:
                raise SearchTimeout

            s, t = SOURCE[move], TARGET[move]
            ca, cb = rectangle_key(b ^ t, (a ^ s) | t)
            if (ca, cb) in seen:
                continue
            seen.add((ca, cb))

            child = engine.reduce(ca, cb, 0, 0)
            estimate = -engine.evaluate(*child)

            if estimate == WIN:
                return move_string(move)

            roots.append((estimate, move, child))

        roots.sort(key=lambda item: item[0], reverse=True)
        best_move = roots[0][1]

        for depth in range(1, 36):
            if time.perf_counter() >= engine.deadline:
                break

            alpha = -WIN
            iteration_best = roots[0][1]
            updated = []

            for index, (_, move, child) in enumerate(roots):
                if time.perf_counter() >= engine.deadline:
                    raise SearchTimeout

                if index == 0:
                    value = -engine.search(
                        *child, depth - 1, -WIN, WIN, 1
                    )
                else:
                    value = -engine.search(
                        *child, depth - 1, -alpha - 1, -alpha, 1
                    )
                    if alpha < value < WIN:
                        value = -engine.search(
                            *child, depth - 1, -WIN, -alpha, 1
                        )

                updated.append((value, move, child))

                if value > alpha:
                    alpha = value
                    iteration_best = move

                if value == WIN:
                    return move_string(move)

            # Only completed iterations replace the established fallback.
            best_move = iteration_best
            updated.sort(key=lambda item: item[0], reverse=True)
            roots = updated

            if alpha == -WIN:
                break

    except SearchTimeout:
        pass

    return move_string(best_move)
