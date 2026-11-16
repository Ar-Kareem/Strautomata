
import time

ROWS = 5
COLS = 6
SIZE = 30
FULL = (1 << SIZE) - 1
LEFT = sum(1 << (r * COLS) for r in range(ROWS))
RIGHT = LEFT << (COLS - 1)
NOT_LEFT = FULL ^ LEFT
NOT_RIGHT = FULL ^ RIGHT

NEIGHBORS = []
for _s in range(SIZE):
    _r, _c = divmod(_s, COLS)
    _mask = 0
    if _r:
        _mask |= 1 << (_s - COLS)
    if _r + 1 < ROWS:
        _mask |= 1 << (_s + COLS)
    if _c:
        _mask |= 1 << (_s - 1)
    if _c + 1 < COLS:
        _mask |= 1 << (_s + 1)
    NEIGHBORS.append(_mask)

WIN = 100000
EXACT, LOWER, UPPER = 0, 1, 2


def _adj(x):
    return (
        (x << COLS)
        | (x >> COLS)
        | ((x & NOT_RIGHT) << 1)
        | ((x & NOT_LEFT) >> 1)
    ) & FULL


def _moves(a, b):
    result = []
    active = a & _adj(b)
    while active:
        bit = active & -active
        active ^= bit
        s = bit.bit_length() - 1
        targets = NEIGHBORS[s] & b
        while targets:
            dest = targets & -targets
            targets ^= dest
            result.append((s << 5) | (dest.bit_length() - 1))
    return result


def _after(a, b, move):
    s = move >> 5
    t = move & 31
    return b ^ (1 << t), a ^ (1 << s) ^ (1 << t)


def _format(move):
    s, t = move >> 5, move & 31
    r, c = divmod(s, COLS)
    delta = t - s
    direction = {-COLS: "U", 1: "R", COLS: "D", -1: "L"}[delta]
    return f"{r},{c},{direction}"


def _read_board(board):
    bits = 0
    if len(board) == SIZE:
        for i in range(SIZE):
            if board[i]:
                bits |= 1 << i
    else:
        for r in range(ROWS):
            for c in range(COLS):
                if board[r][c]:
                    bits |= 1 << (r * COLS + c)
    return bits


def _evaluate(a, b):
    na = _adj(a)
    nb = _adj(b)
    fa = a & nb
    fb = b & na

    occupied = a | b
    relevant = fa | fb
    relevant |= _adj(relevant) & occupied
    relevant |= _adj(relevant) & occupied

    material = (a & relevant).bit_count() - (b & relevant).bit_count()
    mobile = fa.bit_count() - fb.bit_count()
    support = (a & _adj(fa)).bit_count() - (b & _adj(fb)).bit_count()
    unsupported = (fa & ~na).bit_count() - (fb & ~nb).bit_count()

    return 14 * material + 6 * mobile + 8 * support - 4 * unsupported + 10


class _Timeout(Exception):
    pass


class _SmallSolver:
    """Exact normal-play solver, optionally with one independent * component."""

    def __init__(self, deadline):
        self.deadline = deadline
        self.memo = {}
        self.nodes = 0

    def solve(self, a, b, star=0):
        self.nodes += 1
        if (self.nodes & 63) == 0 and time.perf_counter() >= self.deadline:
            raise _Timeout

        key = a | (b << SIZE) | (star << (2 * SIZE))
        cached = self.memo.get(key)
        if cached is not None:
            return cached

        moves = _moves(a, b)
        if not moves:
            answer = bool(star)
            self.memo[key] = answer
            return answer

        if star and not self.solve(b, a, 0):
            self.memo[key] = True
            return True

        for move in moves:
            x, y = _after(a, b, move)
            if not self.solve(x, y, star):
                self.memo[key] = True
                return True

        self.memo[key] = False
        return False


def _simplify(a, b, solver):
    """Remove inert/zero components and pairs of components equal to *."""
    occupied = a | b
    components = []
    remaining = occupied

    while remaining:
        component = remaining & -remaining
        while True:
            grown = component | (_adj(component) & occupied)
            if grown == component:
                break
            component = grown
        remaining &= ~component
        components.append(component)

    keep_a = a
    keep_b = b
    pending_star = 0

    for component in components:
        ca, cb = a & component, b & component

        if not ca or not cb:
            keep_a &= ~component
            keep_b &= ~component
            continue

        if component.bit_count() > 7:
            continue

        try:
            if time.perf_counter() >= solver.deadline:
                break

            left_first = solver.solve(ca, cb)
            right_first = solver.solve(cb, ca)

            # A second-player-win partisan component is equal to zero.
            if not left_first and not right_first:
                keep_a &= ~component
                keep_b &= ~component
                continue

            # G = * precisely when G + * is a second-player win.
            if left_first and right_first:
                is_star = (
                    not solver.solve(ca, cb, 1)
                    and not solver.solve(cb, ca, 1)
                )
                if is_star:
                    if pending_star:
                        remove = pending_star | component
                        keep_a &= ~remove
                        keep_b &= ~remove
                        pending_star = 0
                    else:
                        pending_star = component
        except _Timeout:
            break

    return keep_a, keep_b


class _Search:
    def __init__(self, deadline, root_scores):
        self.deadline = deadline
        self.tt = {}
        self.history = [[0] * 1024 for _ in range(2)]
        self.killers = [[-1, -1] for _ in range(64)]
        self.nodes = 0
        self.root_scores = root_scores
        self.partial_move = None

    def search(self, a, b, depth, alpha, beta, ply=0):
        self.nodes += 1
        if (self.nodes & 127) == 0:
            if time.perf_counter() >= self.deadline:
                raise _Timeout

        original_alpha = alpha
        key = a | (b << SIZE)
        entry = self.tt.get(key)
        tt_move = -1

        if entry is not None:
            old_depth, flag, value, tt_move = entry
            if old_depth >= depth:
                if flag == EXACT:
                    if ply == 0 and tt_move >= 0:
                        self.partial_move = tt_move
                    return value
                if flag == LOWER and value >= beta:
                    return value
                if flag == UPPER and value <= alpha:
                    return value

        moves = _moves(a, b)
        count = len(moves)

        if not count:
            self.tt[key] = (64, EXACT, -WIN, -1)
            return -WIN

        # A capture can eliminate at most seven existing cross-color edges.
        # This test detects every immediate win without making child boards.
        if count <= 7:
            for move in moves:
                s, t = move >> 5, move & 31
                edges_after = (
                    count
                    - (NEIGHBORS[s] & b).bit_count()
                    - (NEIGHBORS[t] & a).bit_count()
                    + 1
                    + (NEIGHBORS[t] & b).bit_count()
                )
                if edges_after == 0:
                    self.tt[key] = (64, EXACT, WIN, move)
                    if ply == 0:
                        self.partial_move = move
                    return WIN

        # Forced lines are extended, including at the nominal horizon.
        if depth <= 0 and count > 1:
            value = _evaluate(a, b)
            self.tt[key] = (0, EXACT, value, tt_move)
            return value

        killer1, killer2 = self.killers[min(ply, 63)]
        history = self.history[ply & 1]

        if count > 1:
            def order(move):
                if move == tt_move:
                    return 1000000000
                bonus = history[move] * 8
                if move == killer1:
                    bonus += 1000000
                elif move == killer2:
                    bonus += 900000
                s, t = move >> 5, move & 31
                bonus += 16 * (
                    5 * (NEIGHBORS[t] & a).bit_count()
                    - 3 * (NEIGHBORS[s] & a).bit_count()
                    + (NEIGHBORS[s] & b).bit_count()
                    - 2 * (NEIGHBORS[t] & b).bit_count()
                )
                if ply == 0:
                    bonus += self.root_scores.get(move, 0) * 8
                return bonus

            moves.sort(key=order, reverse=True)

        child_depth = depth if count == 1 else depth - 1
        best = -WIN - 1
        best_move = moves[0]

        for index, move in enumerate(moves):
            x, y = _after(a, b, move)

            if index == 0:
                value = -self.search(
                    x, y, child_depth, -beta, -alpha, ply + 1
                )
            else:
                reduction = 0
                if (
                    ply > 0
                    and depth >= 3
                    and index >= 4
                    and count >= 6
                    and move != killer1
                    and move != killer2
                ):
                    reduction = 1
                    if depth >= 6 and index >= 10:
                        reduction = 2

                value = -self.search(
                    x, y, max(0, child_depth - reduction),
                    -alpha - 1, -alpha, ply + 1
                )

                if reduction and value > alpha:
                    value = -self.search(
                        x, y, child_depth, -alpha - 1, -alpha, ply + 1
                    )

                if alpha < value < beta:
                    value = -self.search(
                        x, y, child_depth, -beta, -alpha, ply + 1
                    )

            if value > best:
                best = value
                best_move = move
                if ply == 0:
                    self.partial_move = move

            if value > alpha:
                alpha = value

            if alpha >= beta:
                if move != killer1:
                    self.killers[min(ply, 63)] = [move, killer1]
                history[move] = min(
                    8192, history[move] + max(1, depth * depth)
                )
                break

        if best <= original_alpha:
            flag = UPPER
        elif best >= beta:
            flag = LOWER
        else:
            flag = EXACT

        self.tt[key] = (max(0, depth), flag, best, best_move)
        return best


def policy(you: list[int], opponent: list[int]) -> str:
    start = time.perf_counter()
    deadline = start + 0.91

    original_a = _read_board(you)
    original_b = _read_board(opponent)
    original_moves = _moves(original_a, original_b)

    # Terminal positions have no legal action; normal arena calls exclude them.
    if not original_moves:
        return "0,0,U"

    fallback = original_moves[0]
    if len(original_moves) == 1:
        return _format(fallback)

    # Take an immediate win before spending time on any analysis.
    for move in original_moves:
        x, y = _after(original_a, original_b, move)
        if not (x & _adj(y)):
            return _format(move)

    small = _SmallSolver(min(deadline, start + 0.10))
    a, b = _simplify(original_a, original_b, small)

    if not (a & _adj(b)):
        return _format(fallback)

    moves = _moves(a, b)
    if len(moves) == 1:
        return _format(moves[0])

    root_scores = {}
    for move in moves:
        x, y = _after(a, b, move)
        if not (x & _adj(y)):
            return _format(move)
        root_scores[move] = -_evaluate(x, y)

    moves.sort(key=lambda m: root_scores[m], reverse=True)
    best_move = moves[0]

    # Small endgames are usually cheaper to solve directly than to deepen.
    if (a | b).bit_count() <= 12:
        small.deadline = min(deadline, start + 0.25)
        try:
            for move in moves:
                if time.perf_counter() >= small.deadline:
                    raise _Timeout
                x, y = _after(a, b, move)
                if not small.solve(x, y):
                    return _format(move)
            # Every move was proved losing; prefer the positional fallback.
            return _format(best_move)
        except _Timeout:
            pass

    engine = _Search(deadline, root_scores)
    root_key = a | (b << SIZE)
    engine.tt[root_key] = (-1, EXACT, 0, best_move)

    for depth in range(1, 32):
        if time.perf_counter() >= deadline:
            break
        engine.partial_move = None

        try:
            value = engine.search(a, b, depth, -WIN - 1, WIN + 1)
            entry = engine.tt.get(root_key)
            if entry is not None and entry[3] >= 0:
                best_move = entry[3]
            if abs(value) == WIN:
                break
        except _Timeout:
            if engine.partial_move is not None:
                best_move = engine.partial_move
            break

    # Reduction only removes entire disconnected components, so every searched
    # move remains legal on the original board. Check nonetheless as a safeguard.
    if best_move not in original_moves:
        best_move = fallback
    return _format(best_move)
