
import time

_ORDER = (3, 2, 4, 1, 5, 0, 6)
_COLS = tuple(63 << (7 * c) for c in range(7))
_FULL = sum(_COLS)
_BOTTOM = sum(1 << (7 * c) for c in range(7))
_CENTER = _COLS[3]
_LEFT_HALF = sum(_COLS[:4])

_ODD_ROWS = sum(
    1 << (7 * c + r)
    for c in range(7)
    for r in (0, 2, 4)
)
_EVEN_ROWS = _FULL ^ _ODD_ROWS

_INFO = {
    1 << (7 * c + r): (c, 3 - abs(c - 3), 7 * c + r)
    for c in range(7)
    for r in range(6)
}

_LINE_STARTS = []
for _dc, _dr in ((0, 1), (1, 0), (1, -1), (1, 1)):
    _starts = 0
    for _c in range(7):
        for _r in range(6):
            if (
                0 <= _c + 3 * _dc < 7
                and 0 <= _r + 3 * _dr < 6
            ):
                _starts |= 1 << (7 * _c + _r)
    _LINE_STARTS.append((7 * _dc + _dr, _starts))
_LINE_STARTS = tuple(_LINE_STARTS)

_MATE = 100000
_INF = 1000000
_EXACT, _LOWER, _UPPER = 0, 1, 2

# Entries remain useful if the module persists between turns.
_TT = {}


class _SearchTimeout(Exception):
    pass


def _winning(p, mask):
    """Empty squares that complete four for p."""
    result = (p << 1) & (p << 2) & (p << 3)

    t = (p << 7) & (p << 14)
    result |= t & ((p << 21) | (p >> 7))
    t = (p >> 7) & (p >> 14)
    result |= t & ((p << 7) | (p >> 21))

    t = (p << 6) & (p << 12)
    result |= t & ((p << 18) | (p >> 6))
    t = (p >> 6) & (p >> 12)
    result |= t & ((p << 6) | (p >> 18))

    t = (p << 8) & (p << 16)
    result |= t & ((p << 24) | (p >> 8))
    t = (p >> 8) & (p >> 16)
    result |= t & ((p << 8) | (p >> 24))

    return result & (_FULL ^ mask)


def _mirror(x):
    result = 0
    for _ in range(7):
        result = (result << 7) | (x & 127)
        x >>= 7
    return result


def _evaluate(p, mask, count, opponent_wins, safe, possible):
    q = mask ^ p
    my_wins = _winning(p, mask)

    score = 48 * (
        my_wins.bit_count() - opponent_wins.bit_count()
    )

    # The first player prefers odd-height threats; the second
    # player generally prefers even-height threats.
    if count & 1:
        my_parity, their_parity = _EVEN_ROWS, _ODD_ROWS
    else:
        my_parity, their_parity = _ODD_ROWS, _EVEN_ROWS

    score += 12 * (
        (my_wins & my_parity).bit_count()
        - (opponent_wins & their_parity).bit_count()
    )

    # Consecutive threats in one column are particularly valuable.
    score += 40 * (
        (my_wins & (my_wins >> 1)).bit_count()
        - (opponent_wins & (opponent_wins >> 1)).bit_count()
    )

    score += 3 * (
        (p & _CENTER).bit_count() - (q & _CENTER).bit_count()
    )

    # Count unblocked four-cell windows and windows with at least
    # two friendly discs, in parallel using bit operations.
    for shift, starts in _LINE_STARTS:
        p1 = p >> shift
        p2 = p >> (2 * shift)
        p3 = p >> (3 * shift)
        q1 = q >> shift
        q2 = q >> (2 * shift)
        q3 = q >> (3 * shift)

        open_p = starts & ~(q | q1 | q2 | q3)
        open_q = starts & ~(p | p1 | p2 | p3)

        two_p = (p & p1) | (p2 & p3) | ((p | p1) & (p2 | p3))
        two_q = (q & q1) | (q2 & q3) | ((q | q1) & (q2 | q3))

        score += 2 * (open_p.bit_count() - open_q.bit_count())
        score += 10 * (
            (open_p & two_p).bit_count()
            - (open_q & two_q).bit_count()
        )

    their_safe = possible & ~(my_wins >> 1)
    score += 4 * (safe.bit_count() - their_safe.bit_count())
    return score


def policy(board: list[list[int]]) -> int:
    clock = time.perf_counter
    deadline = clock() + 0.90

    p = 0
    mask = 0
    for c in range(7):
        for r in range(6):
            value = board[5 - r][c]
            bit = 1 << (7 * c + r)
            if value:
                mask |= bit
                if value == 1:
                    p |= bit

    legal = [c for c in _ORDER if (mask & _COLS[c]) != _COLS[c]]
    if not legal:
        # A full board has no legal action; normally it is never queried.
        return 0

    # Defensive fallback for a board containing floating discs.
    for c in range(7):
        column = (mask >> (7 * c)) & 63
        if column & (column + 1):
            return int(legal[0])

    count = mask.bit_count()
    if count <= 1:
        return 3 if 3 in legal else int(legal[0])

    winning = _winning
    possible = (mask + _BOTTOM) & _FULL

    immediate = winning(p, mask) & possible
    if immediate:
        for c in _ORDER:
            if immediate & _COLS[c]:
                return int(c)

    opponent_wins = winning(mask ^ p, mask)
    forced = possible & opponent_wins

    if forced and (forced & (forced - 1)):
        safe = 0
    else:
        safe = (forced or possible) & ~(opponent_wins >> 1)

    # Establish a legal, tactically sensible fallback immediately.
    candidates = safe or forced or possible
    fallback_bit = 0
    fallback_score = -_INF
    bits = candidates
    while bits:
        move = bits & -bits
        bits ^= move
        _, centrality, _ = _INFO[move]
        value = (
            16 * winning(p | move, mask | move).bit_count()
            + centrality
        )
        if value > fallback_score:
            fallback_score = value
            fallback_bit = move

    fallback_col = _INFO[fallback_bit][0]

    if not safe:
        return int(fallback_col)
    if not (safe & (safe - 1)):
        return int(_INFO[safe][0])

    tt = _TT
    if len(tt) > 180000:
        tt.clear()
    tt_get = tt.get

    root_count = count
    root_key = p + mask
    root_symmetric = _mirror(p) == p and _mirror(mask) == mask

    history = [[0] * 49 for _ in range(2)]
    killers = [0] * 43
    nodes = 0

    def search(pos, occupied, depth, alpha, beta, n):
        nonlocal nodes
        nodes += 1
        if (nodes & 255) == 0 and clock() >= deadline:
            raise _SearchTimeout

        key = pos + occupied
        entry = tt_get(key)
        preferred = 0

        if entry is not None:
            stored_depth, value, flag, preferred = entry
            if stored_depth >= depth:
                if flag == _EXACT:
                    return value
                if flag == _LOWER:
                    alpha = max(alpha, value)
                else:
                    beta = min(beta, value)
                if alpha >= beta:
                    return value

        alpha_start = alpha
        beta_start = beta
        remaining = 42 - n
        playable = (occupied + _BOTTOM) & _FULL

        if not playable:
            tt[key] = (64, 0, _EXACT, 0)
            return 0

        other = occupied ^ pos
        threats = winning(other, occupied)
        must_block = playable & threats

        if must_block and (must_block & (must_block - 1)):
            allowed = 0
        else:
            allowed = (must_block or playable) & ~(threats >> 1)

        # Every searched position has no immediate win for its
        # side to move: its parent only played non-losing moves.
        if not allowed:
            value = -(_MATE + remaining - 2)
            tt[key] = (64, value, _EXACT, 0)
            return value

        if n == root_count and root_symmetric:
            allowed &= _LEFT_HALF

        if remaining <= 2:
            move = allowed & -allowed
            tt[key] = (64, 0, _EXACT, move)
            return 0

        single_move = not (allowed & (allowed - 1))

        # Extend forced sequences even beyond the nominal horizon.
        if depth <= 0 and not single_move:
            value = _evaluate(
                pos, occupied, n, threats, allowed, playable
            )
            tt[key] = (0, value, _EXACT, 0)
            return value

        if single_move:
            preferred = allowed
        elif not (preferred & allowed):
            preferred = 0

        child_depth = max(0, depth - 1)
        hist = history[n & 1]
        killer = killers[n]
        todo = allowed
        ordered = None
        best_value = -_INF
        best_move = 0
        first = True

        while todo:
            if preferred:
                move = preferred
                preferred = 0
            else:
                # Delay ordering the remaining moves until the
                # transposition-table move has failed to cut off.
                if ordered is None:
                    ordered = []
                    bits = todo
                    while bits:
                        candidate = bits & -bits
                        bits ^= candidate
                        _, centrality, square = _INFO[candidate]
                        priority = (
                            256
                            * winning(
                                pos | candidate, occupied | candidate
                            ).bit_count()
                            + 8 * centrality
                            + hist[square]
                            + (96 if candidate == killer else 0)
                        )
                        ordered.append((priority, candidate))
                    ordered.sort()
                move = ordered.pop()[1]

            todo ^= move
            new_mask = occupied | move

            if first:
                value = -search(
                    other, new_mask, child_depth,
                    -beta, -alpha, n + 1
                )
                first = False
            else:
                # Principal-variation search.
                value = -search(
                    other, new_mask, child_depth,
                    -alpha - 1, -alpha, n + 1
                )
                if alpha < value < beta:
                    value = -search(
                        other, new_mask, child_depth,
                        -beta, -alpha, n + 1
                    )

            if value > best_value:
                best_value = value
                best_move = move
            if value > alpha:
                alpha = value

            if alpha >= beta:
                if not single_move:
                    killers[n] = move
                    square = _INFO[move][2]
                    hist[square] = min(
                        128, hist[square] + depth * depth
                    )
                break

        if best_value <= alpha_start:
            flag = _UPPER
        elif best_value >= beta_start:
            flag = _LOWER
        else:
            flag = _EXACT

        tt[key] = (depth, best_value, flag, best_move)
        return best_value

    best_bit = fallback_bit
    cached = tt_get(root_key)
    if cached is not None and (cached[3] & safe):
        best_bit = cached[3]

    previous_score = 0
    remaining = 42 - count

    try:
        for depth in range(1, remaining + 1):
            if clock() >= deadline:
                break

            if depth >= 4:
                alpha = previous_score - 96
                beta = previous_score + 96
            else:
                alpha, beta = -_INF, _INF

            score = search(p, mask, depth, alpha, beta, count)

            # Widen a failed aspiration window.
            if score <= alpha or score >= beta:
                if clock() >= deadline:
                    break
                score = search(
                    p, mask, depth, -_INF, _INF, count
                )

            entry = tt_get(root_key)
            if entry is not None and (entry[3] & safe):
                best_bit = entry[3]
            previous_score = score

            if abs(score) >= _MATE:
                break

            for hist in history:
                for i in range(49):
                    hist[i] >>= 1

    except _SearchTimeout:
        pass

    column = _INFO[best_bit][0]
    return int(column if column in legal else legal[0])
