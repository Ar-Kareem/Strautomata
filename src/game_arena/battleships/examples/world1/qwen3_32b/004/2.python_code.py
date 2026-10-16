
def policy(board):
    # Check for adjacent candidates to existing hits
    candidates = []
    for row in range(10):
        for col in range(10):
            if board[row][col] == 1:
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    new_r, new_c = row + dr, col + dc
                    if 0 <= new_r < 10 and 0 <= new_c < 10:
                        if board[new_r][new_c] == 0:
                            candidates.append((new_r, new_c))
    # Deduplicate candidates
    candidates = list(dict.fromkeys(candidates))
    if candidates:
        return candidates[0]

    # Precompute probability grid for search phase
    if not hasattr(policy, 'prob_grid'):
        ship_lengths = [5, 4, 3, 3, 2]
        policy.prob_grid = [[0] * 10 for _ in range(10)]
        for r in range(10):
            for c in range(10):
                for L in ship_lengths:
                    # Horizontal possibilities
                    min_sc = max(0, c - L + 1)
                    max_sc = min(10 - L, c)
                    horizontal = max(0, max_sc - min_sc + 1)
                    # Vertical possibilities
                    min_sr = max(0, r - L + 1)
                    max_sr = min(10 - L, r)
                    vertical = max(0, max_sr - min_sr + 1)
                    policy.prob_grid[r][c] += horizontal + vertical

    # Select next move from untested cells based on probability grid
    possible_moves = [
        (r, c) for r in range(10) for c in range(10)
        if board[r][c] == 0
    ]
    possible_moves.sort(key=lambda pos: policy.prob_grid[pos[0]][pos[1]], reverse=True)
    return possible_moves[0]
