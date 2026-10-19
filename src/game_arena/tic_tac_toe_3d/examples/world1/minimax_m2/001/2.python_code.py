
# Precompute all winning lines for 3D Tic Tac Toe
winning_lines = []

# Straight lines along x-axis (depth)
for y in range(3):
    for z in range(3):
        winning_lines.append([(0, y, z), (1, y, z), (2, y, z)])

# Straight lines along y-axis (row)
for x in range(3):
    for z in range(3):
        winning_lines.append([(x, 0, z), (x, 1, z), (x, 2, z)])

# Straight lines along z-axis (column)
for x in range(3):
    for y in range(3):
        winning_lines.append([(x, y, 0), (x, y, 1), (x, y, 2)])

# Face diagonals for x-faces (perpendicular to x-axis)
for x in range(3):
    winning_lines.append([(x, 0, 0), (x, 1, 1), (x, 2, 2)])
    winning_lines.append([(x, 0, 2), (x, 1, 1), (x, 2, 0)])

# Face diagonals for y-faces (perpendicular to y-axis)
for y in range(3):
    winning_lines.append([(0, y, 0), (1, y, 1), (2, y, 2)])
    winning_lines.append([(0, y, 2), (1, y, 1), (2, y, 0)])

# Face diagonals for z-faces (perpendicular to z-axis)
for z in range(3):
    winning_lines.append([(0, 0, z), (1, 1, z), (2, 2, z)])
    winning_lines.append([(0, 2, z), (1, 1, z), (2, 0, z)])

# Space diagonals
winning_lines.append([(0, 0, 0), (1, 1, 1), (2, 2, 2)])
winning_lines.append([(0, 0, 2), (1, 1, 1), (2, 2, 0)])
winning_lines.append([(0, 2, 0), (1, 1, 1), (2, 0, 2)])
winning_lines.append([(0, 2, 2), (1, 1, 1), (2, 0, 0)])

# Helper function to get all empty cells
def get_empty_cells(board):
    empty_cells = []
    for x in range(3):
        for y in range(3):
            for z in range(3):
                if board[x][y][z] == 0:
                    empty_cells.append((x, y, z))
    return empty_cells

# Check if a player has won
def has_won(board, player):
    for line in winning_lines:
        cells = [board[x][y][z] for (x, y, z) in line]
        if all(cell == player for cell in cells):
            return True
    return False

# Check if the game is over
def is_terminal(board):
    return has_won(board, 1) or has_won(board, -1) or not get_empty_cells(board)

# Evaluate the board state
def evaluate(board):
    if has_won(board, 1):
        return 1000
    if has_won(board, -1):
        return -1000
    if not get_empty_cells(board):
        return 0
    
    score = 0
    for line in winning_lines:
        cells = [board[x][y][z] for (x, y, z) in line]
        n1 = cells.count(1)
        n2 = cells.count(-1)
        ne = cells.count(0)
        if n1 == 2 and ne == 1:
            score += 10
        elif n2 == 2 and ne == 1:
            score -= 10
        elif n1 == 1 and ne == 2:
            score += 1
        elif n2 == 1 and ne == 2:
            score -= 1
    return score

# Minimax with alpha-beta pruning
def minimax(board, depth, alpha, beta, maximizing_player):
    if depth == 0 or is_terminal(board):
        return evaluate(board)
    
    if maximizing_player:
        max_eval = -float('inf')
        for move in get_empty_cells(board):
            x, y, z = move
            board[x][y][z] = 1  # Make move for player 1
            eval_score = minimax(board, depth-1, alpha, beta, False)
            board[x][y][z] = 0  # Revert move
            if eval_score > max_eval:
                max_eval = eval_score
            if eval_score > alpha:
                alpha = eval_score
            if beta <= alpha:
                break  # Prune
        return max_eval
    else:
        min_eval = float('inf')
        for move in get_empty_cells(board):
            x, y, z = move
            board[x][y][z] = -1  # Make move for player -1
            eval_score = minimax(board, depth-1, alpha, beta, True)
            board[x][y][z] = 0  # Revert move
            if eval_score < min_eval:
                min_eval = eval_score
            if eval_score < beta:
                beta = eval_score
            if beta <= alpha:
                break  # Prune
        return min_eval

# Main policy function
def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    empty_cells = get_empty_cells(board)
    if not empty_cells:
        # If no empty cells, return a default move (should not happen in practice)
        return (0, 0, 0)
    
    best_move = None
    best_score = -float('inf')
    
    for move in empty_cells:
        x, y, z = move
        board[x][y][z] = 1  # Make the move
        score = minimax(board, depth=4, alpha=-float('inf'), beta=float('inf'), maximizing_player=False)
        board[x][y][z] = 0  # Revert move
        
        if score > best_score:
            best_score = score
            best_move = move
    
    return best_move
