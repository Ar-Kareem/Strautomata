
from collections import deque
from time import perf_counter

SIZE = 11
CELLS = SIZE * SIZE
INF = 10 ** 6

_NEIGHBORS = [[] for _ in range(CELLS)]

for r in range(SIZE):
    for c in range(SIZE):
        a = r * SIZE + c
        for dr, dc in ((0, -1), (0, 1), (-1, 0),
                       (-1, 1), (1, -1), (1, 0)):
            rr, cc = r + dr, c + dc
            if 0 <= rr < SIZE and 0 <= cc < SIZE:
                _NEIGHBORS[a].append(rr * SIZE + cc)

# A bridge pair consists of two nonadjacent cells having exactly two
# common neighbors. If both endpoints are ours and neither carrier is
# occupied by the opponent, the connection is strategically secure.
_BRIDGE_LINKS = [[] for _ in range(CELLS)]
_BRIDGE_PAIRS = []
_CARRIER_PAIRS = [[] for _ in range(CELLS)]

_neighbor_sets = [set(x) for x in _NEIGHBORS]

for a in range(CELLS):
    for b in range(a + 1, CELLS):
        if b in _neighbor_sets[a]:
            continue
        common = _neighbor_sets[a].intersection(_neighbor_sets[b])
        if len(common) == 2:
            c1, c2 = tuple(common)
            pair_index = len(_BRIDGE_PAIRS)
            _BRIDGE_PAIRS.append((a, b, c1, c2))
            _BRIDGE_LINKS[a].append((b, c1, c2))
            _BRIDGE_LINKS[b].append((a, c1, c2))
            _CARRIER_PAIRS[c1].append(pair_index)
            _CARRIER_PAIRS[c2].append(pair_index)


def _connected(board, player, vertical):
    """Return whether player has an actual, non-virtual connection."""
    seen = [False] * CELLS
    q = deque()

    if vertical:
        for c in range(SIZE):
            x = c
            if board[x] == player:
                seen[x] = True
                q.append(x)

        while q:
            x = q.popleft()
            if x // SIZE == SIZE - 1:
                return True
            for y in _NEIGHBORS[x]:
                if not seen[y] and board[y] == player:
                    seen[y] = True
                    q.append(y)
    else:
        for r in range(SIZE):
            x = r * SIZE
            if board[x] == player:
                seen[x] = True
                q.append(x)

        while q:
            x = q.popleft()
            if x % SIZE == SIZE - 1:
                return True
            for y in _NEIGHBORS[x]:
                if not seen[y] and board[y] == player:
                    seen[y] = True
                    q.append(y)

    return False


def _side_reach(board, player, vertical, first_side):
    """Player stones connected to one of the player's target sides."""
    seen = [False] * CELLS
    q = deque()

    if vertical:
        r = 0 if first_side else SIZE - 1
        start = r * SIZE
        for c in range(SIZE):
            x = start + c
            if board[x] == player:
                seen[x] = True
                q.append(x)
    else:
        c = 0 if first_side else SIZE - 1
        for r in range(SIZE):
            x = r * SIZE + c
            if board[x] == player:
                seen[x] = True
                q.append(x)

    while q:
        x = q.popleft()
        for y in _NEIGHBORS[x]:
            if not seen[y] and board[y] == player:
                seen[y] = True
                q.append(y)

    return seen


def _winning_moves(board, player, vertical):
    """
    Find every empty cell that would make an actual connection for player.
    This uses side-connected components and is much faster than testing
    every empty cell with a separate flood fill.
    """
    side_a = _side_reach(board, player, vertical, True)
    side_b = _side_reach(board, player, vertical, False)
    result = []

    for x in range(CELLS):
        if board[x] != 0:
            continue

        r, c = divmod(x, SIZE)

        if vertical:
            touches_a = (r == 0)
            touches_b = (r == SIZE - 1)
        else:
            touches_a = (c == 0)
            touches_b = (c == SIZE - 1)

        if not touches_a or not touches_b:
            for y in _NEIGHBORS[x]:
                if side_a[y]:
                    touches_a = True
                if side_b[y]:
                    touches_b = True
                if touches_a and touches_b:
                    break

        if touches_a and touches_b:
            result.append(x)

    return result


def _connection_distance(board, player, vertical):
    """
    Number of empty cells on a cheapest connection path.

    Own stones cost zero, empty cells cost one, and opponent stones are
    blocked. Secure bridge endpoints are joined by zero-cost virtual edges.
    """
    dist = [INF] * CELLS
    q = deque()

    if vertical:
        starts = range(SIZE)
    else:
        starts = range(0, CELLS, SIZE)

    for x in starts:
        v = board[x]
        if v == -player:
            continue
        cost = 0 if v == player else 1
        if cost < dist[x]:
            dist[x] = cost
            if cost == 0:
                q.appendleft(x)
            else:
                q.append(x)

    while q:
        x = q.popleft()
        dx = dist[x]

        for y in _NEIGHBORS[x]:
            value = board[y]
            if value == -player:
                continue
            step = 0 if value == player else 1
            nd = dx + step
            if nd < dist[y]:
                dist[y] = nd
                if step == 0:
                    q.appendleft(y)
                else:
                    q.append(y)

        if board[x] == player:
            for y, c1, c2 in _BRIDGE_LINKS[x]:
                if (board[y] == player and
                        board[c1] != -player and
                        board[c2] != -player and
                        dx < dist[y]):
                    dist[y] = dx
                    q.appendleft(y)

    if vertical:
        return min(dist[(SIZE - 1) * SIZE:])
    return min(dist[r * SIZE + SIZE - 1] for r in range(SIZE))


def _positional_score(board, me_vertical):
    score = 0

    for x, value in enumerate(board):
        if value == 0:
            continue

        r, c = divmod(x, SIZE)
        vertical = me_vertical if value == 1 else not me_vertical
        axis = c if vertical else r
        centrality = 6 - abs(axis - 5)

        if value == 1:
            score += centrality
        else:
            score -= centrality

        for y in _NEIGHBORS[x]:
            if y > x and board[y] == value:
                score += 2 if value == 1 else -2

    for a, b, c1, c2 in _BRIDGE_PAIRS:
        if board[a] == 1 and board[b] == 1:
            if board[c1] != -1 and board[c2] != -1:
                score += 4
        elif board[a] == -1 and board[b] == -1:
            if board[c1] != 1 and board[c2] != 1:
                score -= 4

    return score


def _evaluate(board, me_vertical):
    my_dist = _connection_distance(board, 1, me_vertical)
    opp_dist = _connection_distance(board, -1, not me_vertical)

    if my_dist >= INF:
        return -800000
    if opp_dist >= INF:
        return 800000

    score = 1000 * (opp_dist - my_dist)

    # With equal path lengths, the root player generally benefits from
    # having the next move at minimax leaves.
    if my_dist <= opp_dist:
        score += 35

    score += _positional_score(board, me_vertical)
    return score


def _quick_rank(board, x, player, vertical):
    """Cheap ordering score used before more expensive position searches."""
    r, c = divmod(x, SIZE)
    axis = c if vertical else r
    score = 12 - 2 * abs(axis - 5)

    own_adj = 0
    enemy_adj = 0
    for y in _NEIGHBORS[x]:
        if board[y] == player:
            own_adj += 1
        elif board[y] == -player:
            enemy_adj += 1

    score += 9 * own_adj + 5 * enemy_adj

    if vertical and (r == 0 or r == SIZE - 1):
        score += 3
    elif not vertical and (c == 0 or c == SIZE - 1):
        score += 3

    # Reward repairing an invaded bridge and disturbing enemy bridges.
    for pair_index in _CARRIER_PAIRS[x]:
        a, b, c1, c2 = _BRIDGE_PAIRS[pair_index]
        other = c2 if x == c1 else c1

        if board[a] == player and board[b] == player:
            if board[other] == -player:
                score += 90
            elif board[other] == 0:
                score += 12

        if board[a] == -player and board[b] == -player:
            if board[other] == 0:
                score += 18

    return score


def _leaf_evaluate(board, me_vertical):
    """
    Tactical evaluation after one move by each side; it is our turn again.
    """
    my_wins = _winning_moves(board, 1, me_vertical)
    if my_wins:
        return 300000 + len(my_wins)

    opp_wins = _winning_moves(board, -1, not me_vertical)
    if len(opp_wins) >= 2:
        return -250000 - len(opp_wins)

    value = _evaluate(board, me_vertical)
    if len(opp_wins) == 1:
        value -= 25000
    return value


class _SearchTimeout(Exception):
    pass


def _exact_endgame(board, empties, me_vertical, deadline):
    """
    Exact alternating game-tree search for small endgames.
    Returns a forced winning move for us, or None.
    """
    cache = {}
    calls = [0]

    def can_force(player):
        calls[0] += 1
        if (calls[0] & 63) == 0 and perf_counter() >= deadline:
            raise _SearchTimeout

        key = (tuple(board), player)
        known = cache.get(key)
        if known is not None:
            return known

        vertical = me_vertical if player == 1 else not me_vertical

        if _winning_moves(board, player, vertical):
            cache[key] = True
            return True

        moves = [x for x in range(CELLS) if board[x] == 0]
        if not moves:
            cache[key] = False
            return False

        moves.sort(
            key=lambda x: _quick_rank(board, x, player, vertical),
            reverse=True
        )

        for x in moves:
            board[x] = player
            opponent_can_force = can_force(-player)
            board[x] = 0

            if not opponent_can_force:
                cache[key] = True
                return True

        cache[key] = False
        return False

    ordered = sorted(
        empties,
        key=lambda x: _quick_rank(board, x, 1, me_vertical),
        reverse=True
    )

    try:
        for x in ordered:
            if perf_counter() >= deadline:
                raise _SearchTimeout
            board[x] = 1
            opponent_can_force = can_force(-1)
            board[x] = 0
            if not opponent_can_force:
                return x
    except _SearchTimeout:
        for x in empties:
            if board[x] != 0:
                board[x] = 0
        return None

    return None


def policy(me: list[tuple[int, int]],
           opp: list[tuple[int, int]],
           color: str) -> tuple[int, int]:
    start_time = perf_counter()
    deadline = start_time + 0.88
    me_vertical = (color == 'b')

    board = [0] * CELLS

    for r, c in me:
        if 0 <= r < SIZE and 0 <= c < SIZE:
            board[r * SIZE + c] = 1

    for r, c in opp:
        if 0 <= r < SIZE and 0 <= c < SIZE:
            board[r * SIZE + c] = -1

    empties = [x for x in range(CELLS) if board[x] == 0]

    # Defensive fallback for every return path.
    if not empties:
        return (0, 0)

    fallback = empties[0]

    if len(empties) == CELLS:
        return (5, 5)

    # 1. Win immediately whenever possible.
    my_immediate = _winning_moves(board, 1, me_vertical)
    if my_immediate:
        best = max(
            my_immediate,
            key=lambda x: _quick_rank(board, x, 1, me_vertical)
        )
        return divmod(best, SIZE)

    # 2. An opponent immediate win must be occupied now.
    opp_immediate = _winning_moves(board, -1, not me_vertical)
    if opp_immediate:
        if len(opp_immediate) == 1:
            return divmod(opp_immediate[0], SIZE)

        best = max(
            opp_immediate,
            key=lambda x: _quick_rank(board, x, 1, me_vertical)
        )
        return divmod(best, SIZE)

    # 3. Look for a move creating two distinct immediate wins.
    fork_moves = []
    for x in empties:
        board[x] = 1
        future_wins = _winning_moves(board, 1, me_vertical)
        board[x] = 0
        if len(future_wins) >= 2:
            fork_moves.append(x)

    if fork_moves:
        best = max(
            fork_moves,
            key=lambda x: _quick_rank(board, x, 1, me_vertical)
        )
        return divmod(best, SIZE)

    # 4. Solve sufficiently small endgames exactly, but reserve time for
    # the strategic fallback if the exact search does not finish.
    if len(empties) <= 11:
        exact_deadline = min(deadline, start_time + 0.47)
        exact_move = _exact_endgame(
            board, empties, me_vertical, exact_deadline
        )
        if exact_move is not None and board[exact_move] == 0:
            return divmod(exact_move, SIZE)

    # 5. One-ply strategic ranking of every move.
    ranked = []
    for x in empties:
        board[x] = 1
        value = _evaluate(board, me_vertical)
        value += _quick_rank(board, x, 1, me_vertical)
        board[x] = 0
        ranked.append((value, x))

    ranked.sort(reverse=True)
    fallback = ranked[0][1]

    remaining = len(empties)
    if remaining > 90:
        candidate_count = 16
    elif remaining > 50:
        candidate_count = 22
    elif remaining > 25:
        candidate_count = 27
    else:
        candidate_count = min(34, remaining)

    candidates = ranked[:candidate_count]

    # 6. Two-ply minimax. Each candidate is judged by the opponent's
    # strongest legal response, including tactical threat creation.
    best_move = fallback
    best_pair = None

    for root_value, x in candidates:
        if perf_counter() >= deadline:
            break

        board[x] = 1
        responses = [y for y in empties if y != x]

        responses.sort(
            key=lambda y: _quick_rank(
                board, y, -1, not me_vertical
            ),
            reverse=True
        )

        worst_value = INF
        complete = True
        pruned = False

        if not responses:
            worst_value = _evaluate(board, me_vertical)
        else:
            for index, y in enumerate(responses):
                if (index & 7) == 0 and perf_counter() >= deadline:
                    complete = False
                    break

                board[y] = -1
                leaf_value = _leaf_evaluate(board, me_vertical)
                board[y] = 0

                if leaf_value < worst_value:
                    worst_value = leaf_value

                if best_pair is not None and worst_value < best_pair[0]:
                    pruned = True
                    break

        board[x] = 0

        if not complete:
            break
        if pruned:
            continue

        pair = (worst_value, root_value)
        if best_pair is None or pair > best_pair:
            best_pair = pair
            best_move = x

    if 0 <= best_move < CELLS and board[best_move] == 0:
        return divmod(best_move, SIZE)

    # Absolute legality safeguard.
    for x in range(CELLS):
        if board[x] == 0:
            return divmod(x, SIZE)

    return divmod(fallback, SIZE)
