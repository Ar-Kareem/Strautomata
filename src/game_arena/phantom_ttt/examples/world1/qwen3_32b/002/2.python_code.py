
def policy(board: list[list[int]], legal_moves: list[int]) -> int:
    # Define all possible lines (rows, columns, and diagonals)
    lines = [
        [(0,0), (0,1), (0,2)],
        [(1,0), (1,1), (1,2)],
        [(2,0), (2,1), (2,2)],
        [(0,0), (1,0), (2,0)],
        [(0,1), (1,1), (2,1)],
        [(0,2), (1,2), (2,2)],
        [(0,0), (1,1), (2,2)],
        [(0,2), (1,1), (2,0)]
    ]

    # Step 1: Check for immediate win
    for move in legal_moves:
        r, c = move // 3, move % 3
        # Check if placing at (r,c) would complete a row
        if all(board[r][y] == 1 or y == c for y in range(3)) and all(board[r][y] == 1 for y in range(3) if y != c):
            return (r, c)
        # Check if placing at (r,c) would complete a column
        if all(board[x][c] == 1 or x == r for x in range(3)) and all(board[x][c] == 1 for x in range(3) if x != r):
            return (r, c)
        # Check if placing at (r,c) would complete a diagonal
        if r == c and all(board[i][i] == 1 or i == r for i in range(3)) and all(board[i][i] == 1 for i in range(3) if i != r):
            return (r, c)
        if r + c == 2 and all(board[i][2-i] == 1 or i == r for i in range(3)) and all(board[i][2-i] == 1 for i in range(3) if i != r):
            return (r, c)

    # Step 2: Block opponent's potential win (block all-zero lines)
    block_candidates = []
    for line in lines:
        all_zero = True
        for (x, y) in line:
            if board[x][y] != 0:
                all_zero = False
                break
        if all_zero:
            for (x, y) in line:
                block_candidates.append((x, y))
    for candidate in block_candidates:
        r, c = candidate
        move_index = r * 3 + c
        if move_index in legal_moves:
            return (r, c)

    # Step 3: Choose best future move based on position score and line potential
    best_score = -1
    best_move = None
    for move in legal_moves:
        r, c = move // 3, move % 3
        score = 0
        for line in lines:
            if (r, c) in line:
                line_has_only_zerors = True
                for (x, y) in line:
                    if board[x][y] != 0:
                        line_has_only_zerors = False
                        break
                if line_has_only_zerors:
                    score += 1
        # Add position-based priority
        if (r, c) == (1, 1):
            score += 2  # center gets highest priority
        elif (r, c) in [(0,0), (0,2), (2,0), (2,2)]:
            score += 1  # corners get second highest
        if score > best_score or (score == best_score and best_move is None):
            best_score = score
            best_move = (r, c)

    return best_move
