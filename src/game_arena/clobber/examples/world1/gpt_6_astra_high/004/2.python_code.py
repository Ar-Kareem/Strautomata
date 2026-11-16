
import time

ROWS = 5
COLS = 6
FULL = (1 << 30) - 1
COL0 = sum(1 << (6 * r) for r in range(5))
COL5 = COL0 << 5
NOT_LEFT = FULL ^ COL0
NOT_RIGHT = FULL ^ COL5

WIN = 100000
INF = 200000

NEIGHBORS = []
for _s in range(30):
    _r, _c = divmod(_s, 6)
    _n = 0
    if _r:
        _n |= 1 << (_s - 6)
    if _c < 5:
        _n |= 1 << (_s + 1)
    if _r < 4:
        _n |= 1 << (_s + 6)
    if _c:
        _n |= 1 << (_s - 1)
    NEIGHBORS.append(_n)


def _adj(x):
    return (((x << 6) | (x >> 6) |
             ((x & NOT_LEFT) >> 1) |
             ((x & NOT_RIGHT) << 1)) & FULL)


def _strip(a, b):
    touching = _adj(a | b)
    return a & touching, b & touching


def _moves(a, b):
    result = []
    for origins, delta in (
        (a & (b << 6), -6),
        (a & (b >> 1) & NOT_RIGHT, 1),
        (a & (b >> 6), 6),
        (a & (b << 1) & NOT_LEFT, -1),
    ):
        while origins:
            f = origins & -origins
            origins -= f
            s = f.bit_length() - 1
            d = s + delta
            result.append((f, 1 << d, (s << 5) | d))
    return result


def _format_move(code):
    s, d = code >> 5, code & 31
    direction = {-6: "U", 1: "R", 6: "D", -1: "L"}[d - s]
    return f"{s // 6},{s % 6},{direction}"


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


class _Timeout(Exception):
    pass


class _Search:
    def __init__(self, a, b, legal):
        self.a = a
        self.b = b
        self.legal = legal
        self.deadline = time.perf_counter() + 0.90
        self.nodes = 0

        self.tt = {}
        self.local_cache = {}
        self.component_cache = {}
        self.reduction_cache = {}

        self.history = [0] * 1024
        self.killers = [[-1, -1] for _ in range(40)]
        self.best = legal[0][2]
        self.current = self.best

    def tick(self):
        self.nodes += 1
        if not (self.nodes & 127):
            if time.perf_counter() >= self.deadline:
                raise _Timeout

    def local_win(self, a, b, star=0):
        """Exact normal-play solution, optionally with one independent star."""
        self.tick()
        a, b = _strip(a, b)
        key = (a << 31) | (b << 1) | star
        cached = self.local_cache.get(key)
        if cached is not None:
            return cached

        if not (a & _adj(b)):
            answer = bool(star)
            self.local_cache[key] = answer
            return answer

        # Moving in the independent star is a one-time pass.
        if star and not self.local_win(b, a, 0):
            self.local_cache[key] = True
            return True

        for f, t, code in _moves(a, b):
            if not self.local_win(b ^ t, a ^ f ^ t, star):
                self.local_cache[key] = True
                return True

        self.local_cache[key] = False
        return False

    def component_info(self, a, b):
        """
        kind: 0=zero, 1=star, 2=positive, -2=negative, 3=fuzzy.
        Also supplies a heuristic infinitesimal weight and star parity.
        """
        key = (a << 30) | b
        cached = self.component_cache.get(key)
        if cached is not None:
            return cached

        left = self.local_win(a, b)
        right = self.local_win(b, a)

        if not left and not right:
            result = (0, 0, 0)
        else:
            left_star = self.local_win(a, b, 1)
            right_star = self.local_win(b, a, 1)

            if left and not right:
                result = (2, 240 if not right_star else 140, 0)
            elif right and not left:
                result = (-2, -240 if not left_star else -140, 0)
            elif not left_star and not right_star:
                result = (1, 0, 1)
            elif left_star and not right_star:
                result = (3, 140, 1)
            elif right_star and not left_star:
                result = (3, -140, 1)
            else:
                result = (3, 0, 1)

        self.component_cache[key] = result
        return result

    @staticmethod
    def quick_eval(a, b):
        aa = _adj(a)
        bb = _adj(b)
        material = a.bit_count() - b.bit_count()
        active = (a & bb).bit_count() - (b & aa).bit_count()
        supported = (a & aa).bit_count() - (b & bb).bit_count()
        return 26 * material + 9 * active + 4 * supported

    def reduce_position(self, a, b):
        """
        Remove monochromatic/zero components and cancel pairs of stars.
        Return reduced boards, an exact outcome if available, and an estimate.
        """
        key = (a << 30) | b
        cached = self.reduction_cache.get(key)
        if cached is not None:
            return cached

        remaining = a | b
        ra = rb = 0
        stars = []
        kinds = []
        estimate = 0
        parity = 0

        while remaining:
            component = remaining & -remaining
            frontier = component
            while frontier:
                frontier = _adj(frontier) & remaining & ~component
                component |= frontier
            remaining &= ~component

            ca, cb = a & component, b & component
            if not ca or not cb:
                continue

            if component.bit_count() <= 6:
                kind, value, nim = self.component_info(ca, cb)
                if kind == 0:
                    continue
                if kind == 1:
                    stars.append((ca, cb))
                    continue
                kinds.append(kind)
                estimate += value
                parity ^= nim
            else:
                kinds.append(4)
                estimate += self.quick_eval(ca, cb)

            ra |= ca
            rb |= cb

        if len(stars) & 1:
            ca, cb = stars[0]
            ra |= ca
            rb |= cb
            kinds.append(1)
            parity ^= 1

        exact = 0
        if not kinds:
            exact = -1
        elif len(kinds) == 1 and kinds[0] != 4:
            exact = -1 if kinds[0] == -2 else 1
        elif all(k == 2 for k in kinds):
            exact = 1
        elif all(k == -2 for k in kinds):
            exact = -1

        if kinds:
            estimate += 12 if parity else -12

        result = (ra, rb, exact, estimate)
        self.reduction_cache[key] = result
        return result

    def move_bias(self, a, b, code):
        s, d = code >> 5, code & 31
        ns, nd = NEIGHBORS[s], NEIGHBORS[d]
        return (
            7 * (nd & a).bit_count()
            - 4 * (ns & a).bit_count()
            + 3 * (ns & b).bit_count()
            - 2 * (nd & b).bit_count()
        )

    def ordered_moves(self, a, b, moves, tt_move, ply):
        k0, k1 = self.killers[min(ply, 39)]

        def priority(move):
            code = move[2]
            if code == tt_move:
                return 10000000
            value = self.history[code] + self.move_bias(a, b, code)
            if code == k0:
                value += 1000000
            elif code == k1:
                value += 900000
            return value

        moves.sort(key=priority, reverse=True)
        return moves

    def search(self, a, b, depth, alpha, beta, ply):
        self.tick()
        a, b = _strip(a, b)

        if not (a & _adj(b)):
            return -WIN + ply

        count = (a | b).bit_count()
        if count <= 8:
            return (WIN - ply) if self.local_win(a, b) else (-WIN + ply)

        estimate = None
        if count <= 18:
            a, b, exact, estimate = self.reduce_position(a, b)
            if exact:
                return (WIN - ply) if exact > 0 else (-WIN + ply)
            count = (a | b).bit_count()
            if count <= 8:
                return (WIN - ply) if self.local_win(a, b) else (-WIN + ply)

        key = (a << 30) | b
        entry = self.tt.get(key)
        tt_move = -1
        if entry is not None:
            old_depth, flag, value, tt_move = entry
            if old_depth >= depth:
                if flag == 0:
                    return value
                if flag == 1 and value >= beta:
                    return value
                if flag == 2 and value <= alpha:
                    return value

        moves = _moves(a, b)
        if not moves:
            return -WIN + ply

        if depth <= 0:
            # A forced capture is searched rather than evaluated.
            if len(moves) == 1:
                depth = 1
            else:
                if estimate is None:
                    estimate = self.quick_eval(a, b)
                return estimate

        self.ordered_moves(a, b, moves, tt_move, ply)
        original_alpha = alpha
        best_value = -INF
        best_move = moves[0][2]
        k0, k1 = self.killers[min(ply, 39)]

        for index, (f, t, code) in enumerate(moves):
            child_a = b ^ t
            child_b = a ^ f ^ t

            if index == 0:
                value = -self.search(
                    child_a, child_b, depth - 1, -beta, -alpha, ply + 1
                )
            else:
                reduction = (
                    1 if depth >= 4 and index >= 5 and count > 14
                    and code != k0 and code != k1 else 0
                )
                value = -self.search(
                    child_a, child_b, depth - 1 - reduction,
                    -alpha - 1, -alpha, ply + 1
                )
                if reduction and value > alpha:
                    value = -self.search(
                        child_a, child_b, depth - 1,
                        -alpha - 1, -alpha, ply + 1
                    )
                if alpha < value < beta:
                    value = -self.search(
                        child_a, child_b, depth - 1,
                        -beta, -alpha, ply + 1
                    )

            if value > best_value:
                best_value = value
                best_move = code
            if value > alpha:
                alpha = value

            if alpha >= beta:
                self.history[code] = min(
                    200000, self.history[code] + depth * depth * 8
                )
                killers = self.killers[min(ply, 39)]
                if killers[0] != code:
                    killers[1] = killers[0]
                    killers[0] = code
                break

        if best_value <= original_alpha:
            flag = 2
        elif best_value >= beta:
            flag = 1
        else:
            flag = 0

        stored_depth = 99 if flag == 0 and abs(best_value) > WIN - 100 else depth
        self.tt[key] = (stored_depth, flag, best_value, best_move)
        return best_value

    def run(self):
        a, b = self.a, self.b
        ordered = list(self.legal)
        ordered.sort(
            key=lambda m: self.move_bias(a, b, m[2]), reverse=True
        )
        self.best = ordered[0][2]
        self.current = self.best

        try:
            for depth in range(1, 31):
                if time.perf_counter() >= self.deadline:
                    break

                ordered.sort(key=lambda m: m[2] != self.best)
                alpha = -INF
                best_value = -INF
                iteration_best = ordered[0][2]
                scores = {}

                for index, (f, t, code) in enumerate(ordered):
                    if time.perf_counter() >= self.deadline:
                        raise _Timeout

                    child_a = b ^ t
                    child_b = a ^ f ^ t
                    if index == 0:
                        value = -self.search(
                            child_a, child_b, depth - 1,
                            -INF, INF, 1
                        )
                    else:
                        value = -self.search(
                            child_a, child_b, depth - 1,
                            -alpha - 1, -alpha, 1
                        )
                        if value > alpha:
                            value = -self.search(
                                child_a, child_b, depth - 1,
                                -INF, -alpha, 1
                            )

                    scores[code] = value
                    if value > best_value:
                        best_value = value
                        iteration_best = code
                        self.current = code
                    if value > alpha:
                        alpha = value

                    if value > WIN - 100:
                        self.best = code
                        return code

                self.best = iteration_best
                self.current = self.best
                ordered.sort(
                    key=lambda m: scores.get(m[2], -INF), reverse=True
                )

                if abs(best_value) > WIN - 100:
                    break

        except _Timeout:
            self.best = self.current

        return self.best


def policy(you: list[int], opponent: list[int]) -> str:
    a = _read_board(you)
    b = _read_board(opponent)
    legal = _moves(a, b)

    # No legal action exists in a terminal position.
    if not legal:
        return "0,0,U"

    if len(legal) == 1:
        return _format_move(legal[0][2])

    searcher = _Search(a, b, legal)
    chosen = searcher.run()

    # Keep the API output tied to an actual move from the original board.
    legal_codes = {move[2] for move in legal}
    if chosen not in legal_codes:
        chosen = legal[0][2]
    return _format_move(chosen)
