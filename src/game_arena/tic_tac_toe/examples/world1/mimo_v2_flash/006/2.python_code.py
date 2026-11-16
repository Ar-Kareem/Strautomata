
def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Unbeatable Tic-Tac-Toe AI using Minimax with Alpha-Beta pruning.
    Returns the optimal move for the current board state.
    """
    import math
    
    def is_winner(board, player):
        """Check if player has won the game."""
        # Check rows and columns
        for i in range(3):
            if all(board[i][j] == player for j in range(3)):
                return True
            if all(board[j][i] == player for j in range(3)):
                return True
        # Check diagonals
        if all(board[i][i] == player for i in range(3)):
            return True
        if all(board[i][2-i] == player for i in range(3)):
            return True
        return False
    
    def is_full(board):
        """Check if board is full (draw)."""
        for row in board:
            for cell in row:
                if cell == 0:
                    return False
        return True
    
    def get_empty_cells(board):
        """Return list of empty cell coordinates."""
        cells = []
        for i in range(3):
            for j in range(3):
                if board[i][j] == 0:
                    cells.append((i, j))
        return cells
    
    def minimax(board, depth, is_maximizing, alpha, beta):
        """
        Minimax with Alpha-Beta pruning.
        Returns score for the current board state.
        """
        # Check terminal states
        if is_winner(board, 1):
            return 10 - depth  # Prefer quicker wins
        if is_winner(board, -1):
            return depth - 10  # Prefer slower losses
        if is_full(board):
            return 0  # Draw
        
        empty_cells = get_empty_cells(board)
        
        if is_maximizing:
            max_eval = -math.inf
            for cell in empty_cells:
                i, j = cell
                board[i][j] = 1  # AI move
                eval_score = minimax(board, depth + 1, False, alpha, beta)
                board[i][j] = 0  # Undo move
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break  # Alpha-beta pruning
            return max_eval
        else:
            min_eval = math.inf
            for cell in empty_cells:
                i, j = cell
                board[i][j] = -1  # Opponent move
                eval_score = minimax(board, depth + 1, True, alpha, beta)
                board[i][j] = 0  # Undo move
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break  # Alpha-beta pruning
            return min_eval
    
    # Find optimal move
    best_score = -math.inf
    best_move = None
    empty_cells = get_empty_cells(board)
    
    # Handle empty board (optimal opening move: center)
    if len(empty_cells) == 9:
        return (1, 1)
    
    for cell in empty_cells:
        i, j = cell
        board[i][j] = 1  # AI move
        score = minimax(board, 0, False, -math.inf, math.inf)
        board[i][j] = 0  # Undo move
        
        if score > best_score:
            best_score = score
            best_move = cell
    
    return best_move
