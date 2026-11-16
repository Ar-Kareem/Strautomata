
from array import array
from time import perf_counter


_FULL = (1 << 16) - 1
_MATE = 10000
_INF = 20000

_LINES = tuple(
    [15 << (4 * r) for r in range(4)]
    + [sum(1 << (4 * r + c) for r in range(4)) for c in range(4)]
    + [
        sum(1 << (5 * i) for i in range(4)),
        sum(1 << (3 + 3 * i) for i in range(4)),
    ]
)

_CELL_LINES = tuple(
    sum(1 << j for j, line in enumerate(_LINES) if line & (1 << i))
    for i in range(16)
)

_POSITION = (
    6, 3, 3, 6,
    3, 7, 7, 3,
    3, 7, 7, 3,
    6, 3, 3, 6,
)

_READY = False
_TT = {}


def _initialize():
    """Build compact lookup tables, once per Python process."""
    global _READY, _TOUCH, _ONE, _TWO, _THREATS, _WON, _FORKS

    if _READY:
        return

    unions = [0] * 1024
    forks = [0] * 1024

    for s in range(1, 1024):
        bit = s & -s
        rest = s ^ bit
        line = _LINES[bit.bit_length() - 1]
        unions[s] = unions[rest] | line
        forks[s] = forks[rest] | (unions[rest] & line)

    touch = array("H", [0]) * 65536
    one = array("H", [0]) * 65536
    two = array("H", [0]) * 65536
    three = array("H", [0]) * 65536
    threats = array("H", [0]) * 65536
    won = bytearray(65536)

    for mask in range(1, 65536):
        bit = mask & -mask
        rest = mask ^ bit
        affected = _CELL_LINES[bit.bit_length() - 1]
        unaffected = ~affected

        old_touch = touch[rest]
        old_one = one[rest]
        old_two = two[rest]
        old_three = three[rest]

        touch[mask] = old_touch | affected
        one[mask] = (
            (old_one & unaffected) | (affected & ~old_touch)
        )
        two[mask] = (
            (old_two & unaffected) | (old_one & affected)
        )
        new_three = (
            (old_three & unaffected) | (old_two & affected)
        )
        three[mask] = new_three
        threats[mask] = unions[new_three] & (_FULL ^ mask)
        won[mask] = bool(won[rest] or (old_three & affected))

    _TOUCH = touch
    _ONE = one
    _TWO = two
    _THREATS = threats
    _WON = won
    _FORKS = forks
    _READY = True


def _evaluate(me, opponent):
    my_open = ~_TOUCH[opponent]
    their_open = ~_TOUCH[me]

    singles = (
        (_ONE[me] & my_open).bit_count()
        - (_ONE[opponent] & their_open).bit_count()
    )
    doubles = (
        (_TWO[me] & my_open).bit_count()
        - (_TWO[opponent] & their_open).bit_count()
    )

    return 5 * singles + 32 * doubles + 2


class _Timeout(Exception):
    pass


class _Search:
    def __init__(self, deadline):
        self.deadline = deadline
        self.nodes = 0
        self.killers = [(0, 0) for _ in range(17)]
        self.history = [0] * 16

    def ordered_moves(
        self, me, opponent, empty, hash_move=0, forced=0, opponent_forks=0
    ):
        if forced:
            return [forced]

        n = empty.bit_count()
        killer1, killer2 = self.killers[n]
        my_open = ~_TOUCH[opponent]
        their_twos = _TWO[opponent]
        ranked = []

        remaining_moves = empty
        while remaining_moves:
            move = remaining_moves & -remaining_moves
            remaining_moves ^= move

            new_me = me | move
            next_empty = empty ^ move
            attacks = _THREATS[new_me] & next_empty
            their_open = ~_TOUCH[new_me]

            # Without a forcing threat of our own, leaving an opposing
            # fork available loses immediately to that fork.
            if (
                opponent_forks
                and not attacks
                and (_FORKS[their_twos & their_open] & next_empty)
            ):
                continue

            index = move.bit_length() - 1
            score = _POSITION[index]
            score += min(self.history[index], 8000)
            score += 100 * (_TWO[new_me] & my_open).bit_count()
            score -= 120 * (their_twos & their_open).bit_count()

            if attacks:
                score += 100000
            if move == killer1:
                score += 15000
            elif move == killer2:
                score += 12000
            if move == hash_move:
                score += 1000000

            ranked.append((score, move))

        ranked.sort(reverse=True)
        return [move for _, move in ranked]

    def search(self, me, opponent, depth, alpha, beta):
        self.nodes += 1
        if (self.nodes & 127) == 0 and perf_counter() >= self.deadline:
            raise _Timeout

        empty = _FULL ^ (me | opponent)
        n = empty.bit_count()

        if _WON[opponent]:
            return -_MATE - n
        if not empty:
            return 0

        winning = _THREATS[me] & empty
        if winning:
            return _MATE + n - 1

        forced = _THREATS[opponent] & empty
        if forced and (forced & (forced - 1)):
            return -_MATE - n + 2

        opponent_forks = 0
        if not forced:
            my_forks = _FORKS[_TWO[me] & ~_TOUCH[opponent]] & empty
            if my_forks:
                return _MATE + n - 3

            opponent_forks = (
                _FORKS[_TWO[opponent] & ~_TOUCH[me]] & empty
            )

            # Extend tactical positions beyond the nominal horizon.
            if depth <= 0 and not opponent_forks:
                return _evaluate(me, opponent)

        key = me | (opponent << 16)
        effective_depth = max(depth, 0)
        entry = _TT.get(key)
        hash_move = 0

        if entry is not None:
            saved_depth, saved_score, flag, hash_move = entry
            if saved_depth >= effective_depth:
                if flag == 0:
                    return saved_score
                if flag == 1 and saved_score >= beta:
                    return saved_score
                if flag == 2 and saved_score <= alpha:
                    return saved_score

        moves = self.ordered_moves(
            me, opponent, empty, hash_move, forced, opponent_forks
        )

        if not moves:
            # Every move permits an immediate opposing fork.
            value = -_MATE - n + 4
            _TT[key] = (64, value, 0, empty & -empty)
            return value

        original_alpha = alpha
        best_score = -_INF
        best_move = moves[0]

        for index, move in enumerate(moves):
            if index == 0:
                score = -self.search(
                    opponent, me | move, depth - 1, -beta, -alpha
                )
            else:
                # Principal-variation search: first test whether this
                # move can improve the current best value.
                score = -self.search(
                    opponent, me | move, depth - 1, -alpha - 1, -alpha
                )
                if alpha < score < beta:
                    score = -self.search(
                        opponent, me | move, depth - 1, -beta, -alpha
                    )

            if score > best_score:
                best_score = score
                best_move = move

            if score > alpha:
                alpha = score

            if alpha >= beta:
                first, second = self.killers[n]
                if move != first:
                    self.killers[n] = (move, first)

                cell = move.bit_length() - 1
                self.history[cell] += max(1, effective_depth ** 2)
                break

        if best_score <= original_alpha:
            flag = 2
        elif best_score >= beta:
            flag = 1
        else:
            flag = 0

        _TT[key] = (effective_depth, best_score, flag, best_move)
        return best_score


def policy(board: list[list[int]]) -> tuple[int, int]:
    start = perf_counter()

    me = 0
    opponent = 0
    for row in range(4):
        for col in range(4):
            bit = 1 << (4 * row + col)
            if board[row][col] == 1:
                me |= bit
            elif board[row][col] == -1:
                opponent |= bit

    empty = _FULL ^ (me | opponent)

    # A full board has no legal action; ordinary arena calls are
    # expected to be nonterminal.
    if not empty:
        return (0, 0)

    if empty == _FULL:
        return (1, 1)

    if not (empty & (empty - 1)):
        index = empty.bit_length() - 1
        return divmod(index, 4)

    _initialize()

    winning = _THREATS[me] & empty
    if winning:
        move = winning & -winning
        return divmod(move.bit_length() - 1, 4)

    blocking = _THREATS[opponent] & empty
    if blocking:
        move = blocking & -blocking
        return divmod(move.bit_length() - 1, 4)

    forks = _FORKS[_TWO[me] & ~_TOUCH[opponent]] & empty
    if forks:
        move = forks & -forks
        return divmod(move.bit_length() - 1, 4)

    # Absolute mate scores depend on remaining empty cells, allowing
    # transposition entries to be reused safely between calls.
    if len(_TT) > 180000:
        _TT.clear()

    deadline = start + 0.88
    searcher = _Search(deadline)
    root_key = me | (opponent << 16)
    entry = _TT.get(root_key)
    hash_move = entry[3] if entry is not None else 0

    opponent_forks = (
        _FORKS[_TWO[opponent] & ~_TOUCH[me]] & empty
    )
    candidates = searcher.ordered_moves(
        me, opponent, empty, hash_move, 0, opponent_forks
    )

    # Establish a legal move before beginning interruptible search.
    best_move = candidates[0] if candidates else empty & -empty
    previous_score = None

    for depth in range(1, empty.bit_count() + 1):
        if perf_counter() >= deadline:
            break

        try:
            if depth >= 3 and previous_score is not None:
                low = previous_score - 64
                high = previous_score + 64
                score = searcher.search(me, opponent, depth, low, high)
                if score <= low or score >= high:
                    score = searcher.search(
                        me, opponent, depth, -_INF, _INF
                    )
            else:
                score = searcher.search(
                    me, opponent, depth, -_INF, _INF
                )
        except _Timeout:
            break

        entry = _TT.get(root_key)
        if entry is not None and (entry[3] & empty):
            best_move = entry[3]

        previous_score = score
        if abs(score) >= _MATE:
            break

    if not (best_move & empty) or (best_move & (best_move - 1)):
        best_move = empty & -empty

    return divmod(best_move.bit_length() - 1, 4)
