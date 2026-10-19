
def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Implements a Tic Tac Toe policy using the minimax algorithm with alpha-beta pruning.
    The AI always plays as player 1 (value 1) and assumes the opponent is -1.
    It evaluates all possible moves and selects the optimal one to maximize the score,
    where a win for AI is +1, a loss is -1, and a draw is 0.
    """
    
    def is_winner(board, player):
        # Check rows, columns, and diagonals for a win
        for i in range(3):
            if all(board[i][j] == player for j in range(3)):  # Row
                return True
            if all(board[j][i] == player for j in range(3)):  # Column
                return True
        if all(board[i][i] == player for i in range(3)):  # Diagonal
            return True
        if all(board[i][2 - i] == player for i in range(3)):  # Anti-diagonal
            return True
        return False
    
    def game_over(board):
        # Game is over if there's a winner or no empty spots
        return is_winner(board, 1) or is_winner(board, -1) or all(all(cell != 0 for cell in row) for row in board)
    
    def evaluate(board):
        # Evaluate the board: +1 for AI win, -1 for opponent win, 0 for draw
        if is_winner(board, 1):
            return 1
        if is_winner(board, -1):
            return -1
        return 0
    
    def minimax(board, depth, is_maximizing, alpha=-float('inf'), beta=float('inf')):
        if game_over(board):
            return evaluate(board)
        
        if is_maximizing:
            max_eval = -float('inf')
            for i in range(3):
                for j in range(3):
                    if board[i][j] == 0:
                        board[i][j] = 1  # AI's move
                        eval = minimax(board, depth + 1, False, alpha, beta)
                        board[i][j] = 0  # Undo move
                        max_eval = max(max_eval, eval)
                        alpha = max(alpha, eval)
                        if beta <= alpha:
                            break  # Alpha-beta pruning
                else:
                    continue
                break
            return max_eval
        else:
            min_eval = float('inf')
            for i in range(3):
                for j in range(3):
                    if board[i][j] == 0:
                        board[i][j] = -1  # Opponent's move
                        eval = minimax(board, depth + 1, True, alpha, beta)
                        board[i][j] = 0  # Undo move
                        min_eval = min(min_eval, eval)
                        beta = min(beta, eval)
                        if beta <= alpha:
                            break  # Alpha-beta pruning
                else:
                    continue
                break
            return min_eval
    
    # Find the best move for AI
    best_val = -float('inf')
    best_move = None
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                board[i][j] = 1  # Try AI's move
                move_val = minimax(board, 0, False)  # Opponent's turn next
                board[i][j] = 0  # Undo
                if move_val > best_val:
                    best_val = move_val
                    best_move = (i, j)
    
    return best_move
