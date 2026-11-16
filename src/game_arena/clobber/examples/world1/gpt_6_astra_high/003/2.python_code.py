
import time

ROWS = 5
COLS = 6
FULL = (1 << 30) - 1
LEFT = sum(1 << (6 * r) for r in range(5))
RIGHT = LEFT << 5
NOT_LEFT = FULL ^ LEFT
NOT_RIGHT = FULL ^ RIGHT
WIN = 1000000


def _adj(x):
    return (
        (x << 6)
        | (x >> 6)
        | ((x & NOT_RIGHT) << 1)
        | ((x & NOT_LEFT) >> 1)
    ) & FULL


NEIGHBORS = [_adj(1 << i) for i in range(30)]


def _moves(a, b):
    result = []

    x = a & (b >> 6)
    while x:
        s = x & -x
        x -= s
        result.append((s, s << 6))

    x = a & (b << 6)
    while x:
        s = x & -x
        x -= s
        result.append((s, s >> 6))

    x = a & ((b & NOT_LEFT) >> 1)
    while x:
        s = x & -x
        x -= s
        result.append((s, s << 1))

    x = a & ((b & NOT_RIGHT) << 1)
    while x:
        s = x & -x
        x -= s
        result.append((s, s >> 1))

    return result


# Exact short-game database.
# A game stores its Left and Right options, its inverse, and outcomes
# both by itself and with one additional independent single-move game.
_GL = [(), (0,)]
_GR = [(), (0,)]
_GINV = [0, 1]
_GLW = [False, True]
_GRW = [False, True]
_GLS = [True, False]
_GRS = [True, False]
_GBIAS = [0, 0]
_GAME_MAP = {
    ((), ()): 0,
    ((0,), (0,)): 1,
}

_SMALL = {}
_REDUCTIONS = {}
_SUM_CACHE = {}
_TT = {}


def _intern_game(left, right):
    left = tuple(sorted(set(left)))
    right = tuple(sorted(set(right)))
    signature = (left, right)

    old = _GAME_MAP.get(signature)
    if old is not None:
        return old

    inverse_signature = (
        tuple(sorted(_GINV[g] for g in right)),
        tuple(sorted(_GINV[g] for g in left)),
    )

    lw = any(not _GRW[g] for g in left)
    rw = any(not _GLW[g] for g in right)

    # A previous-player win for either starting color is exactly zero.
    if not lw and not rw:
        _GAME_MAP[signature] = 0
        _GAME_MAP[inverse_signature] = 0
        return 0

    ls = (not rw) or any(not _GRS[g] for g in left)
    rs = (not lw) or any(not _GLS[g] for g in right)

    # If G + * is zero, then G is exactly *.
    if not ls and not rs:
        _GAME_MAP[signature] = 1
        _GAME_MAP[inverse_signature] = 1
        return 1

    g = len(_GL)
    h = g if signature == inverse_signature else g + 1
    bias = 100 if lw and not rw else -100 if rw and not lw else 0

    _GL.append(left)
    _GR.append(right)
    _GINV.append(h)
    _GLW.append(lw)
    _GRW.append(rw)
    _GLS.append(ls)
    _GRS.append(rs)
    _GBIAS.append(bias)
    _GAME_MAP[signature] = g

    if h != g:
        _GL.append(inverse_signature[0])
        _GR.append(inverse_signature[1])
        _GINV.append(g)
        _GLW.append(rw)
        _GRW.append(lw)
        _GLS.append(rs)
        _GRS.append(ls)
        _GBIAS.append(-bias)

    _GAME_MAP[inverse_signature] = h
    return g


def _small_game(a, b):
    # Isolated pieces can never participate in a future move.
    occupied = a | b
    connected = _adj(occupied)
    a &= connected
    b &= connected

    if not (a & _adj(b)):
        return 0

    key = a | (b << 30)
    old = _SMALL.get(key)
    if old is not None:
        return old

    left = []
    for s, d in _moves(a, b):
        left.append(_small_game(a ^ s ^ d, b ^ d))

    right = []
    for s, d in _moves(b, a):
        right.append(_small_game(a ^ d, b ^ s ^ d))

    g = _intern_game(left, right)
    _SMALL[key] = g
    _SMALL[b | (a << 30)] = _GINV[g]
    return g


def _canonical_sum(games):
    counts = {}
    for g in games:
        if g == 0:
            continue
        inverse = _GINV[g]
        n = counts.get(inverse, 0)
        if n:
            if n == 1:
                del counts[inverse]
            else:
                counts[inverse] = n - 1
        else:
            counts[g] = counts.get(g, 0) + 1

    return tuple(
        g
        for g in sorted(counts)
        for _ in range(counts[g])
    )


def _reduce(a, b):
    key = a | (b << 30)
    cached = _REDUCTIONS.get(key)
    if cached is not None:
        return cached

    remaining = a | b
    large_a = 0
    large_b = 0
    has_large = False
    star = 0
    pending = {}

    while remaining:
        component = remaining & -remaining
        while True:
            expanded = component | (_adj(component) & remaining)
            if expanded == component:
                break
            component = expanded

        remaining ^= component
        ca = component & a
        cb = component & b

        # Occupied components cannot reconnect: occupied cells only disappear.
        if not ca or not cb:
            continue

        if component.bit_count() > 5:
            has_large = True
            large_a |= ca
            large_b |= cb
            continue

        g = _small_game(ca, cb)
        if g == 0:
            continue
        if g == 1:
            star ^= 1
            continue

        inverse = _GINV[g]
        bucket = pending.get(inverse)
        if bucket:
            bucket.pop()
            if not bucket:
                del pending[inverse]
        else:
            pending.setdefault(g, []).append((ca, cb))

    na, nb = large_a, large_b
    bias = 0
    games = []

    for g, components in pending.items():
        for ca, cb in components:
            na |= ca
            nb |= cb
            games.append(g)
            bias += _GBIAS[g]

    exact_games = None if has_large else tuple(sorted(games))
    result = (na, nb, star, bias, exact_games)
    _REDUCTIONS[key] = result

    inverse_games = (
        None if exact_games is None
        else tuple(sorted(_GINV[g] for g in exact_games))
    )
    _REDUCTIONS[b | (a << 30)] = (
        nb, na, star, -bias, inverse_games
    )
    return result


def _evaluate(a, b, star, bias):
    na = _adj(a)
    nb = _adj(b)
    active_a = a & nb
    active_b = b & na

    near_a = a & _adj(active_a) & ~active_a
    near_b = b & _adj(active_b) & ~active_b
    far_a = a & _adj(near_a) & ~(active_a | near_a)
    far_b = b & _adj(near_b) & ~(active_b | near_b)

    relevant_a = active_a | near_a | far_a
    relevant_b = active_b | near_b | far_b

    pairs_a = (
        (relevant_a & (relevant_a << 6)).bit_count()
        + (relevant_a & ((relevant_a & NOT_RIGHT) << 1)).bit_count()
    )
    pairs_b = (
        (relevant_b & (relevant_b << 6)).bit_count()
        + (relevant_b & ((relevant_b & NOT_RIGHT) << 1)).bit_count()
    )

    exposed_a = (active_a & ~na).bit_count()
    exposed_b = (active_b & ~nb).bit_count()

    return (
        bias
        + 12 * (active_a.bit_count() - active_b.bit_count())
        + 20 * (near_a.bit_count() - near_b.bit_count())
        + 8 * (far_a.bit_count() - far_b.bit_count())
        + 5 * (pairs_a - pairs_b)
        - 8 * (exposed_a - exposed_b)
        + (-5 if star else 5)
    )


def _local_order(a, b, s, d):
    ns = NEIGHBORS[s.bit_length() - 1]
    nd = NEIGHBORS[d.bit_length() - 1]
    return (
        8 * (a & nd).bit_count()
        + 5 * (b & nd).bit_count()
        - 6 * (a & ns).bit_count()
        + 2 * (b & ns).bit_count()
    )


class _Timeout(Exception):
    pass


class _Engine:
    def __init__(self, deadline):
        self.deadline = deadline
        self.nodes = 0
        self.history = [{}, {}]
        self.killers = [[-1, -1] for _ in range(64)]

    def check(self):
        if time.perf_counter() >= self.deadline:
            raise _Timeout

    def sum_win(self, games):
        self.nodes += 1
        if not (self.nodes & 127):
            self.check()

        if not games:
            return False
        if len(games) == 1:
            return _GLW[games[0]]

        cached = _SUM_CACHE.get(games)
        if cached is not None:
            return cached

        previous = -1
        for i, g in enumerate(games):
            if g == previous:
                continue
            previous = g

            # Swapping all component colors makes the next player "Left".
            base = [_GINV[x] for j, x in enumerate(games) if j != i]
            for option in _GL[g]:
                child = _canonical_sum(base + [_GINV[option]])
                if not self.sum_win(child):
                    _SUM_CACHE[games] = True
                    return True

        _SUM_CACHE[games] = False
        return False

    def search(self, a, b, star, depth, alpha, beta, ply):
        self.nodes += 1
        if not (self.nodes & 127):
            self.check()

        occupied = a | b
        connected = _adj(occupied)
        a &= connected
        b &= connected
        size = (a | b).bit_count()
        bias = 0

        if size <= 18:
            a, b, extra_star, bias, games = _reduce(a, b)
            star ^= extra_star
            if games is not None:
                if star:
                    games = _canonical_sum(games + (1,))
                return WIN if self.sum_win(games) else -WIN
            size = (a | b).bit_count()

        if not (a & _adj(b)):
            return WIN if star else -WIN

        key = a | (b << 30) | (star << 60)
        entry = _TT.get(key)
        preferred = -1

        if entry is not None:
            old_depth, value, bound, preferred = entry
            if old_depth >= depth:
                if bound == 0:
                    return value
                if bound == 1:
                    alpha = max(alpha, value)
                else:
                    beta = min(beta, value)
                if alpha >= beta:
                    return value

        if depth <= 0:
            value = _evaluate(a, b, star, bias)
            if entry is None or entry[0] <= 0:
                _TT[key] = (0, value, 0, -1)
            return value

        alpha_start = alpha
        hist = self.history[ply & 1]
        killer1, killer2 = self.killers[min(ply, 63)]
        ordered = []

        for s, d in _moves(a, b):
            move = s | d
            priority = _local_order(a, b, s, d) + hist.get(move, 0)
            if move == preferred:
                priority += 10000000
            elif move == killer1:
                priority += 500000
            elif move == killer2:
                priority += 400000
            ordered.append((priority, s, d, move))

        if star:
            priority = 20 + hist.get(0, 0)
            if preferred == 0:
                priority += 10000000
            elif killer1 == 0:
                priority += 500000
            elif killer2 == 0:
                priority += 400000
            ordered.append((priority, 0, 0, 0))

        ordered.sort(reverse=True)
        best = -WIN
        best_move = ordered[0][3]
        cutoff = False
        narrow = beta - alpha <= 1

        for number, (_, s, d, move) in enumerate(ordered):
            if move == 0:
                child_a, child_b, child_star = b, a, 0
            else:
                child_a = b ^ d
                child_b = a ^ s ^ d
                child_star = star

            next_depth = depth - 1
            reduction = (
                1
                if depth >= 4 and number >= 5 and size > 18
                and narrow and move != killer1 and move != killer2
                else 0
            )

            if number == 0:
                value = -self.search(
                    child_a, child_b, child_star,
                    next_depth, -beta, -alpha, ply + 1
                )
            else:
                value = -self.search(
                    child_a, child_b, child_star,
                    next_depth - reduction, -alpha - 1, -alpha, ply + 1
                )
                if reduction and value > alpha:
                    value = -self.search(
                        child_a, child_b, child_star,
                        next_depth, -alpha - 1, -alpha, ply + 1
                    )
                if alpha < value < beta:
                    value = -self.search(
                        child_a, child_b, child_star,
                        next_depth, -beta, -alpha, ply + 1
                    )

            if value > best:
                best = value
                best_move = move
            if value > alpha:
                alpha = value

            if alpha >= beta:
                cutoff = True
                hist[move] = min(
                    200000, hist.get(move, 0) + 16 * depth * depth
                )
                killers = self.killers[min(ply, 63)]
                if killers[0] != move:
                    killers[1] = killers[0]
                    killers[0] = move
                break

        if best == WIN or (best == -WIN and not cutoff):
            _TT[key] = (99, best, 0, best_move)
        else:
            bound = (
                2 if best <= alpha_start
                else 1 if best >= beta
                else 0
            )
            if entry is None or depth >= entry[0]:
                _TT[key] = (depth, best, bound, best_move)

        return best


def _read_board(board):
    result = 0
    try:
        for r in range(5):
            for c in range(6):
                if board[r][c]:
                    result |= 1 << (6 * r + c)
    except (TypeError, IndexError):
        result = 0
        for i in range(30):
            if board[i]:
                result |= 1 << i
    return result


def _format_move(s, d):
    source = s.bit_length() - 1
    destination = d.bit_length() - 1
    direction = {
        -6: "U",
        1: "R",
        6: "D",
        -1: "L",
    }[destination - source]
    return f"{source // 6},{source % 6},{direction}"


def policy(you: list[int], opponent: list[int]) -> str:
    start = time.perf_counter()
    a = _read_board(you)
    b = _read_board(opponent)
    legal = _moves(a, b)

    # Terminal states have no legal action; normally the arena never calls
    # policy after the game has ended.
    if not legal:
        return "0,0,U"

    if len(legal) == 1:
        return _format_move(*legal[0])

    ordered = sorted(
        ((_local_order(a, b, s, d), s, d) for s, d in legal),
        reverse=True,
    )
    answer = (ordered[0][1], ordered[0][2])

    # Retain useful information across calls, with bounded cache growth.
    if len(_TT) > 160000:
        _TT.clear()
    if len(_REDUCTIONS) > 70000:
        _REDUCTIONS.clear()
    if len(_SMALL) > 100000:
        _SMALL.clear()
    if len(_SUM_CACHE) > 150000:
        _SUM_CACHE.clear()

    engine = _Engine(start + 0.88)
    maximum_depth = min(30, (a | b).bit_count())

    try:
        for depth in range(1, maximum_depth + 1):
            engine.check()
            alpha = -WIN
            best_value = -WIN
            iteration_answer = answer
            scored = []

            for number, (_, s, d) in enumerate(ordered):
                engine.check()
                child_a = b ^ d
                child_b = a ^ s ^ d

                if number == 0 or depth <= 2:
                    value = -engine.search(
                        child_a, child_b, 0, depth - 1,
                        -WIN, -alpha, 1
                    )
                else:
                    value = -engine.search(
                        child_a, child_b, 0, depth - 1,
                        -alpha - 1, -alpha, 1
                    )
                    if alpha < value < WIN:
                        value = -engine.search(
                            child_a, child_b, 0, depth - 1,
                            -WIN, -alpha, 1
                        )

                scored.append((value, s, d))

                if number == 0 or value > best_value:
                    best_value = value
                    iteration_answer = (s, d)

                if value > alpha:
                    alpha = value

                # A proven winning move needs no further search.
                if value == WIN:
                    return _format_move(s, d)

            answer = iteration_answer
            ordered = sorted(scored, reverse=True)

            if best_value == -WIN:
                break

    except _Timeout:
        pass

    return _format_move(*answer)
