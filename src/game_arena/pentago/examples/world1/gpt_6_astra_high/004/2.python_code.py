
import time
from functools import lru_cache


FULL = (1 << 36) - 1
MATE = 1_000_000
INF = 2_000_000
WEIGHTS = (0, 3, 18, 110, 650, 100_000)

# Bits are packed by quadrant, with nine bits per quadrant.
CELL = [
    [
        ((r // 3) * 2 + c // 3) * 9 + (r % 3) * 3 + c % 3
        for c in range(6)
    ]
    for r in range(6)
]

COORD = [None] * 36
for _r in range(6):
    for _c in range(6):
        COORD[CELL[_r][_c]] = (_r + 1, _c + 1)

LINES = []
for _dr, _dc in ((0, 1), (1, 0), (1, 1), (1, -1)):
    for _r in range(6):
        for _c in range(6):
            _er = _r + 4 * _dr
            _ec = _c + 4 * _dc
            if 0 <= _er < 6 and 0 <= _ec < 6:
                _mask = 0
                for _k in range(5):
                    _mask |= 1 << CELL[_r + _k * _dr][_c + _k * _dc]
                LINES.append(_mask)
LINES = tuple(LINES)

# Direction zero is L; direction one is R.
LOCAL_MAP = [[], []]
for _i in range(9):
    _r, _c = divmod(_i, 3)
    LOCAL_MAP[0].append((2 - _c) * 3 + _r)
    LOCAL_MAP[1].append(_c * 3 + 2 - _r)

LOCAL_ROT = []
for _direction in range(2):
    _table = [0] * 512
    for _x in range(1, 512):
        _bit = _x & -_x
        _i = _bit.bit_length() - 1
        _table[_x] = (
            _table[_x ^ _bit] | (1 << LOCAL_MAP[_direction][_i])
        )
    LOCAL_ROT.append(_table)

ROT_TABLE = []
KEEP = []
SHIFT = []
INVERSE_CELL = []

for _rotation in range(8):
    _q, _direction = divmod(_rotation, 2)
    _shift = 9 * _q
    SHIFT.append(_shift)
    KEEP.append(FULL ^ (511 << _shift))
    ROT_TABLE.append(
        tuple(x << _shift for x in LOCAL_ROT[_direction])
    )
    _inverse = []
    for _i in range(36):
        if _i // 9 == _q:
            _inverse.append(
                _shift + LOCAL_MAP[_direction ^ 1][_i % 9]
            )
        else:
            _inverse.append(_i)
    INVERSE_CELL.append(tuple(_inverse))

CENTERS = sum(1 << (9 * q + 4) for q in range(4))
CELL_BONUS = tuple(8 if i % 9 == 4 else 0 for i in range(36))


def _rotate(board, rotation):
    return (
        (board & KEEP[rotation])
        | ROT_TABLE[rotation][
            (board >> SHIFT[rotation]) & 511
        ]
    )


def _action(index, rotation):
    row, col = COORD[index]
    return f"{row},{col},{rotation // 2},{'L' if rotation % 2 == 0 else 'R'}"


def _mapped_action(bit, rotation):
    index = INVERSE_CELL[rotation][bit.bit_length() - 1]
    return index, rotation


@lru_cache(maxsize=65536)
def _patterns(board):
    """Return (already has five, cells completing an own four)."""
    if board.bit_count() < 4:
        return False, 0

    holes = 0
    for mask in LINES:
        occupied = board & mask
        if occupied == mask:
            return True, 0
        if occupied.bit_count() == 4:
            holes |= mask ^ occupied
    return False, holes


@lru_cache(maxsize=32768)
def _safe_placements(me, opponent):
    """
    The boards have already undergone our chosen rotation, but our
    new marble has not yet been added.

    Return every empty placement that prevents an immediate opponent
    win on the following turn. Simultaneous wins are treated as draws.
    """
    empty = FULL ^ (me | opponent)
    if opponent.bit_count() < 4:
        return empty

    safe = empty
    for rotation in range(8):
        other_rotated = _rotate(opponent, rotation)
        other_win, other_holes = _patterns(other_rotated)

        if not other_win and not other_holes:
            continue

        me_rotated = _rotate(me, rotation)
        rotated_empty = FULL ^ (me_rotated | other_rotated)
        threats = other_holes & rotated_empty

        if not other_win and not threats:
            continue

        my_win, my_holes = _patterns(me_rotated)
        if my_win:
            # The opponent cannot win alone after this rotation.
            continue

        allowed = my_holes & rotated_empty

        # A single enemy completion can also be blocked directly.
        if not other_win and threats and not (threats & (threats - 1)):
            allowed |= threats

        if not allowed:
            return 0

        safe &= _rotate(allowed, rotation ^ 1)
        if not safe:
            return 0

    return safe


@lru_cache(maxsize=32768)
def _evaluate(me, opponent):
    score = 8 * (
        (me & CENTERS).bit_count()
        - (opponent & CENTERS).bit_count()
    )
    for mask in LINES:
        a = me & mask
        b = opponent & mask
        if not b:
            score += WEIGHTS[a.bit_count()]
        elif not a:
            score -= WEIGHTS[b.bit_count()]
    return score


def _rank_placements(me, opponent, available):
    """Incrementally evaluate adding a marble at each available cell."""
    base = 8 * (
        (me & CENTERS).bit_count()
        - (opponent & CENTERS).bit_count()
    )
    delta = list(CELL_BONUS)

    for mask in LINES:
        a = me & mask
        b = opponent & mask
        if a and b:
            continue

        if not b:
            count = a.bit_count()
            base += WEIGHTS[count]
            change = WEIGHTS[count + 1] - WEIGHTS[count]
        else:
            count = b.bit_count()
            base -= WEIGHTS[count]
            change = WEIGHTS[count]

        cells = mask & available
        while cells:
            bit = cells & -cells
            cells ^= bit
            delta[bit.bit_length() - 1] += change

    result = []
    cells = available
    while cells:
        bit = cells & -cells
        cells ^= bit
        index = bit.bit_length() - 1
        result.append((base + delta[index], index))
    return result


class _Timeout(Exception):
    pass


class _Engine:
    def __init__(self, deadline):
        self.deadline = deadline
        self.tt = {}

    def check(self):
        if time.perf_counter() >= self.deadline:
            raise _Timeout

    def generate(self, me, opponent, root=False):
        """
        Return:
            nonterminal safe moves,
            immediate winning action or None,
            drawing action or None,
            fallback action or None.

        Move tuples are:
            (ordering score, resulting me, resulting opponent,
             original placement index, rotation).
        """
        self.check()
        groups = []
        seen_rotations = set()
        draw = None
        fallback = None
        fallback_score = -INF

        # Check every rotation for a direct win before doing more work.
        for rotation in range(8):
            a = _rotate(me, rotation)
            b = _rotate(opponent, rotation)
            key = (a, b)
            if key in seen_rotations:
                continue
            seen_rotations.add(key)

            empty = FULL ^ (a | b)
            my_win, holes = _patterns(a)
            other_win, _ = _patterns(b)
            completions = holes & empty

            if other_win:
                drawing_cells = empty if my_win else completions
                if drawing_cells and draw is None:
                    draw = _mapped_action(
                        drawing_cells & -drawing_cells, rotation
                    )
                continue

            winning_cells = empty if my_win else completions
            if winning_cells:
                win = _mapped_action(
                    winning_cells & -winning_cells, rotation
                )
                return [], win, draw, fallback

            if not (empty & (empty - 1)):
                if draw is None:
                    draw = _mapped_action(empty, rotation)
                continue

            groups.append((a, b, empty, rotation))

        moves = []
        seen_children = set()

        for a, b, empty, rotation in groups:
            self.check()
            safe = _safe_placements(a, b)

            if not safe:
                if root:
                    ranked = _rank_placements(a, b, empty)
                    score, index = max(ranked)
                    if score > fallback_score:
                        fallback_score = score
                        fallback = (
                            INVERSE_CELL[rotation][index], rotation
                        )
                continue

            for score, index in _rank_placements(a, b, safe):
                child = a | (1 << index)
                key = (child, b)
                if key in seen_children:
                    continue
                seen_children.add(key)
                original = INVERSE_CELL[rotation][index]
                moves.append((score, child, b, original, rotation))

        moves.sort(key=lambda move: move[0], reverse=True)
        return moves, None, draw, fallback

    def leaf(self, me, opponent, ply):
        """
        All callers arrive through a safe move, so 'me' cannot have an
        immediate winning move. Detect forced tactical losses before
        using the positional evaluation.
        """
        self.check()
        if opponent.bit_count() < 4:
            return _evaluate(me, opponent)

        drawing_move = False
        seen = set()

        for rotation in range(8):
            a = _rotate(me, rotation)
            b = _rotate(opponent, rotation)
            key = (a, b)
            if key in seen:
                continue
            seen.add(key)

            empty = FULL ^ (a | b)
            other_win, _ = _patterns(b)

            if other_win:
                my_win, holes = _patterns(a)
                if my_win or (holes & empty):
                    drawing_move = True
                continue

            # A final placement without an opponent five is a draw:
            # a win for 'me' was excluded by the parent safety check.
            if not (empty & (empty - 1)):
                return 0

            if _safe_placements(a, b):
                value = _evaluate(me, opponent)
                return max(0, value) if drawing_move else value

        if drawing_move:
            return 0
        return -MATE + ply + 1

    def search(self, me, opponent, depth, alpha, beta, ply):
        self.check()
        if depth <= 0:
            return self.leaf(me, opponent, ply)

        key = (me, opponent)
        entry = self.tt.get(key)
        preferred = None

        if entry is not None:
            old_depth, value, flag, preferred = entry
            if old_depth >= depth:
                if flag == 0:
                    return value
                if flag == 1 and value >= beta:
                    return value
                if flag == 2 and value <= alpha:
                    return value

        original_alpha = alpha
        moves, win, draw, _ = self.generate(me, opponent)

        if win is not None:
            value = MATE - ply
            self.tt[key] = (99, value, 0, None)
            return value

        if not moves:
            value = 0 if draw is not None else -MATE + ply + 1
            self.tt[key] = (99, value, 0, None)
            return value

        best = 0 if draw is not None else -INF
        best_child = None

        if best > alpha:
            alpha = best
        if alpha >= beta:
            return best

        if preferred is not None:
            for i, move in enumerate(moves):
                if (move[1], move[2]) == preferred:
                    if i:
                        moves.insert(0, moves.pop(i))
                    break

        empties = 36 - (me | opponent).bit_count()
        if empties <= 7:
            width = len(moves)
        elif ply == 1:
            width = 14
        elif ply == 2:
            width = 10
        else:
            width = 8

        for move in moves[:width]:
            _, child_me, child_other, _, _ = move
            value = -self.search(
                child_other, child_me, depth - 1,
                -beta, -alpha, ply + 1
            )

            if value > best:
                best = value
                best_child = (child_me, child_other)
            if value > alpha:
                alpha = value
            if alpha >= beta:
                break

        if best <= original_alpha:
            flag = 2
        elif best >= beta:
            flag = 1
        else:
            flag = 0

        self.tt[key] = (depth, best, flag, best_child)
        return best


def policy(you, opponent) -> str:
    deadline = time.perf_counter() + 0.88

    me = 0
    other = 0
    for r in range(6):
        for c in range(6):
            bit = 1 << CELL[r][c]
            if you[r][c]:
                me |= bit
            elif opponent[r][c]:
                other |= bit

    empty = FULL ^ (me | other)
    first_empty = (empty & -empty).bit_length() - 1
    best_action = (first_empty, 0)

    if not (me | other):
        return "2,2,0,L"

    engine = _Engine(deadline)

    try:
        moves, win, draw, fallback = engine.generate(
            me, other, root=True
        )

        if win is not None:
            return _action(*win)

        if not moves:
            return _action(*(draw or fallback or best_action))

        best_action = draw or (moves[0][3], moves[0][4])
        best_value = 0 if draw is not None else -INF
        root_scores = {}

        # Examine every safe root move for a forced win on our next
        # turn, before restricting the deeper search's branching.
        for move in moves:
            value = -engine.leaf(move[2], move[1], 1)
            root_scores[(move[1], move[2])] = value

            if value > best_value:
                best_value = value
                best_action = (move[3], move[4])

            if value >= MATE - 2:
                return _action(*best_action)

        ordered = sorted(
            moves,
            key=lambda m: (root_scores[(m[1], m[2])], m[0]),
            reverse=True
        )

        empty_count = empty.bit_count()
        maximum_depth = min(empty_count, 8)

        for depth in range(2, maximum_depth + 1):
            engine.check()
            width = len(ordered) if empty_count <= 8 else 28
            candidates = ordered[:width]

            iteration_value = 0 if draw is not None else -INF
            iteration_action = draw
            alpha = iteration_value
            new_scores = {}
            found_win = False

            for move in candidates:
                value = -engine.search(
                    move[2], move[1], depth - 1,
                    -INF, -alpha, 1
                )
                new_scores[(move[1], move[2])] = value

                if value > iteration_value:
                    iteration_value = value
                    iteration_action = (move[3], move[4])
                if value > alpha:
                    alpha = value

                if value > MATE // 2:
                    found_win = True
                    break

            # Only completed iterations replace the established move.
            if iteration_action is not None:
                best_action = iteration_action
                best_value = iteration_value

            if found_win:
                break

            root_scores.update(new_scores)
            ordered.sort(
                key=lambda m: (
                    (m[3], m[4]) == best_action,
                    root_scores.get((m[1], m[2]), -INF),
                    m[0]
                ),
                reverse=True
            )

    except _Timeout:
        pass

    return _action(*best_action)
