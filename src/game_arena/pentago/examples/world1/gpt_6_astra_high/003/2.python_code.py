
import time

_FULL = (1 << 36) - 1
_MATE = 10_000_000
_INF = 100_000_000
_WEIGHTS = (0, 2, 18, 110, 800, _MATE)


def _index(r, c):
    return ((r // 3) * 2 + c // 3) * 9 + (r % 3) * 3 + c % 3


# Each quadrant occupies nine consecutive bits.
_ROT_LUT = []
_ROT_MAP = []
_KEEP = []
_SHIFT = []

for t in range(8):
    q, direction = divmod(t, 2)  # 0 = L, 1 = R
    shift = 9 * q
    local_map = []
    for i in range(9):
        r, c = divmod(i, 3)
        if direction == 0:
            nr, nc = 2 - c, r
        else:
            nr, nc = c, 2 - r
        local_map.append(3 * nr + nc)

    table = []
    for pattern in range(512):
        rotated = 0
        for i in range(9):
            if pattern & (1 << i):
                rotated |= 1 << local_map[i]
        table.append(rotated << shift)

    mapping = list(range(36))
    for i in range(9):
        mapping[shift + i] = shift + local_map[i]

    _ROT_LUT.append(tuple(table))
    _ROT_MAP.append(tuple(mapping))
    _KEEP.append(_FULL ^ (511 << shift))
    _SHIFT.append(shift)


def _rotate(board, t):
    return ((board & _KEEP[t]) |
            _ROT_LUT[t][(board >> _SHIFT[t]) & 511])


_LINES = []
for r in range(6):
    for c in range(6):
        for dr, dc in ((0, 1), (1, 0), (1, 1), (1, -1)):
            er, ec = r + 4 * dr, c + 4 * dc
            if 0 <= er < 6 and 0 <= ec < 6:
                mask = 0
                for k in range(5):
                    mask |= 1 << _index(r + k * dr, c + k * dc)
                _LINES.append(mask)
_LINES = tuple(_LINES)

# A rotated winning line can instead be tested in the original coordinates.
_INV_LINES = tuple(
    tuple(_rotate(mask, t ^ 1) for mask in _LINES)
    for t in range(8)
)

_pattern_rotations = {}
for t, lines in enumerate(_INV_LINES):
    for mask in lines:
        _pattern_rotations.setdefault(mask, []).append(t)

_PATTERNS = tuple(
    (mask, tuple(rotations))
    for mask, rotations in sorted(
        _pattern_rotations.items(),
        key=lambda item: -len(item[1])
    )
)

_centers = sum(1 << (9 * q + 4) for q in range(4))
_inner = sum(1 << _index(r, c)
             for r in range(1, 5) for c in range(1, 5))
_middle = sum(1 << _index(r, c)
              for r in (2, 3) for c in (2, 3))
_POSITION_MASKS = ((_centers, 5), (_inner, 1), (_middle, 2))
_POSITION = [
    sum(weight for mask, weight in _POSITION_MASKS if mask & (1 << i))
    for i in range(36)
]

# Action codes use the ORIGINAL placement square.
_MOVE_TEXT = [""] * 512
for t in range(8):
    q, direction = divmod(t, 2)
    for i in range(36):
        square_q, local = divmod(i, 9)
        r = (square_q // 2) * 3 + local // 3 + 1
        c = (square_q % 2) * 3 + local % 3 + 1
        _MOVE_TEXT[(t << 6) | i] = (
            f"{r},{c},{q},{'L' if direction == 0 else 'R'}"
        )


class _Timeout(Exception):
    pass


class _Engine:
    def __init__(self, deadline, fallback):
        self.deadline = deadline
        self.best = fallback
        self.win_cache = {}
        self.tt = {}

    def check_time(self):
        if time.perf_counter() >= self.deadline:
            raise _Timeout

    def winning_move(self, a, b):
        """An exclusive winning action, or -1. Simultaneous wins are excluded."""
        if a.bit_count() < 4:
            return -1

        key = (a, b)
        cached = self.win_cache.get(key)
        if cached is not None:
            return cached

        absent = _FULL ^ a
        empty = _FULL ^ (a | b)
        opponent_can_have_five = b.bit_count() >= 5
        bad_rotations = 0

        for mask, rotations in _PATTERNS:
            missing = mask & absent
            if missing & (missing - 1):
                continue
            if missing & b:
                continue

            # Zero missing squares means rotation alone completes the line.
            square = missing if missing else (empty & -empty)
            if not square:
                continue

            for t in rotations:
                flag = 1 << t
                if bad_rotations & flag:
                    continue

                if opponent_can_have_five:
                    opponent_wins = False
                    for line in _INV_LINES[t]:
                        if (b & line) == line:
                            opponent_wins = True
                            break
                    if opponent_wins:
                        bad_rotations |= flag
                        continue

                action = (t << 6) | (square.bit_length() - 1)
                self.win_cache[key] = action
                return action

        self.win_cache[key] = -1
        return -1

    def generate(self, a, b, preferred=-1):
        """
        Produce ordered unique outcomes.
        Tuple: (static score, mover board, other board, action, terminal).
        Terminal: 0 ongoing, 1 mover wins, 2 draw.
        Immediately losing rotations are omitted.
        """
        moves = []
        seen = set()
        draw_added = False

        for t in range(8):
            self.check_time()
            ra = _rotate(a, t)
            rb = _rotate(b, t)
            empty = _FULL ^ (ra | rb)

            base = 0
            for mask, weight in _POSITION_MASKS:
                base += weight * (
                    (ra & mask).bit_count() - (rb & mask).bit_count()
                )

            gains = _POSITION.copy()
            already_won = False
            opponent_won = False
            winning_squares = 0

            # Evaluate a rotated board once, then calculate the incremental
            # value of placement at every empty square.
            for line in _LINES:
                ours = ra & line
                theirs = rb & line

                if not theirs:
                    count = ours.bit_count()
                    base += _WEIGHTS[count]
                    if count == 5:
                        already_won = True
                        continue
                    if count == 4:
                        winning_squares |= line & empty
                    increment = _WEIGHTS[count + 1] - _WEIGHTS[count]
                elif not ours:
                    count = theirs.bit_count()
                    base -= _WEIGHTS[count]
                    if count == 5:
                        opponent_won = True
                    increment = _WEIGHTS[count]
                else:
                    continue

                remaining = line & empty
                while remaining:
                    bit = remaining & -remaining
                    gains[bit.bit_length() - 1] += increment
                    remaining ^= bit

            fills_board = not (empty & (empty - 1))
            remaining = empty
            while remaining:
                bit = remaining & -remaining
                remaining ^= bit
                won = already_won or bool(winning_squares & bit)

                if opponent_won:
                    if not won:
                        continue
                    terminal = 2
                elif won:
                    terminal = 1
                elif fills_board:
                    terminal = 2
                else:
                    terminal = 0

                if terminal == 2 and draw_added:
                    continue

                na = ra | bit
                state = (na, rb)
                if state in seen:
                    continue
                seen.add(state)

                final_i = bit.bit_length() - 1
                original_i = _ROT_MAP[t ^ 1][final_i]
                action = (t << 6) | original_i

                if terminal == 1:
                    score = _MATE
                elif terminal == 2:
                    score = 0
                    draw_added = True
                else:
                    score = base + gains[final_i]

                moves.append((score, na, rb, action, terminal))

        moves.sort(reverse=True)
        if preferred >= 0:
            for i, move in enumerate(moves):
                if move[3] == preferred:
                    if i:
                        moves.insert(0, moves.pop(i))
                    break
        return moves

    def search(self, a, b, depth, alpha, beta, ply, static_score):
        self.check_time()

        if self.winning_move(a, b) >= 0:
            return _MATE - ply

        if depth <= 0:
            return static_score

        key = (a, b)
        entry = self.tt.get(key)
        preferred = -1
        if entry is not None:
            old_depth, value, flag, preferred = entry
            if old_depth >= depth:
                if flag == 0:
                    return value
                if flag == 1:
                    beta = min(beta, value)
                else:
                    alpha = max(alpha, value)
                if alpha >= beta:
                    return value

        original_alpha = alpha
        original_beta = beta
        moves = self.generate(a, b, preferred)

        if not moves:
            return -_MATE + ply + 1

        width = 12 if depth == 1 else (10 if depth == 2 else 8)
        if (a | b).bit_count() >= 28:
            width += 6

        best_value = -_INF
        best_action = moves[0][3]
        safe_examined = 0

        for score, na, nb, action, terminal in moves:
            if terminal == 1:
                value = _MATE - ply
            elif terminal == 2:
                value = 0
            else:
                value = -self.search(
                    nb, na, depth - 1, -beta, -alpha,
                    ply + 1, -score
                )

            if value > best_value:
                best_value = value
                best_action = action
            if value > alpha:
                alpha = value
            if alpha >= beta:
                break

            # Losing tactical moves do not consume the beam. Thus a sole
            # immediate defense can be found even if its static rank is low.
            if value > -_MATE // 2:
                safe_examined += 1
                if safe_examined >= width:
                    break

        if best_value <= original_alpha:
            flag = 1  # upper bound
        elif best_value >= original_beta:
            flag = 2  # lower bound
        else:
            flag = 0

        self.tt[key] = (depth, best_value, flag, best_action)
        return best_value

    def choose(self, a, b):
        winning = self.winning_move(a, b)
        if winning >= 0:
            self.best = _MOVE_TEXT[winning]
            return self.best

        moves = self.generate(a, b)
        if not moves:
            return self.best

        self.best = _MOVE_TEXT[moves[0][3]]

        # Exact root safety filtering, without a heuristic beam.
        safe = []
        for move in moves:
            self.check_time()
            score, na, nb, action, terminal = move
            if terminal == 1:
                self.best = _MOVE_TEXT[action]
                return self.best
            if terminal == 2 or self.winning_move(nb, na) < 0:
                safe.append(move)
                if len(safe) == 1:
                    self.best = _MOVE_TEXT[action]

        if not safe:
            return self.best
        if len(safe) == 1:
            self.best = _MOVE_TEXT[safe[0][3]]
            return self.best

        ranked = [(move[0], move) for move in safe]
        incumbent = safe[0][3]

        # First examine every safe root move. Later iterations concentrate
        # search on the strongest candidates from the previous iteration.
        for depth in range(2, 13):
            self.check_time()
            ranked.sort(key=lambda item: item[0], reverse=True)

            if depth == 2:
                limit = len(ranked)
            elif depth == 3:
                limit = 28
            elif depth == 4:
                limit = 16
            else:
                limit = 12

            selected = ranked[:limit]
            for i, item in enumerate(selected):
                if item[1][3] == incumbent:
                    selected.insert(0, selected.pop(i))
                    break

            next_ranked = []
            alpha = -_INF
            iteration_best = -_INF

            for _, move in selected:
                self.check_time()
                score, na, nb, action, terminal = move

                if terminal == 2:
                    value = 0
                elif terminal == 1:
                    value = _MATE
                else:
                    value = -self.search(
                        nb, na, depth - 1,
                        -_INF, -alpha, 1, -score
                    )

                next_ranked.append((value, move))
                if value > iteration_best:
                    iteration_best = value
                    incumbent = action
                    self.best = _MOVE_TEXT[action]
                if value > alpha:
                    alpha = value

                if value > _MATE // 2:
                    return self.best

            ranked = next_ranked
            if iteration_best < -_MATE // 2:
                break

        return self.best


def policy(you, opponent) -> str:
    started = time.perf_counter()
    a = 0
    b = 0

    for r in range(6):
        for c in range(6):
            bit = 1 << _index(r, c)
            if you[r][c]:
                a |= bit
            elif opponent[r][c]:
                b |= bit

    empty = _FULL ^ (a | b)
    first_empty = (empty & -empty).bit_length() - 1
    fallback = _MOVE_TEXT[(1 << 6) | first_empty]

    if not (a | b):
        return "2,2,0,R"

    engine = _Engine(started + 0.89, fallback)
    try:
        return engine.choose(a, b)
    except _Timeout:
        return engine.best
