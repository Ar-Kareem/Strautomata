
from itertools import permutations, product
from time import perf_counter

_SIZE = 27
_FULL = (1 << _SIZE) - 1
_MATE = 100000
_INF = 1000000
_COORDS = tuple(
    (i, j, k)
    for i in range(3)
    for j in range(3)
    for k in range(3)
)


def _build_geometry():
    lines = set()

    for direction in product((-1, 0, 1), repeat=3):
        if direction == (0, 0, 0):
            continue
        if next(x for x in direction if x) < 0:
            continue

        for start in _COORDS:
            end = tuple(start[d] + 2 * direction[d] for d in range(3))
            if not all(0 <= x < 3 for x in end):
                continue

            mask = 0
            for step in range(3):
                p = tuple(start[d] + step * direction[d] for d in range(3))
                mask |= 1 << (9 * p[0] + 3 * p[1] + p[2])
            lines.add(mask)

    lines = tuple(sorted(lines))
    through = tuple(
        tuple(line for line in lines if line & (1 << index))
        for index in range(_SIZE)
    )

    symmetries = []
    for perm in permutations(range(3)):
        for flips in product((False, True), repeat=3):
            mapping = []
            for point in _COORDS:
                q = [
                    2 - point[perm[d]] if flips[d] else point[perm[d]]
                    for d in range(3)
                ]
                mapping.append(1 << (9 * q[0] + 3 * q[1] + q[2]))
            symmetries.append(tuple(mapping))

    return lines, through, tuple(symmetries)


_LINES, _THROUGH, _SYMMETRIES = _build_geometry()
_WEIGHTS = tuple(len(lines) for lines in _THROUGH)


def _pick(mask):
    """Choose a geometrically useful cell from a nonempty bit mask."""
    best = 0
    best_weight = -1
    while mask:
        bit = mask & -mask
        mask ^= bit
        weight = _WEIGHTS[bit.bit_length() - 1]
        if weight > best_weight:
            best_weight = weight
            best = bit
    return best


def _transform(mask, mapping):
    result = 0
    while mask:
        bit = mask & -mask
        mask ^= bit
        result |= mapping[bit.bit_length() - 1]
    return result


def _analyse(mine, other):
    wins = blocks = 0
    forks = enemy_forks = 0
    forces = enemy_forces = 0
    score = 0
    enemy_pairs = []

    for line in _LINES:
        a = line & mine
        b = line & other

        if a and b:
            continue

        if a:
            empty = line ^ a
            if not (empty & (empty - 1)):
                wins |= empty
            else:
                forks |= forces & empty
                forces |= empty
                score += 20

        elif b:
            empty = line ^ b
            if not (empty & (empty - 1)):
                blocks |= empty
            else:
                enemy_forks |= enemy_forces & empty
                enemy_forces |= empty
                enemy_pairs.append(empty)
                score -= 20

    score += 4 * (forces.bit_count() - enemy_forces.bit_count())
    score -= 60 * enemy_forks.bit_count()
    score += 8  # Small initiative bonus.

    return (
        wins, blocks, forks, enemy_forks,
        forces, enemy_forces, score, tuple(enemy_pairs)
    )


def _fork_defenses(empty, forks, pairs):
    """
    Quiet moves that eliminate every opposing fork.

    A fork supported by two lines can be stopped at its intersection
    or at either remaining endpoint. Three or more supporting lines
    require occupying the intersection itself.
    """
    defenses = empty

    while forks and defenses:
        bit = forks & -forks
        forks ^= bit
        count = 0
        stops = bit

        for pair in pairs:
            if pair & bit:
                count += 1
                stops |= pair
                if count == 3:
                    stops = bit
                    break

        defenses &= stops

    return defenses


class _Timeout(Exception):
    pass


class _Search:
    def __init__(self, deadline):
        self.deadline = deadline
        self.nodes = 0
        self.tt = {}
        self.analysis_cache = {}
        self.history = [[0] * _SIZE for _ in range(2)]
        self.killers = [(0, 0) for _ in range(28)]
        self.root_move = 0
        self.root_score = -_INF

    def _terminal(self, key, value, move, ply):
        self.tt[key] = (99, value, 0, move)
        if ply == 0 and move:
            self.root_move = move
            self.root_score = value
        return value

    @staticmethod
    def _child_symmetries(symmetries, move):
        if len(symmetries) <= 1:
            return symmetries
        index = move.bit_length() - 1
        return tuple(s for s in symmetries if s[index] == move)

    def ordered_moves(self, mine, other, moves, info, preferred, ply):
        forces = info[4]
        enemy_forces = info[5]
        enemy_forks = info[3]
        history = self.history[ply & 1]
        killer1, killer2 = self.killers[ply]
        ranked = []

        while moves:
            move = moves & -moves
            moves ^= move
            index = move.bit_length() - 1

            if move == preferred:
                ranked.append((10000000, move))
                continue

            value = 8 * _WEIGHTS[index] + (history[index] >> 2)

            if move & forces:
                value += 4000
            if move & enemy_forces:
                value += 250
            if move & enemy_forks:
                value += 1400
            if move == killer1:
                value += 800
            elif move == killer2:
                value += 500

            for line in _THROUGH[index]:
                a = line & mine
                b = line & other

                if not b:
                    if a:
                        value += 100
                    else:
                        value += 32
                        # New single-piece lines can intersect existing
                        # ones to create future forks.
                        value += 90 * ((line ^ move) & forces).bit_count()
                elif not a:
                    value += 45

            ranked.append((value, move))

        ranked.sort(reverse=True)
        return [move for _, move in ranked]

    def search(self, mine, other, depth, alpha, beta, ply, symmetries):
        self.nodes += 1
        if (self.nodes & 63) == 0 and perf_counter() >= self.deadline:
            raise _Timeout

        key = mine | (other << _SIZE)
        entry = self.tt.get(key)
        preferred = 0

        if entry is not None:
            old_depth, old_value, flag, preferred = entry
            if old_depth >= depth:
                if (
                    flag == 0
                    or (flag == 1 and old_value >= beta)
                    or (flag == -1 and old_value <= alpha)
                ):
                    if ply == 0 and preferred:
                        self.root_move = preferred
                        self.root_score = old_value
                    return old_value

        empty = _FULL ^ (mine | other)
        if not empty:
            return self._terminal(key, 0, 0, ply)

        info = self.analysis_cache.get(key)
        if info is None:
            info = _analyse(mine, other)
            self.analysis_cache[key] = info

        wins, blocks, forks, enemy_forks, forces, _, static, pairs = info

        if wins:
            return self._terminal(
                key, _MATE - ply - 1, _pick(wins), ply
            )

        if blocks & (blocks - 1):
            return self._terminal(
                key, -_MATE + ply + 2, _pick(blocks), ply
            )

        original_alpha = alpha

        if blocks:
            move = blocks
            if forks & move:
                return self._terminal(
                    key, _MATE - ply - 3, move, ply
                )

            child_symmetries = self._child_symmetries(symmetries, move)

            # Forced blocks do not consume decision depth.
            value = -self.search(
                other, mine | move, depth,
                -beta, -alpha, ply + 1, child_symmetries
            )

            flag = -1 if value <= original_alpha else (
                1 if value >= beta else 0
            )
            self.tt[key] = (depth, value, flag, move)

            if ply == 0:
                self.root_move = move
                self.root_score = value
            return value

        if forks:
            return self._terminal(
                key, _MATE - ply - 3, _pick(forks), ply
            )

        if not (empty & (empty - 1)):
            return self._terminal(key, 0, empty, ply)

        moves = empty

        if enemy_forks:
            defenses = _fork_defenses(empty, enemy_forks, pairs)

            # A forcing threat may also defend by denying the opponent
            # time to play a fork.
            moves &= defenses | forces

            if not moves:
                move = self.root_move if ply == 0 else _pick(empty)
                return self._terminal(
                    key, -_MATE + ply + 4, move, ply
                )

        # Extend tactically unstable fork-defense positions, but cap
        # their extra branching. Ordinary forced blocks remain extended.
        if depth <= 0 and (not enemy_forks or depth <= -4):
            self.tt[key] = (depth, static, 0, preferred)
            return static

        ordered = self.ordered_moves(
            mine, other, moves, info, preferred, ply
        )

        best_value = -_INF
        best_move = ordered[0]
        seen = 0
        use_symmetry = len(symmetries) > 1

        for move in ordered:
            if use_symmetry:
                if seen & move:
                    continue
                index = move.bit_length() - 1
                for symmetry in symmetries:
                    seen |= symmetry[index]

            child_symmetries = self._child_symmetries(symmetries, move)
            value = -self.search(
                other, mine | move, depth - 1,
                -beta, -alpha, ply + 1, child_symmetries
            )

            if value > best_value:
                best_value = value
                best_move = move
                if ply == 0:
                    self.root_move = move
                    self.root_score = value

            if value > alpha:
                alpha = value

            if alpha >= beta:
                index = move.bit_length() - 1
                bonus = 8 * max(1, depth) ** 2
                h = self.history[ply & 1]
                h[index] = min(2048, h[index] + bonus)

                first, second = self.killers[ply]
                if move != first:
                    self.killers[ply] = (move, first)
                break

        flag = -1 if best_value <= original_alpha else (
            1 if best_value >= beta else 0
        )
        self.tt[key] = (depth, best_value, flag, best_move)
        return best_value


def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    start = perf_counter()
    mine = 0
    other = 0

    for index, (i, j, k) in enumerate(_COORDS):
        value = board[i][j][k]
        if value == 1:
            mine |= 1 << index
        elif value == -1:
            other |= 1 << index

    empty = _FULL ^ (mine | other)

    # A full board has no legal action; normal arena calls are nonterminal.
    if not empty:
        return (0, 0, 0)

    fallback = _pick(empty)

    if not (mine | other):
        return (1, 1, 1)

    # Remain well-defined if a terminal position with empty cells is supplied.
    for line in _LINES:
        if (mine & line) == line or (other & line) == line:
            return _COORDS[fallback.bit_length() - 1]

    info = _analyse(mine, other)
    wins, blocks, forks = info[:3]

    if wins:
        return _COORDS[_pick(wins).bit_length() - 1]

    if blocks:
        if not (blocks & (blocks - 1)):
            return _COORDS[blocks.bit_length() - 1]

        # Unavoidable loss against perfect play: block the cell supporting
        # the greatest number of immediate winning lines.
        candidates = []
        remaining = blocks
        while remaining:
            move = remaining & -remaining
            remaining ^= move
            index = move.bit_length() - 1
            covered = sum(
                1
                for line in _THROUGH[index]
                if not (line & mine) and (line & other).bit_count() == 2
            )
            candidates.append((covered, _WEIGHTS[index], move))

        move = max(candidates)[2]
        return _COORDS[move.bit_length() - 1]

    if forks:
        return _COORDS[_pick(forks).bit_length() - 1]

    if not (empty & (empty - 1)):
        return _COORDS[empty.bit_length() - 1]

    searcher = _Search(start + 0.90)
    key = mine | (other << _SIZE)
    searcher.analysis_cache[key] = info

    initial_moves = searcher.ordered_moves(
        mine, other, empty, info, 0, 0
    )
    best_move = initial_moves[0]
    searcher.root_move = best_move

    symmetries = tuple(
        symmetry
        for symmetry in _SYMMETRIES
        if _transform(mine, symmetry) == mine
        and _transform(other, symmetry) == other
    )

    completed = False

    for depth in range(1, empty.bit_count() + 1):
        if perf_counter() >= searcher.deadline:
            break

        searcher.root_score = -_INF

        try:
            score = searcher.search(
                mine, other, depth, -_INF, _INF, 0, symmetries
            )
        except _Timeout:
            if not completed or searcher.root_score > _MATE // 2:
                if searcher.root_move & empty:
                    best_move = searcher.root_move
            break

        if searcher.root_move & empty:
            best_move = searcher.root_move
        completed = True

        if abs(score) > _MATE // 2:
            break

    if not (best_move & empty):
        best_move = fallback

    return _COORDS[best_move.bit_length() - 1]
