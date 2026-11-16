
def policy(board: list[list[int]]) -> tuple[int, int]:
    for r in range(10):
        for c in range(10):
            if board[r][c] == 1:
                # Check adjacent cells in order: up, left, right, down
                if r > 0 and board[r-1][c] == 0:
                    return (r-1, c)
                if c > 0 and board[r][c-1] == 0:
                    return (r, c-1)
                if c < 9 and board[r][c+1] == 0:
                    return (r, c+1)
                if r < 9 and board[r+1][c] == 0:
                    return (r+1, c)
    # No hits or no adjacent unknowns, fallback to row-major
    for r in range(10):
        for c in range(10):
            if board[r][c] == 0:
                return (r, c)
    # Fallback in case all cells are targeted (unlikely but safe)
    return (0, 0)
