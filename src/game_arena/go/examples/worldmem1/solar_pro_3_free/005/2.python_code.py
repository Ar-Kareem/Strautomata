
import numpy as np
import random

def policy(me: list[tuple[int, int]],
           opponent: list[tuple[int, int]],
           memory: dict) -> tuple[tuple[int, int], dict]:
    """
    Return the next Go move (row, col) in 1‑based coordinates, or (0, 0) to pass.
    The policy simulates each empty point, captures opponent groups that would be
    removed, checks for suicide, and selects the point with the highest heuristic
    score.
    """
    # Convert coordinates to zero‑based indices
    me_coords = [(r - 1, c - 1) for r, c in me]
    opp_coords = [(r - 1, c - 1) for r, c in opponent]

    # Board representation: 0 = empty, 1 = me, 2 = opponent
    board = np.zeros((19, 19), dtype=int)
    my_grid = np.zeros((19, 19), dtype=int)
    opp_grid = np.zeros((19, 19), dtype=int)

    for r, c in me_coords:
        my_grid[r, c] = 1
    for r, c in opp_coords:
        opp_grid[r, c] = 2
    board = my_grid + opp_grid   # quick way to see occupied cells

    # Orthogonal directions (up, down, left, right)
    dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    legal_moves = []

    for row in range(19):
        for col in range(19):
            if board[row, col] != 0:       # not empty → ignore
                continue

            # Simulate placing our stone at (row, col)
            simulated = board.copy()
            simulated[row, col] = 1   # our new stone

            # Find opponent stones that touch the empty point
            adj_opp = [
                (row + dr, col + dc)
                for dr, dc in dirs
                if 0 <= row + dr < 19 and 0 <= col + dc < 19
                and opp_grid[row + dr, col + dc] == 2
            ]

            # Detect opponent groups that could be captured
            opp_visited = np.zeros_like(opp_grid, dtype=bool)
            captured_cells = []          # coordinates that will disappear
            captured_stones = 0

            for start in adj_opp:
                if opp_visited[start[0], start[1]]:
                    continue

                # BFS of the whole opponent group reachable from this start
                group_cells = [(start[0], start[1])]
                opp_visited[start[0], start[1]] = True
                queue = [(start[0], start[1])]
                liberties = 0

                while queue:
                    cr, cc = queue.pop()
                    # Count empty neighbours (liberties) in the simulated board
                    for dr, dc in dirs:
                        nr, nc = cr + dr, cc + dc
                        if 0 <= nr < 19 and 0 <= nc < 19 and simulated[nr, nc] == 0:
                            liberties += 1

                    # Expand to orthogonal opponent neighbours
                    for dr, dc in dirs:
                        nr, nc = cr + dr, cc + dc
                        if (0 <= nr < 19 and 0 <= nc < 19 and
                            simulated[nr, nc] == 2 and
                            not opp_visited[nr, nc]):
                            opp_visited[nr, nc] = True
                            queue.append((nr, nc))
                            group_cells.append((nr, nc))

                # If liberties == 0, this group would be captured
                if liberties == 0:
                    captured_cells.extend(group_cells)
                    captured_stones += len(group_cells)
                    # Remove captured stones from the simulated board
                    captured_arr = np.array(captured_cells)
                    simulated[captured_arr[:, 0], captured_arr[:, 1]] = 0

            # Count liberties of the stone we just placed
            new_liberties = sum(
                simulated[row + dr, col + dc] == 0
                for dr, dc in dirs
            )
            if new_liberties == 0:
                # Suicide – illegal, skip
                continue

            # Adjacent own stones (group cohesion)
            own_adjacent = sum(
                simulated[row + dr, col + dc] == 1
                for dr, dc in dirs
            )

            # Central weight (Manhattan distance)
            center = (8, 8)            # zero‑based index for (9,9)
            dist = abs(row - center[0]) + abs(col - center[1])
            center_weight = 1.0 / (dist + 1)

            # Build the heuristic score
            score = (
                captured_stones * 100               # killing opponent stones
                + new_liberties * 5                 # safety
                + int(center_weight * 500)          # be central
                + own_adjacent * 10                 # connect to own groups
            )

            legal_moves.append((score, (row + 1, col + 1)))   # back to 1‑based

    # Choose the best move (random tie‑breaker)
    if not legal_moves:
        move = (0, 0)   # pass
    else:
        max_score = max(score for score, _ in legal_moves)
        best_candidates = [move for score, move in legal_moves if score == max_score]
        move = random.choice(best_candidates)

    # Return the selected move together with the unchanged memory dict
    return move, memory
