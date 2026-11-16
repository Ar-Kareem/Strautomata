
def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Select the next legal move (row, col) on a 10x10 Battleship board.
    The board contains:
        0  – unknown (not yet fired)
       -1  – miss
        1  – hit
    Returns a tuple of integers (row, col) with board[row][col] == 0.
    """
    # Ensure we have a 10x10 board
    if not board or len(board) != 10 or any(len(row) != 10 for row in board):
        raise ValueError("Board must be a 10x10 matrix")

    # Collect unknown cells and hit cells from the current knowledge
    unknown = []
    hits = []
    for r in range(10):
        for c in range(10):
            v = board[r][c]
            if v == 0:
                unknown.append((r, c))
            elif v == 1:
                hits.append((r, c))

    # If there is no unknown cell left, we cannot make a legal move.
    # In practice this situation should not occur before the game ends.
    if not unknown:
        # Return a safe fallback (won't be legal but avoids crashing)
        return (0, 0)

    # Helper to compute minimal Manhattan distance to any known hit
    def nearest_distance(pos):
        row, col = pos
        return min(abs(row - hit_r) + abs(col - hit_c) for hit_r, hit_c in hits)

    # Distance‑based selection: choose the unknown cell with smallest distance.
    # Ties are resolved by lexicographic (row, then column) order.
    best_pos = None
    min_dist = 100  # larger than any possible Manhattan distance on a 10×10 board
    for pos in unknown:
        d = nearest_distance(pos)
        if d < min_dist:
            min_dist = d
            best_pos = pos
        elif d == min_dist:
            # Tie‑break by row then column (natural row‑major order)
            if pos < best_pos:
                best_pos = pos

    if best_pos is None:
        # Should never happen, but fallback to systematic scanning
        best_pos = min(unknown)

    return best_pos
