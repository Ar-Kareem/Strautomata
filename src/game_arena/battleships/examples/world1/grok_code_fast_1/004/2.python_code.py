
def policy(board: list[list[int]]) -> tuple[int, int]:
    # Collect all unique target moves: unknown cells adjacent to hits
    target_moves = set()
    for r in range(10):
        for c in range(10):
            if board[r][c] == 1:
                # Check adjacent cells
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < 10 and 0 <= nc < 10 and board[nr][nc] == 0:
                        target_moves.add((nr, nc))
    
    # If target moves exist, pick the first one (deterministic order)
    if target_moves:
        return min(target_moves)  # min gives top-left preference
    
    # Hunt mode: Checkerboard pattern, even sum first, then odd sum
    for parity in [0, 1]:
        for r in range(10):
            for c in range(10):
                if board[r][c] == 0 and (r + c) % 2 == parity:
                    return (r, c)
    
    # Should never reach here if board is valid, but return (0,0) as fallback
    return (0, 0)
