
def policy(board: list[list[int]]) -> tuple[int, int]:
    ROWS, COLS = 10, 10

    # Collect all current hits
    hits = []
    for x in range(ROWS):
        for y in range(COLS):
            if board[x][y] == 1:
                hits.append((x, y))

    # Exploration phase: if no hits, proceed with row-major order
    if not hits:
        for row in range(ROWS):
            for col in range(COLS):
                if board[row][col] == 0:
                    return (row, col)
        return (0, 0)  # Should never reach here as there must be unshot cells

    # Collect adjacent unshot cells to current hits
    candidates = []
    for x, y in hits:
        # Check all four possible neighboring cells
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < ROWS and 0 <= ny < COLS and board[nx][ny] == 0:
                candidates.append((nx, ny))

    # Remove duplicates and maintain order
    seen = set()
    unique_candidates = []
    for cell in candidates:
        if cell not in seen:
            seen[cell] = True
            unique_candidates.append(cell)

    # Return the first candidate in row-major order
    if unique_candidates:
        unique_candidates.sort()
        return unique_candidates[0]

    # Fallback exploration if no candidates found (unlikely)
    for x in range(ROWS):
        for y in range(COLS):
            if board[x][y] == 0:
                return (x, y)
    return (0, 0)
