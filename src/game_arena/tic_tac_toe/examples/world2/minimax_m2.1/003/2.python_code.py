
# Precompute winning lines for a 4x4 Tic Tac Toe board
LINES = []
# Horizontal lines (rows)
for i in range(4):
    LINES.append([(i, j) for j in range(4)])
# Vertical lines (columns)
for j in range(4):
    LINES.append([(i, j) for i in range(4)])
# Diagonal lines
LINES.append([(i, i) for i in range(4)])  # Main diagonal
LINES.append([(i, 3-i) for i in range(4)])  # Anti-diagonal

def is_winning_move(board, player, move):
    """Check if placing player's mark at move would win the game."""
    i, j = move
    for line in LINES:
        if move in line:
            count = 0
            for (x, y) in line:
                if (x, y) == move:
                    count += 1
                else:
                    if board[x][y] == player:
                        count += 1
            if count == 4:
                return True
    return False

def policy(board):
    """Determine the next move for the current board state."""
    # Check for winning moves
    for i in range(4):
        for j in range(4):
            if board[i][j] == 0:
                if is_winning_move(board, 1, (i, j)):
                    return (i, j)
    
    # Check for blocking moves
    block_move = None
    for i in range(4):
        for j in range(4):
            if board[i][j] == 0:
                if is_winning_move(board, -1, (i, j)):
                    if block_move is None:
                        block_move = (i, j)
    if block_move is not None:
        return block_move
    
    # Use scoring heuristic for remaining moves
    best_score = -1
    best_move = None
    for i in range(4):
        for j in range(4):
            if board[i][j] == 0:
                score = 0
                for line in LINES:
                    if (i, j) in line:
                        has_opponent = False
                        for (x, y) in line:
                            if (x, y) == (i, j):
                                continue
                            if board[x][y] == -1:
                                has_opponent = True
                                break
                        if has_opponent:
                            continue
                        our_count = 0
                        for (x, y) in line:
                            if (x, y) == (i, j):
                                continue
                            if board[x][y] == 1:
                                our_count += 1
                        score += (our_count + 1) ** 2
                if score > best_score:
                    best_score = score
                    best_move = (i, j)
    
    return best_move
