
import time

# ---------------------------------------------------------------------------
# Board geometry and bitboard helpers
# ---------------------------------------------------------------------------

SIZE = 6
SQUARES = 36
ALL = (1 << SQUARES) - 1

DIRECTIONS = (
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1),           (0, 1),
    (1, -1),  (1, 0),  (1, 1),
)

RAYS = []
for r in range(SIZE):
    for c in range(SIZE):
        square_rays = []
        for dr, dc in DIRECTIONS:
            ray = []
            nr, nc = r + dr, c + dc
            while 0 <= nr < SIZE and 0 <= nc < SIZE:
                ray.append(nr * SIZE + nc)
                nr += dr
                nc += dc
            square_rays.append(tuple(ray))
        RAYS.append(tuple(square_rays))

LEFT_COLUMN = sum(1 << (r * SIZE) for r in range(SIZE))
RIGHT_COLUMN = sum(1 << (r * SIZE + SIZE - 1) for r in range(SIZE))
NOT_LEFT = ALL ^ LEFT_COLUMN
NOT_RIGHT = ALL ^ RIGHT_COLUMN

CENTRAL_VALUE = []
for r in range(SIZE):
    for c in range(SIZE):
        CENTRAL_VALUE.append(min(r, c, SIZE - 1 - r, SIZE - 1 - c))

WIN_SCORE = 1_000_000


def _neighbors(bits):
    """All king-adjacent squares to a bitboard."""
    result = ((bits << SIZE) | (bits >> SIZE))
    result |= (bits & NOT_RIGHT) << 1
    result |= (bits & NOT_LEFT) >> 1
    result |= (bits & NOT_RIGHT) << (SIZE + 1)
    result |= (bits & NOT_LEFT) << (SIZE - 1)
    result |= (bits & NOT_RIGHT) >> (SIZE - 1)
    result |= (bits & NOT_LEFT) >> (SIZE + 1)
    return result & ALL


def _generate_moves(me, opponent, blocked):
    """Yield all legal compound moves as (from, to, arrow)."""
    occupied = me | opponent | blocked
    pieces = me

    while pieces:
        from_bit = pieces & -pieces
        pieces ^= from_bit
        origin = from_bit.bit_length() - 1

        for move_ray in RAYS[origin]:
            for destination in move_ray:
                to_bit = 1 << destination
                if occupied & to_bit:
                    break

                occupied_after_move = (occupied ^ from_bit) | to_bit

                for arrow_ray in RAYS[destination]:
                    for arrow in arrow_ray:
                        arrow_bit = 1 << arrow
                        if occupied_after_move & arrow_bit:
                            break
                        yield origin, destination, arrow


def _apply_move(me, blocked, move):
    origin, destination, arrow = move
    new_me = (me ^ (1 << origin)) | (1 << destination)
    new_blocked = blocked | (1 << arrow)
    return new_me, new_blocked


def _mobility(pieces, occupied):
    """Number of queen destinations available across all amazons."""
    total = 0
    remaining = pieces

    while remaining:
        bit = remaining & -remaining
        remaining ^= bit
        square = bit.bit_length() - 1

        for ray in RAYS[square]:
            for target in ray:
                if occupied & (1 << target):
                    break
                total += 1

    return total


def _territory(first, second, occupied):
    """
    Simultaneous king-distance Voronoi expansion.

    Returns:
      distance-based territory advantage,
      total reachable-area advantage.
    """
    empty = ALL ^ occupied

    frontier_first = first
    frontier_second = second
    visited_first = first
    visited_second = second
    unclaimed = empty
    territory = 0

    while frontier_first or frontier_second:
        next_first = _neighbors(frontier_first) & empty & ~visited_first
        next_second = _neighbors(frontier_second) & empty & ~visited_second

        if not next_first and not next_second:
            break

        reached_first = next_first & unclaimed
        reached_second = next_second & unclaimed

        territory += (reached_first & ~reached_second).bit_count()
        territory -= (reached_second & ~reached_first).bit_count()

        unclaimed &= ~(reached_first | reached_second)

        visited_first |= next_first
        visited_second |= next_second
        frontier_first = next_first
        frontier_second = next_second

    reachable_advantage = (
        (visited_first & empty).bit_count()
        - (visited_second & empty).bit_count()
    )
    return territory, reachable_advantage


def _central_score(pieces):
    result = 0
    while pieces:
        bit = pieces & -pieces
        pieces ^= bit
        result += CENTRAL_VALUE[bit.bit_length() - 1]
    return result


def _evaluate(first, second, blocked):
    """Evaluation from player-one's perspective."""
    occupied = first | second | blocked
    empty = ALL ^ occupied

    mobility_first = _mobility(first, occupied)
    mobility_second = _mobility(second, occupied)

    territory, reachable = _territory(first, second, occupied)

    local_first = (_neighbors(first) & empty).bit_count()
    local_second = (_neighbors(second) & empty).bit_count()

    central = _central_score(first) - _central_score(second)

    score = (
        48 * territory
        + 12 * reachable
        + 4 * (mobility_first - mobility_second)
        + 3 * (local_first - local_second)
        + 2 * central
    )

    return score, mobility_first, mobility_second


def _format_move(move):
    origin, destination, arrow = move
    fr, fc = divmod(origin, SIZE)
    tr, tc = divmod(destination, SIZE)
    ar, ac = divmod(arrow, SIZE)
    return f"{fr},{fc}:{tr},{tc}:{ar},{ac}"


# ---------------------------------------------------------------------------
# Exact late-game solver
# ---------------------------------------------------------------------------

class _SearchTimeout(Exception):
    pass


def _exact_result(current, opponent, blocked, deadline, memo):
    """
    Return +1 if the player to move can force a win, otherwise -1.

    The player identities are swapped recursively, so this result is always
    from the current player's perspective.
    """
    if time.perf_counter() >= deadline:
        raise _SearchTimeout

    key = (current, opponent, blocked)
    cached = memo.get(key)
    if cached is not None:
        return cached

    has_move = False

    for move in _generate_moves(current, opponent, blocked):
        has_move = True
        new_current, new_blocked = _apply_move(current, blocked, move)

        child = _exact_result(
            opponent, new_current, new_blocked, deadline, memo
        )

        if child < 0:
            memo[key] = 1
            return 1

    if not has_move:
        memo[key] = -1
        return -1

    memo[key] = -1
    return -1


# ---------------------------------------------------------------------------
# Main policy
# ---------------------------------------------------------------------------

def policy(board) -> str:
    start = time.perf_counter()
    hard_deadline = start + 0.965

    first = 0
    second = 0
    blocked = 0

    for r in range(SIZE):
        for c in range(SIZE):
            value = int(board[r, c])
            bit = 1 << (r * SIZE + c)
            if value == 1:
                first |= bit
            elif value == 2:
                second |= bit
            elif value == -1:
                blocked |= bit

    # Enumerate and statically evaluate every root move. The first generated
    # move is also a guaranteed legal fallback.
    roots = []

    for move in _generate_moves(first, second, blocked):
        new_first, new_blocked = _apply_move(first, blocked, move)
        score, own_mobility, opponent_mobility = _evaluate(
            new_first, second, new_blocked
        )

        # The opponent is now to move. No mobility means an immediate win.
        if opponent_mobility == 0:
            return _format_move(move)

        roots.append(
            [score, move, new_first, second, new_blocked]
        )

    # No legal move exists. The environment promises not to call policy in
    # this state; this remains a syntactically valid emergency return.
    if not roots:
        return "0,0:0,0:0,0"

    roots.sort(key=lambda item: item[0], reverse=True)
    fallback_move = roots[0][1]

    # Try exact solving in sufficiently small endgames.
    occupied = first | second | blocked
    empty_count = SQUARES - occupied.bit_count()

    if empty_count <= 7:
        exact_deadline = min(hard_deadline, start + 0.42)
        memo = {}

        try:
            for root in roots:
                _, move, new_first, new_second, new_blocked = root

                # Opponent is the next player. If the opponent's exact result
                # is losing, this root move is a proven win.
                opponent_result = _exact_result(
                    new_second,
                    new_first,
                    new_blocked,
                    exact_deadline,
                    memo,
                )
                if opponent_result < 0:
                    return _format_move(move)

        except _SearchTimeout:
            pass

    # -----------------------------------------------------------------------
    # Selective two-ply search:
    # For strong root candidates, inspect every legal opponent response.
    # -----------------------------------------------------------------------

    stage_two_deadline = min(hard_deadline, start + 0.71)
    root_candidate_count = min(48, len(roots))
    reply_beam = 14
    completed_two_ply = []

    for root_index in range(root_candidate_count):
        if time.perf_counter() >= stage_two_deadline:
            break

        root = roots[root_index]
        static_score, move, root_first, root_second, root_blocked = root

        replies = []
        worst_score = WIN_SCORE
        complete = True
        reply_count = 0

        for opponent_move in _generate_moves(
            root_second, root_first, root_blocked
        ):
            new_second, new_blocked = _apply_move(
                root_second, root_blocked, opponent_move
            )

            value, first_mobility, second_mobility = _evaluate(
                root_first, new_second, new_blocked
            )

            # Player one is next to move.
            if first_mobility == 0:
                value = -WIN_SCORE

            if value < worst_score:
                worst_score = value

            replies.append(
                (value, root_first, new_second, new_blocked)
            )

            reply_count += 1
            if (reply_count & 15) == 0:
                if time.perf_counter() >= stage_two_deadline:
                    complete = False
                    break

        if not complete:
            break

        # A missing reply would mean the root was an immediate win, which was
        # already handled during root generation.
        if not replies:
            return _format_move(move)

        replies.sort(key=lambda item: item[0])
        dangerous_replies = replies[:reply_beam]

        completed_two_ply.append(
            (worst_score, static_score, root, dangerous_replies)
        )

    if not completed_two_ply:
        return _format_move(fallback_move)

    completed_two_ply.sort(
        key=lambda item: (item[0], item[1]),
        reverse=True,
    )
    best_two_ply_move = completed_two_ply[0][2][1]

    # -----------------------------------------------------------------------
    # Selective third ply:
    # For the most promising roots, calculate our best answer to each of the
    # opponent's most dangerous replies.
    # -----------------------------------------------------------------------

    third_ply_candidates = min(10, len(completed_two_ply))
    completed_three_ply = []

    for candidate_index in range(third_ply_candidates):
        if time.perf_counter() >= hard_deadline:
            break

        two_score, static_score, root, replies = (
            completed_two_ply[candidate_index]
        )

        root_three_score = WIN_SCORE
        root_complete = True

        for reply_value, reply_first, reply_second, reply_blocked in replies:
            if time.perf_counter() >= hard_deadline:
                root_complete = False
                break

            best_answer = -WIN_SCORE
            found_answer = False
            answer_count = 0

            for answer in _generate_moves(
                reply_first, reply_second, reply_blocked
            ):
                found_answer = True
                new_first, new_blocked = _apply_move(
                    reply_first, reply_blocked, answer
                )

                value, first_mobility, second_mobility = _evaluate(
                    new_first, reply_second, new_blocked
                )

                # The opponent is next to move.
                if second_mobility == 0:
                    value = WIN_SCORE

                if value > best_answer:
                    best_answer = value

                answer_count += 1
                if (answer_count & 15) == 0:
                    if time.perf_counter() >= hard_deadline:
                        root_complete = False
                        break

            if not root_complete:
                break

            if not found_answer:
                best_answer = -WIN_SCORE

            if best_answer < root_three_score:
                root_three_score = best_answer

        if root_complete:
            completed_three_ply.append(
                (
                    root_three_score,
                    two_score,
                    static_score,
                    root[1],
                )
            )

    if completed_three_ply:
        completed_three_ply.sort(
            key=lambda item: (item[0], item[1], item[2]),
            reverse=True,
        )
        return _format_move(completed_three_ply[0][3])

    return _format_move(best_two_ply_move)
