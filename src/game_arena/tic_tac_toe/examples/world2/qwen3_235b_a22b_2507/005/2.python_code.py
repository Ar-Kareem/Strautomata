
def policy(board: list[list[int]]) -> tuple[int, int]:
    # Define all possible lines (rows, columns, diagonals) of length 4
    LINES = [
        # Rows
        [(0,0), (0,1), (0,2), (0,3)],
        [(1,0), (1,1), (1,2), (1,3)],
        [(2,0), (2,1), (2,2), (2,3)],
        [(3,0), (3,1), (3,2), (3,3)],
        # Columns
        [(0,0), (1,0), (2,0), (3,0)],
        [(0,1), (1,1), (2,1), (3,1)],
        [(0,2), (1,2), (2,2), (3,2)],
        [(0,3), (1,3), (2,3), (3,3)],
        # Diagonals
        [(0,0), (1,1), (2,2), (3,3)],
        [(0,3), (1,2), (2,1), (3,0)]
    ]
    
    def is_winner(board, player):
        for line in LINES:
            if all(board[r][c] == player for r, c in line):
                return True
        return False
    
    def get_empty_cells(board):
        cells = []
        for r in range(4):
            for c in range(4):
                if board[r][c] == 0:
                    cells.append((r, c))
        return cells
    
    def evaluate_line(values):
        # values: list of 4 integers from a line
        if 1 in values and -1 in values:
            return 0
        if all(v == 1 for v in values):
            return 10000  # win for me
        if all(v == -1 for v in values):
            return -10000  # win for opponent
        count_1 = values.count(1)
        count_m1 = values.count(-1)
        if count_1 > 0:
            return {1: 1, 2: 10, 3: 100}[count_1]
        elif count_m1 > 0:
            return {1: -1, 2: -10, 3: -100}[count_m1]
        return 0
    
    def evaluate(board):
        score = 0
        for line in LINES:
            values = [board[r][c] for (r, c) in line]
            score += evaluate_line(values)
        return score
    
    def alphabeta(board, depth, alpha, beta, maximizing):
        # Check for terminal states or depth limit
        if depth == 0:
            return evaluate(board)
        
        # Check if the game is won
        if is_winner(board, 1):
            return 10000
        if is_winner(board, -1):
            return -10000
        
        empty_cells = get_empty_cells(board)
        if not empty_cells:
            return 0  # draw
        
        if maximizing:
            value = -float('inf')
            for r, c in empty_cells:
                board[r][c] = 1
                score = alphabeta(board, depth - 1, alpha, beta, False)
                board[r][c] = 0
                value = max(value, score)
                alpha = max(alpha, value)
                if alpha >= beta:
                    break  # beta cutoff
            return value
        else:
            value = float('inf')
            for r, c in empty_cells:
                board[r][c] = -1
                score = alphabeta(board, depth - 1, alpha, beta, True)
                board[r][c] = 0
                value = min(value, score)
                beta = min(beta, value)
                if alpha >= beta:
                    break  # alpha cutoff
            return value
    
    # Get all empty cells
    empty_cells = get_empty_cells(board)
    
    # If no moves, return first cell (should not happen)
    if not empty_cells:
        return (0, 0)
    
    # 1. Check if I can win in one move
    for r, c in empty_cells:
        board[r][c] = 1
        if is_winner(board, 1):
            board[r][c] = 0
            return (r, c)
        board[r][c] = 0
    
    # 2. Check if opponent can win in one move -> block
    for r, c in empty_cells:
        board[r][c] = -1
        if is_winner(board, -1):
            board[r][c] = 0
            return (r, c)
        board[r][c] = 0
    
    # 3. Otherwise, use minimax with alpha-beta pruning
    MAX_DEPTH = 8
    best_move = None
    best_score = -float('inf')
    
    # Order moves: try center first for efficiency
    # Prefer center: (1,1), (1,2), (2,1), (2,2), then others
    center_cells = [(1,1), (1,2), (2,1), (2,2)]
    edge_cells = [cell for cell in empty_cells if cell not in center_cells]
    ordered_cells = center_cells + edge_cells
    
    for r, c in empty_cells:
        board[r][c] = 1
        score = alphabeta(board, MAX_DEPTH - 1, -float('inf'), float('inf'), False)
        board[r][c] = 0
        
        if score > best_score:
            best_score = score
            best_move = (r, c)
    
    # If no best move found (unlikely), return first empty
    if best_move is None:
        best_move = empty_cells[0]
    
    return best_move
