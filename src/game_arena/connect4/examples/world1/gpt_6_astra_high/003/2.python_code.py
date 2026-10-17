
from time import perf_counter

_ORDER = (3, 2, 4, 1, 5, 0, 6)
_COLS = tuple(63 << (7 * c) for c in range(7))
_BOTTOM = sum(1 << (7 * c) for c in range(7))
_BOARD = _BOTTOM * 63
_ODD = _BOTTOM * 21
_EVEN = _ODD << 1
_CENTER = _COLS[3]
_INNER = _COLS[2] | _COLS[4]

# Valid starting squares for every four-cell segment.
_LINES = (
    (1, sum(1 << (7 * c + r)
            for c in range(7) for r in range(3))),
    (7, sum(1 << (7 * c + r)
            for c in range(4) for r in range(6))),
    (6, sum(1 << (7 * c + r)
            for c in range(4) for r in range(3, 6))),
    (8, sum(1 << (7 * c + r)
            for c in range(4) for r in range(3))),
)

_MATE = 30000
_INF = 1000000
_EXACT, _LOWER, _UPPER = 0, 1, 2
_TT = {}


class _Timeout(Exception):
    pass


def _winning(p, occupied):
    """Empty squares which complete four for p."""
    result = (p << 1) & (p << 2) & (p << 3)

    for shift in (7, 6, 8):
        twice = shift * 2
        thrice = shift * 3
        pair = (p << shift) & (p << twice)
        result |= pair & ((p << thrice) | (p >> shift))
        pair = (p >> shift) & (p >> twice)
        result |= pair & ((p << shift) | (p >> thrice))

    return result & (_BOARD ^ occupied)


def _mirror(bits):
    result = 0
    for c in range(7):
        result |= ((bits >> (7 * c)) & 127) << (7 * (6 - c))
    return result


def _evaluate(p, occupied, opponent_wins, count):
    opponent = occupied ^ p
    own_wins = _winning(p, occupied)

    score = 3 * (
        (p & _CENTER).bit_count()
        - (opponent & _CENTER).bit_count()
    )
    score += (
        (p & _INNER).bit_count()
        - (opponent & _INNER).bit_count()
    )

    # Count uncontested windows with at least one or two discs.
    for shift, starts in _LINES:
        b = p >> shift
        c = p >> (2 * shift)
        d = p >> (3 * shift)
        f = opponent >> shift
        g = opponent >> (2 * shift)
        h = opponent >> (3 * shift)

        ab, cd = p | b, c | d
        ef, gh = opponent | f, g | h
        own_any = ab | cd
        opp_any = ef | gh

        own_open = starts & ~opp_any
        opp_open = starts & ~own_any

        own_two = (p & b) | (c & d) | (ab & cd)
        opp_two = (opponent & f) | (g & h) | (ef & gh)

        score += 2 * (
            (own_open & own_any).bit_count()
            - (opp_open & opp_any).bit_count()
        )
        score += 10 * (
            (own_open & own_two).bit_count()
            - (opp_open & opp_two).bit_count()
        )

    score += 44 * (
        own_wins.bit_count() - opponent_wins.bit_count()
    )

    # Odd rows favor the first player; even rows favor the second.
    own_parity = _ODD if count % 2 == 0 else _EVEN
    opp_parity = _EVEN if count % 2 == 0 else _ODD
    score += 14 * (
        (own_wins & own_parity).bit_count()
        - (opponent_wins & opp_parity).bit_count()
    )

    # Vertically adjacent threats cannot both be blocked.
    score += 40 * (
        (own_wins & (own_wins >> 1)).bit_count()
        - (opponent_wins & (opponent_wins >> 1)).bit_count()
    )
    return score


def policy(board: list[list[int]]) -> int:
    global _TT

    deadline = perf_counter() + 0.90

    legal = [
        c for c in _ORDER
        if any(board[r][c] == 0 for r in range(6))
    ]
    if not legal:
        # A full board has no legal action; it should never be queried.
        return 0
    if len(legal) == 1:
        return int(legal[0])

    p = 0
    occupied = 0
    for c in range(7):
        for r in range(6):
            value = board[r][c]
            if value:
                bit = 1 << (7 * c + 5 - r)
                occupied |= bit
                if value == 1:
                    p |= bit

    count = occupied.bit_count()
    if count <= 1 and 3 in legal:
        return 3

    possible = (occupied + _BOTTOM) & _BOARD
    wins = _winning(p, occupied) & possible
    if wins:
        for c in legal:
            if wins & _COLS[c]:
                return int(c)

    opponent = occupied ^ p
    opponent_wins = _winning(opponent, occupied)
    forced = possible & opponent_wins

    if forced and forced & (forced - 1):
        # Two immediate opponent wins: block one when defeat is forced.
        for c in legal:
            if forced & _COLS[c]:
                return int(c)

    safe = forced if forced else possible
    safe &= ~(opponent_wins >> 1)

    if not safe:
        for c in legal:
            if forced & _COLS[c]:
                return int(c)
        return int(legal[0])

    root_order = [c for c in legal if safe & _COLS[c]]
    if not root_order:
        return int(legal[0])
    if len(root_order) == 1:
        return int(root_order[0])

    # Equivalent moves need not both be searched on symmetric boards.
    if p == _mirror(p) and occupied == _mirror(occupied):
        root_order = [c for c in root_order if c <= 3]

    if len(root_order) == 1 or count >= 40:
        return int(root_order[0])

    if len(_TT) > 240000:
        _TT = {}
    tt = _TT

    root_key = p + occupied
    root_entry = tt.get(root_key)
    cached_col = root_entry[3] if root_entry else -1

    if cached_col not in root_order and 6 - cached_col in root_order:
        if p == _mirror(p) and occupied == _mirror(occupied):
            cached_col = 6 - cached_col

    if (root_entry and root_entry[2] == _EXACT
            and abs(root_entry[1]) >= _MATE
            and cached_col in root_order):
        return int(cached_col)

    root_moves = {c: safe & _COLS[c] for c in root_order}
    initial_scores = {}
    for rank, c in enumerate(root_order):
        move = root_moves[c]
        new_occupied = occupied | move
        threats = _winning(p | move, new_occupied)
        playable = (new_occupied + _BOTTOM) & _BOARD
        immediate = threats & playable

        if immediate and immediate & (immediate - 1):
            return int(c)

        initial_scores[c] = (
            48 * threats.bit_count()
            + 128 * immediate.bit_count()
            + 7 - rank
            + (100000 if c == cached_col else 0)
        )

    root_order.sort(key=initial_scores.get, reverse=True)
    chosen = root_order[0]
    proven_move = None

    history = [[0] * 7 for _ in range(2)]
    killers = [[-1, -1] for _ in range(43)]
    nodes = 0
    win_squares = _winning
    evaluate = _evaluate
    clock = perf_counter

    def search(position, mask, depth, alpha, beta, n):
        nonlocal nodes
        nodes += 1
        if nodes & 127 == 0 and clock() >= deadline:
            raise _Timeout

        if n >= 42:
            return 0

        key = position + mask
        entry = tt.get(key)
        tt_col = -1
        if entry is not None:
            old_depth, value, flag, tt_col = entry
            if old_depth >= depth:
                if flag == _EXACT:
                    return value
                if flag == _LOWER and value >= beta:
                    return value
                if flag == _UPPER and value <= alpha:
                    return value

        other = mask ^ position
        available = (mask + _BOTTOM) & _BOARD
        threats = win_squares(other, mask)
        block = available & threats

        # Every searched position has no immediate win for the mover:
        # its parent excluded moves allowing one.
        if block and block & (block - 1):
            value = -_MATE - (41 - n)
            tt[key] = (99, value, _EXACT, -1)
            return value

        moves = block if block else available
        moves &= ~(threats >> 1)
        if not moves:
            value = -_MATE - (41 - n)
            tt[key] = (99, value, _EXACT, -1)
            return value

        if n >= 40:
            tt[key] = (99, 0, _EXACT, -1)
            return 0

        single = not (moves & (moves - 1))
        if depth <= 0 and not single:
            value = evaluate(position, mask, threats, n)
            if entry is None or entry[0] <= 0:
                tt[key] = (0, value, _EXACT, -1)
            return value

        alpha_original = alpha

        if single:
            col = (moves.bit_length() - 1) // 7
            candidates = [(0, col, moves)]
            next_depth = depth  # Extend forced sequences.
        else:
            next_depth = depth - 1
            candidates = []
            hist = history[n & 1]
            killer1, killer2 = killers[n]

            # A cached principal move usually gives sufficient ordering
            # for repeated searches; expensive ordering is most useful
            # in previously unexplored subtrees.
            tactical_order = depth >= 3 and (
                tt_col < 0 or depth >= 5
            )

            for rank, col in enumerate(_ORDER):
                move = moves & _COLS[col]
                if not move:
                    continue

                order_score = 7 - rank + hist[col] // 8
                if col == killer1:
                    order_score += 2000
                elif col == killer2:
                    order_score += 1500
                if col == tt_col:
                    order_score += 1000000

                if tactical_order:
                    new_mask = mask | move
                    own_threats = win_squares(
                        position | move, new_mask
                    )
                    next_available = (
                        new_mask + _BOTTOM
                    ) & _BOARD
                    immediate = own_threats & next_available

                    if immediate and immediate & (immediate - 1):
                        value = _MATE + 40 - n
                        tt[key] = (99, value, _EXACT, col)
                        return value

                    order_score += (
                        48 * own_threats.bit_count()
                        + 128 * immediate.bit_count()
                    )

                candidates.append((order_score, col, move))

            candidates.sort(reverse=True)

        best = -_INF
        best_col = candidates[0][1]

        for index, (_, col, move) in enumerate(candidates):
            new_mask = mask | move

            if index == 0 or depth <= 1:
                value = -search(
                    other, new_mask, next_depth,
                    -beta, -alpha, n + 1
                )
            else:
                value = -search(
                    other, new_mask, next_depth,
                    -alpha - 1, -alpha, n + 1
                )
                if alpha < value < beta:
                    value = -search(
                        other, new_mask, next_depth,
                        -beta, -alpha, n + 1
                    )

            if value > best:
                best, best_col = value, col
            if value > alpha:
                alpha = value

            if alpha >= beta:
                if not single:
                    hist = history[n & 1]
                    hist[col] += max(1, depth * depth)
                    if hist[col] > 4096:
                        for c in range(7):
                            hist[c] //= 2
                    if killers[n][0] != col:
                        killers[n][1] = killers[n][0]
                        killers[n][0] = col
                break

        flag = (
            _UPPER if best <= alpha_original
            else _LOWER if best >= beta
            else _EXACT
        )
        if entry is None or depth >= entry[0]:
            tt[key] = (depth, best, flag, best_col)
        return best

    def search_root(depth, alpha, beta):
        nonlocal proven_move
        best = -_INF
        best_col = root_order[0]
        scores = []

        for index, col in enumerate(root_order):
            if clock() >= deadline:
                raise _Timeout

            new_mask = occupied | root_moves[col]
            if index == 0 or depth <= 2:
                value = -search(
                    opponent, new_mask, depth - 1,
                    -beta, -alpha, count + 1
                )
            else:
                value = -search(
                    opponent, new_mask, depth - 1,
                    -alpha - 1, -alpha, count + 1
                )
                if alpha < value < beta:
                    value = -search(
                        opponent, new_mask, depth - 1,
                        -beta, -alpha, count + 1
                    )

            scores.append((value, col))
            if value >= _MATE:
                proven_move = col
            if value > best:
                best, best_col = value, col
            if value > alpha:
                alpha = value
            if alpha >= beta:
                break

        return best, best_col, scores

    previous_score = 0
    try:
        for depth in range(1, 43 - count):
            if clock() >= deadline:
                break

            if depth >= 4:
                alpha = previous_score - 64
                beta = previous_score + 64
            else:
                alpha, beta = -_INF, _INF

            score, col, scores = search_root(depth, alpha, beta)

            if score <= alpha or score >= beta:
                root_order = [col] + [
                    c for c in root_order if c != col
                ]
                score, col, scores = search_root(
                    depth, -_INF, _INF
                )

            chosen = col
            previous_score = score
            scores.sort(key=lambda item: item[0], reverse=True)
            root_order = [c for _, c in scores]

            old = tt.get(root_key)
            if old is None or depth >= old[0]:
                tt[root_key] = (depth, score, _EXACT, chosen)

            if abs(score) >= _MATE:
                break

    except _Timeout:
        pass

    if proven_move is not None:
        return int(proven_move)
    return int(chosen)
