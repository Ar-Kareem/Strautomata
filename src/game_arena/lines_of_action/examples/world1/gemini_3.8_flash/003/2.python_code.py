
import time
from collections import deque

def policy(board) -> str:
    start_time = time.time()
    time_limit = 0.85  # Reserve margin within 1.0 second limit

    # Convert board input to a flat list for faster indexed access
    # board[r][c] -> flat[r * 8 + c]
    b = [0] * 64
    for r in range(8):
        for c in range(8):
            b[r * 8 + c] = board[r][c]

    def is_connected(state, player):
        pieces = [i for i in range(64) if state[i] == player]
        n = len(pieces)
        if n <= 1:
            return True

        # BFS to check 8-connectivity
        visited = set()
        queue = deque([pieces[0]])
        visited.add(pieces[0])

        while queue:
            curr = queue.popleft()
            cr, cc = curr // 8, curr % 8
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == 0 and dc == 0:
                        continue
                    nr, nc = cr + dr, cc + dc
                    if 0 <= nr < 8 and 0 <= nc < 8:
                        idx = nr * 8 + nc
                        if state[idx] == player and idx not in visited:
                            visited.add(idx)
                            queue.append(idx)

        return len(visited) == n

    def get_moves(state, player):
        moves = []
        enemy = -player

        # Precompute line counts for efficiency
        # Rows
        row_counts = [0] * 8
        col_counts = [0] * 8
        # Diagonals: d1 = r - c + 7 (0..14), d2 = r + c (0..14)
        diag1_counts = [0] * 15
        diag2_counts = [0] * 15

        player_pieces = []
        for r in range(8):
            for c in range(8):
                val = state[r * 8 + c]
                if val != 0:
                    row_counts[r] += 1
                    col_counts[c] += 1
                    diag1_counts[r - c + 7] += 1
                    diag2_counts[r + c] += 1
                if val == player:
                    player_pieces.append((r, c))

        # Directions: (dr, dc, count_type)
        # 0: horiz, 1: vert, 2: diag1 (\), 3: diag2 (/)
        for r, c in player_pieces:
            directions = (
                (0, 1, row_counts[r]),
                (0, -1, row_counts[r]),
                (1, 0, col_counts[c]),
                (-1, 0, col_counts[c]),
                (1, 1, diag1_counts[r - c + 7]),
                (-1, -1, diag1_counts[r - c + 7]),
                (1, -1, diag2_counts[r + c]),
                (-1, 1, diag2_counts[r + c])
            )

            for dr, dc, k in directions:
                nr = r + k * dr
                nc = c + k * dc
                if not (0 <= nr < 8 and 0 <= nc < 8):
                    continue

                dest_idx = nr * 8 + nc
                if state[dest_idx] == player:
                    continue  # Friendly piece at destination

                # Check intermediate path for enemy obstacles
                blocked = False
                for step in range(1, k):
                    if state[(r + step * dr) * 8 + (c + step * dc)] == enemy:
                        blocked = True
                        break
                if not blocked:
                    moves.append((r, c, nr, nc, dest_idx))

        return moves

    def evaluate(state):
        p1_pieces = []
        p2_pieces = []
        for idx in range(64):
            v = state[idx]
            if v == 1:
                p1_pieces.append((idx // 8, idx % 8))
            elif v == -1:
                p2_pieces.append((idx // 8, idx % 8))

        n1 = len(p1_pieces)
        n2 = len(p2_pieces)

        # Terminal evaluations
        conn1 = is_connected(state, 1)
        conn2 = is_connected(state, -1)
        if conn1 and not conn2:
            return 100000.0
        if conn2 and not conn1:
            return -100000.0
        if conn1 and conn2:
            return 100000.0  # Moving player preference

        # Center of mass and concentration for player 1
        r_sum1 = sum(r for r, c in p1_pieces)
        c_sum1 = sum(c for r, c in p1_pieces)
        mr1, mc1 = r_sum1 / n1, c_sum1 / n1
        dist1 = sum(max(abs(r - mr1), abs(c - mc1)) + 0.5 * (abs(r - mr1) + abs(c - mc1)) for r, c in p1_pieces)

        # Center of mass and concentration for player -1
        r_sum2 = sum(r for r, c in p2_pieces)
        c_sum2 = sum(c for r, c in p2_pieces)
        mr2, mc2 = r_sum2 / n2, c_sum2 / n2
        dist2 = sum(max(abs(r - mr2), abs(c - mc2)) + 0.5 * (abs(r - mr2) + abs(c - mc2)) for r, c in p2_pieces)

        # Component count heuristics
        def component_penalty(player, pieces):
            visited = set()
            components = 0
            largest_comp = 0
            for r, c in pieces:
                idx = r * 8 + c
                if idx not in visited:
                    components += 1
                    q = deque([idx])
                    visited.add(idx)
                    comp_size = 0
                    while q:
                        curr = q.popleft()
                        comp_size += 1
                        cr, cc = curr // 8, curr % 8
                        for dr in (-1, 0, 1):
                            for dc in (-1, 0, 1):
                                if dr == 0 and dc == 0:
                                    continue
                                nr, nc = cr + dr, cc + dc
                                if 0 <= nr < 8 and 0 <= nc < 8:
                                    nidx = nr * 8 + nc
                                    if state[nidx] == player and nidx not in visited:
                                        visited.add(nidx)
                                        q.append(nidx)
                    if comp_size > largest_comp:
                        largest_comp = comp_size
            return components, largest_comp

        comps1, max_comp1 = component_penalty(1, p1_pieces)
        comps2, max_comp2 = component_penalty(-1, p2_pieces)

        score = (
            -15.0 * dist1
            + 15.0 * dist2
            - 25.0 * comps1
            + 25.0 * comps2
            + 10.0 * max_comp1
            - 10.0 * max_comp2
        )
        return score

    all_legal_moves = get_moves(b, 1)
    if not all_legal_moves:
        return "0,0:0,0"

    # Fast win check
    for r, c, nr, nc, dest_idx in all_legal_moves:
        orig = b[dest_idx]
        b[dest_idx] = 1
        b[r * 8 + c] = 0
        if is_connected(b, 1):
            b[r * 8 + c] = 1
            b[dest_idx] = orig
            return f"{r},{c}:{nr},{nc}"
        b[r * 8 + c] = 1
        b[dest_idx] = orig

    # Move scoring for ordering
    def score_move(m, player):
        r, c, nr, nc, dest_idx = m
        score = 0
        # Captures are valuable
        if b[dest_idx] == -player:
            score += 100
        # Centralizing moves
        center_dist_before = abs(r - 3.5) + abs(c - 3.5)
        center_dist_after = abs(nr - 3.5) + abs(nc - 3.5)
        score += (center_dist_before - center_dist_after) * 5
        return score

    all_legal_moves.sort(key=lambda m: score_move(m, 1), reverse=True)
    best_move = all_legal_moves[0]
    tt = {}

    def alphabeta(state, depth, alpha, beta, player):
        if time.time() - start_time > time_limit:
            raise TimeoutError()

        # Terminal conditions
        conn1 = is_connected(state, 1)
        conn2 = is_connected(state, -1)
        if conn1 or conn2:
            if player == 1:
                return (100000.0 - (5 - depth)) if conn1 else (-100000.0 + (5 - depth))
            else:
                return (100000.0 - (5 - depth)) if conn2 else (-100000.0 + (5 - depth))

        if depth == 0:
            return evaluate(state) if player == 1 else -evaluate(state)

        key = (tuple(state), player)
        if key in tt:
            entry_depth, entry_val = tt[key]
            if entry_depth >= depth:
                return entry_val

        moves = get_moves(state, player)
        if not moves:
            return -50000.0

        moves.sort(key=lambda m: score_move(m, player), reverse=True)

        value = -float('inf')
        for r, c, nr, nc, dest_idx in moves:
            orig = state[dest_idx]
            state[dest_idx] = player
            state[r * 8 + c] = 0

            child_val = -alphabeta(state, depth - 1, -beta, -alpha, -player)

            state[r * 8 + c] = player
            state[dest_idx] = orig

            if child_val > value:
                value = child_val
            alpha = max(alpha, value)
            if alpha >= beta:
                break

        tt[key] = (depth, value)
        return value

    # Iterative deepening
    max_depth = 4
    for depth in range(1, max_depth + 1):
        if time.time() - start_time > time_limit:
            break
        current_best = None
        current_val = -float('inf')
        alpha = -float('inf')
        beta = float('inf')

        try:
            for m in all_legal_moves:
                r, c, nr, nc, dest_idx = m
                orig = b[dest_idx]
                b[dest_idx] = 1
                b[r * 8 + c] = 0

                val = -alphabeta(b, depth - 1, -beta, -alpha, -1)

                b[r * 8 + c] = 1
                b[dest_idx] = orig

                if val > current_val:
                    current_val = val
                    current_best = m
                alpha = max(alpha, current_val)

            if current_best is not None:
                best_move = current_best
                # Order best move first in next iteration
                all_legal_moves.remove(best_move)
                all_legal_moves.insert(0, best_move)

            if current_val >= 90000:
                break  # Win found
        except TimeoutError:
            break

    r, c, nr, nc, _ = best_move
    return f"{r},{c}:{nr},{nc}"
