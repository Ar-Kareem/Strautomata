
def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    # Create a 19x19 board representation (0: empty, 1: me, -1: opponent)
    board = [[0] * 19 for _ in range(19)]
    for r, c in me:
        board[r-1][c-1] = 1
    for r, c in opponent:
        board[r-1][c-1] = -1

    best_move = (0, 0)
    best_score = -float('inf')
    directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]  # Right, Down, Left, Up

    for r in range(19):
        for c in range(19):
            if board[r][c] != 0:  # Skip non-empty cells
                continue

            # Check if move is legal (has at least one liberty)
            liberties = 0
            for dr, dc in directions:
                nr, nc = r + dr, c + dc
                if 0 <= nr < 19 and 0 <= nc < 19 and board[nr][nc] == 0:
                    liberties += 1
            if liberties == 0:  # Illegal move (no liberties)
                continue

            # Check for captures (surrounds opponent stones)
            captures = 0
            for dr, dc in directions:
                nr, nc = r + dr, c + dc
                if 0 <= nr < 19 and 0 <= nc < 19 and board[nr][nc] == -1:
                    # Check if this stone has only one liberty (the current move)
                    stone_liberties = 0
                    for ddr, ddc in directions:
                        nrr, ncc = nr + ddr, nc + ddc
                        if 0 <= nrr < 19 and 0 <= ncc < 19 and board[nrr][ncc] == 0:
                            stone_liberties += 1
                    if stone_liberties == 1:  # Captures this stone
                        captures += 1

            # Calculate move score (captures + liberties)
            score = captures * 10 + liberties
            if score > best_score:
                best_score = score
                best_move = (r + 1, c + 1)  # Convert to 1-indexed

    return best_move
