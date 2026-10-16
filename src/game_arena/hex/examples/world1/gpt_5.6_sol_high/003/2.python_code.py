
import time
import random
from collections import deque

SIZE = 11
CELLS = SIZE * SIZE
INF = 10 ** 6
WIN_SCORE = 100000

# Hex neighbors for the coordinate system specified in the prompt.
_DIRECTIONS = (
    (0, -1), (0, 1),
    (-1, 0), (-1, 1),
    (1, 0), (1, -1),
)

NEIGHBORS = [[] for _ in range(CELLS)]
for r in range(SIZE):
    for c in range(SIZE):
        i = r * SIZE + c
        for dr, dc in _DIRECTIONS:
            rr, cc = r + dr, c + dc
            if 0 <= rr < SIZE and 0 <= cc < SIZE:
                NEIGHBORS[i].append(rr * SIZE + cc)

NEIGHBOR_SETS = [set(x) for x in NEIGHBORS]

# A bridge consists of two nonadjacent endpoints having exactly two
# common neighboring carrier cells.
BRIDGE_ENDPOINTS = [[] for _ in range(CELLS)]
CARRIER_RELATIONS = [[] for _ in range(CELLS)]

for a in range(CELLS):
    for b in range(a + 1, CELLS):
        if b in NEIGHBOR_SETS[a]:
            continue
        common = NEIGHBOR_SETS[a].intersection(NEIGHBOR_SETS[b])
        if len(common) == 2:
            x, y = tuple(common)
            BRIDGE_ENDPOINTS[a].append((b, x, y))
            BRIDGE_ENDPOINTS[b].append((a, x, y))
            CARRIER_RELATIONS[x].append((a, b, y))
            CARRIER_RELATIONS[y].append((a, b, x))

# Deterministic Zobrist values for transposition and candidate caches.
_rng = random.Random(0x48E85A11)
ZOBRIST = [
    (_rng.getrandbits(64), _rng.getrandbits(64))
    for _ in range(CELLS)
]


def policy(me: list[tuple[int, int]],
           opp: list[tuple[int, int]],
           color: str) -> tuple[int, int]:
    """
    Return a legal move on an 11x11 Hex board.

    Internally:
        1  = stones belonging to the caller
       -1  = opponent stones
        0  = empty
    """
    board = [0] * CELLS

    for r, c in me:
        if 0 <= r < SIZE and 0 <= c < SIZE:
            board[r * SIZE + c] = 1

    for r, c in opp:
        if 0 <= r < SIZE and 0 <= c < SIZE:
            i = r * SIZE + c
            if board[i] == 0:
                board[i] = -1

    empties = [i for i, value in enumerate(board) if value == 0]

    # A full board cannot legally occur when this function is asked to move.
    # This keeps the function total for malformed external inputs.
    if not empties:
        return (0, 0)

    # Always maintain a legal center-biased fallback.
    fallback = min(
        empties,
        key=lambda i: (
            abs(i // SIZE - SIZE // 2) + abs(i % SIZE - SIZE // 2),
            i
        )
    )

    if len(empties) == CELLS:
        return (SIZE // 2, SIZE // 2)

    root_color = 'b' if color == 'b' else 'w'
    colors = {
        1: root_color,
        -1: 'w' if root_color == 'b' else 'b'
    }

    start_time = time.perf_counter()
    deadline = start_time + 0.88

    initial_hash = 0
    for i, value in enumerate(board):
        if value == 1:
            initial_hash ^= ZOBRIST[i][0]
        elif value == -1:
            initial_hash ^= ZOBRIST[i][1]

    candidate_cache = {}
    transposition = {}

    def side_cells(player, first_side):
        player_color = colors[player]
        if player_color == 'b':
            row = 0 if first_side else SIZE - 1
            return [row * SIZE + c for c in range(SIZE)]
        col = 0 if first_side else SIZE - 1
        return [r * SIZE + col for r in range(SIZE)]

    def virtual_edge_stones(player, first_side):
        """
        Stones securely connected to a side through two empty edge carriers.
        """
        result = []
        player_color = colors[player]

        if player_color == 'b':
            if first_side:
                # (1,c) bridges to top via (0,c) and (0,c+1).
                for c in range(SIZE - 1):
                    stone = SIZE + c
                    a, b = c, c + 1
                    if (board[stone] == player and
                            board[a] == 0 and board[b] == 0):
                        result.append(stone)
            else:
                # (9,c) bridges to bottom via (10,c) and (10,c-1).
                for c in range(1, SIZE):
                    stone = (SIZE - 2) * SIZE + c
                    a = (SIZE - 1) * SIZE + c
                    b = (SIZE - 1) * SIZE + c - 1
                    if (board[stone] == player and
                            board[a] == 0 and board[b] == 0):
                        result.append(stone)
        else:
            if first_side:
                # (r,1) bridges to left via (r,0) and (r+1,0).
                for r in range(SIZE - 1):
                    stone = r * SIZE + 1
                    a = r * SIZE
                    b = (r + 1) * SIZE
                    if (board[stone] == player and
                            board[a] == 0 and board[b] == 0):
                        result.append(stone)
            else:
                # (r,9) bridges to right via (r,10) and (r-1,10).
                for r in range(1, SIZE):
                    stone = r * SIZE + SIZE - 2
                    a = r * SIZE + SIZE - 1
                    b = (r - 1) * SIZE + SIZE - 1
                    if (board[stone] == player and
                            board[a] == 0 and board[b] == 0):
                        result.append(stone)

        return result

    def dijkstra(player, first_side, virtual):
        """
        0-1 shortest path:
          own stones cost 0,
          empty cells cost 1,
          opponent stones are impassable.

        If virtual=True, intact bridge endpoints are connected at zero cost.
        """
        dist = [INF] * CELLS
        q = deque()

        for i in side_cells(player, first_side):
            if board[i] == -player:
                continue
            cost = 0 if board[i] == player else 1
            if cost < dist[i]:
                dist[i] = cost
                if cost == 0:
                    q.appendleft(i)
                else:
                    q.append(i)

        if virtual:
            for i in virtual_edge_stones(player, first_side):
                if dist[i] > 0:
                    dist[i] = 0
                    q.appendleft(i)

        while q:
            u = q.popleft()
            du = dist[u]

            for v in NEIGHBORS[u]:
                if board[v] == -player:
                    continue
                weight = 0 if board[v] == player else 1
                nd = du + weight
                if nd < dist[v]:
                    dist[v] = nd
                    if weight == 0:
                        q.appendleft(v)
                    else:
                        q.append(v)

            if virtual and board[u] == player:
                for v, carrier_a, carrier_b in BRIDGE_ENDPOINTS[u]:
                    if (board[v] == player and
                            board[carrier_a] == 0 and
                            board[carrier_b] == 0 and
                            du < dist[v]):
                        dist[v] = du
                        q.appendleft(v)

        return dist

    def connection_data(player, virtual=False):
        forward = dijkstra(player, True, virtual)
        backward = dijkstra(player, False, virtual)
        target = side_cells(player, False)
        distance = min(forward[i] for i in target)
        return forward, backward, distance

    def shortest_distance(player, virtual=False):
        dist = dijkstra(player, True, virtual)
        return min(dist[i] for i in side_cells(player, False))

    def has_win(player):
        player_color = colors[player]
        q = deque()
        seen = [False] * CELLS

        if player_color == 'b':
            for c in range(SIZE):
                i = c
                if board[i] == player:
                    seen[i] = True
                    q.append(i)

            while q:
                u = q.popleft()
                if u // SIZE == SIZE - 1:
                    return True
                for v in NEIGHBORS[u]:
                    if not seen[v] and board[v] == player:
                        seen[v] = True
                        q.append(v)
        else:
            for r in range(SIZE):
                i = r * SIZE
                if board[i] == player:
                    seen[i] = True
                    q.append(i)

            while q:
                u = q.popleft()
                if u % SIZE == SIZE - 1:
                    return True
                for v in NEIGHBORS[u]:
                    if not seen[v] and board[v] == player:
                        seen[v] = True
                        q.append(v)

        return False

    def immediate_cells(forward, backward, distance):
        if distance != 1:
            return []
        result = []
        for i in range(CELLS):
            if board[i] != 0:
                continue
            if forward[i] >= INF or backward[i] >= INF:
                continue
            if forward[i] + backward[i] - 1 == 1:
                result.append(i)
        return result

    def ordered_candidates(player, board_hash):
        key = (board_hash, player)
        cached = candidate_cache.get(key)
        if cached is not None:
            return cached

        if time.perf_counter() >= deadline:
            raise TimeoutError

        own_f, own_b, own_d = connection_data(player, False)
        opp_f, opp_b, opp_d = connection_data(-player, False)

        wins = immediate_cells(own_f, own_b, own_d)
        if wins:
            wins.sort(key=lambda i: (
                abs(i // SIZE - 5) + abs(i % SIZE - 5),
                i
            ))
            result = tuple(wins)
            candidate_cache[key] = result
            return result

        threats = immediate_cells(opp_f, opp_b, opp_d)
        if threats:
            threats.sort(key=lambda i: (
                abs(i // SIZE - 5) + abs(i % SIZE - 5),
                i
            ))
            result = tuple(threats)
            candidate_cache[key] = result
            return result

        scored = []
        player_color = colors[player]

        for i in range(CELLS):
            if board[i] != 0:
                continue

            r, c = divmod(i, SIZE)
            score = 0

            # Proximity to each player's best current connection corridor.
            if own_f[i] < INF and own_b[i] < INF:
                through = own_f[i] + own_b[i] - 1
                excess = max(0, through - own_d)
                score += max(0, 68 - 11 * excess)

            if opp_f[i] < INF and opp_b[i] < INF:
                through = opp_f[i] + opp_b[i] - 1
                excess = max(0, through - opp_d)
                score += max(0, 72 - 11 * excess)

            friendly = [v for v in NEIGHBORS[i] if board[v] == player]
            enemies = [v for v in NEIGHBORS[i] if board[v] == -player]

            score += 9 * len(friendly)
            score += 8 * len(enemies)

            # Reward moves joining separated friendly groups.
            separated_pairs = 0
            for x in range(len(friendly)):
                for y in range(x + 1, len(friendly)):
                    if friendly[y] not in NEIGHBOR_SETS[friendly[x]]:
                        separated_pairs += 1
            score += min(30, 13 * separated_pairs)

            # Blocking a cell which could join enemy groups is also valuable.
            enemy_pairs = 0
            for x in range(len(enemies)):
                for y in range(x + 1, len(enemies)):
                    if enemies[y] not in NEIGHBOR_SETS[enemies[x]]:
                        enemy_pairs += 1
            score += min(25, 11 * enemy_pairs)

            # Creating a new bridge extension.
            for other, a, b in BRIDGE_ENDPOINTS[i]:
                if board[other] == player and board[a] == 0 and board[b] == 0:
                    score += 18
                elif (board[other] == -player and
                      board[a] == 0 and board[b] == 0):
                    score += 11

            # Bridge-carrier tactics.
            for endpoint_a, endpoint_b, other_carrier in CARRIER_RELATIONS[i]:
                va = board[endpoint_a]
                vb = board[endpoint_b]
                vo = board[other_carrier]

                if va == player and vb == player:
                    if vo == -player:
                        # Last remaining carrier of our attacked bridge.
                        score += 58
                    elif vo == 0:
                        score += 3
                elif va == -player and vb == -player:
                    if vo == player:
                        # Remove the opponent's last bridge carrier.
                        score += 48
                    elif vo == 0:
                        score += 9

            # Prefer the center line perpendicular to the desired direction.
            if player_color == 'b':
                score += 3 * (5 - abs(c - 5))
            else:
                score += 3 * (5 - abs(r - 5))

            # Mild general center preference.
            score -= abs(r - 5) + abs(c - 5)

            # Deterministic tie breaker.
            scored.append((score, -abs(r - 5) - abs(c - 5), -i, i))

        scored.sort(reverse=True)
        result = tuple(item[3] for item in scored)
        candidate_cache[key] = result
        return result

    def normalized_distance(value):
        return 35 if value >= INF else value

    def evaluate(turn):
        my_raw = normalized_distance(shortest_distance(1, False))
        op_raw = normalized_distance(shortest_distance(-1, False))

        # An immediate win for the side to move is nearly terminal.
        if turn == 1 and my_raw == 1:
            return 30000
        if turn == -1 and op_raw == 1:
            return -30000

        my_virtual = normalized_distance(shortest_distance(1, True))
        op_virtual = normalized_distance(shortest_distance(-1, True))

        score = 125 * (op_virtual - my_virtual)
        score += 30 * (op_raw - my_raw)

        if my_raw == 1:
            score += 260
        if op_raw == 1:
            score -= 260

        # Small tempo adjustment.
        score += 12 if turn == 1 else -12
        return score

    def branch_limit(depth, empty_count):
        if empty_count <= 13:
            return empty_count
        if depth >= 4:
            return 8
        if depth == 3:
            return 10
        return 13

    def alphabeta(depth, turn, alpha, beta, board_hash, empty_count):
        if time.perf_counter() >= deadline:
            raise TimeoutError

        if depth <= 0 or empty_count == 0:
            return evaluate(turn)

        original_alpha = alpha
        original_beta = beta
        tt_key = (board_hash, turn, depth)
        entry = transposition.get(tt_key)
        tt_move = None

        if entry is not None:
            value, flag, tt_move = entry
            if flag == 0:
                return value
            if flag == 1:
                alpha = max(alpha, value)
            else:
                beta = min(beta, value)
            if alpha >= beta:
                return value

        candidates = list(ordered_candidates(turn, board_hash))
        limit = branch_limit(depth, empty_count)
        candidates = candidates[:limit]

        if tt_move is not None and tt_move in candidates:
            candidates.remove(tt_move)
            candidates.insert(0, tt_move)

        if not candidates:
            return evaluate(turn)

        best_move = candidates[0]

        if turn == 1:
            best = -WIN_SCORE * 2

            for move in candidates:
                board[move] = 1
                new_hash = board_hash ^ ZOBRIST[move][0]
                try:
                    if has_win(1):
                        value = WIN_SCORE + depth
                    else:
                        value = alphabeta(
                            depth - 1, -1, alpha, beta,
                            new_hash, empty_count - 1
                        )
                finally:
                    board[move] = 0

                if value > best:
                    best = value
                    best_move = move
                alpha = max(alpha, best)
                if alpha >= beta:
                    break
        else:
            best = WIN_SCORE * 2

            for move in candidates:
                board[move] = -1
                new_hash = board_hash ^ ZOBRIST[move][1]
                try:
                    if has_win(-1):
                        value = -WIN_SCORE - depth
                    else:
                        value = alphabeta(
                            depth - 1, 1, alpha, beta,
                            new_hash, empty_count - 1
                        )
                finally:
                    board[move] = 0

                if value < best:
                    best = value
                    best_move = move
                beta = min(beta, best)
                if alpha >= beta:
                    break

        if best <= original_alpha:
            flag = 2  # Upper bound
        elif best >= original_beta:
            flag = 1  # Lower bound
        else:
            flag = 0  # Exact

        transposition[tt_key] = (best, flag, best_move)
        return best

    def root_search(depth, board_hash, empty_count):
        candidates = list(ordered_candidates(1, board_hash))

        if empty_count <= 14:
            limit = empty_count
        elif depth <= 1:
            limit = 26
        elif depth == 2:
            limit = 22
        else:
            limit = 20

        candidates = candidates[:limit]
        if not candidates:
            return fallback, -WIN_SCORE * 2

        best_move = candidates[0]
        best_value = -WIN_SCORE * 2
        alpha = -WIN_SCORE * 2
        beta = WIN_SCORE * 2

        for move in candidates:
            if time.perf_counter() >= deadline:
                raise TimeoutError

            board[move] = 1
            new_hash = board_hash ^ ZOBRIST[move][0]
            try:
                if has_win(1):
                    value = WIN_SCORE + depth
                else:
                    value = alphabeta(
                        depth - 1, -1, alpha, beta,
                        new_hash, empty_count - 1
                    )
            finally:
                board[move] = 0

            if value > best_value:
                best_value = value
                best_move = move

            alpha = max(alpha, best_value)

        return best_move, best_value

    best_completed = fallback

    try:
        initial_order = ordered_candidates(1, initial_hash)
        if initial_order:
            best_completed = initial_order[0]

        # Iterative deepening ensures there is always a completed answer.
        max_depth = min(7, len(empties))
        for depth in range(1, max_depth + 1):
            move, value = root_search(depth, initial_hash, len(empties))
            best_completed = move

            # No deeper search is needed after a proven immediate win.
            if value >= WIN_SCORE:
                break

            if time.perf_counter() >= deadline:
                break

    except TimeoutError:
        pass
    except Exception:
        # Preserve the guaranteed legal fallback on any unexpected platform
        # or malformed-input issue.
        pass

    if 0 <= best_completed < CELLS and board[best_completed] == 0:
        return divmod(best_completed, SIZE)

    return divmod(fallback, SIZE)
