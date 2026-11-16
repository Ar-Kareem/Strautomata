
def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Optimal Tic Tac Toe policy using minimax with alpha-beta pruning.
    Returns the best move (row, col) for player 1 (our pieces).
    
    Strategy:
    1. Win immediately if possible
    2. Block opponent's winning move
    3. Use minimax to find optimal move for neutral positions
    """
    # Check for empty board - take center as best opening
    if all(cell == 0 for row in board for cell in row):
        return (1, 1)
    
    # Check for immediate winning move
    for move in get_available_moves(board):
        test_board = [row[:] for row in board]
        test_board[move[0]][move[1]] = 1
        if check_winner(test_board) == 1:
            return move
    
    # Check if opponent can win next move and block
    for move in get_available_moves(board):
        test_board = [row[:] for row in board]
        test_board[move[0]][move[1]] = -1
        if check_winner(test_board) == -1:
            return move
    
    # Use minimax to find the best move
    best_move = None
    best_score = float('-inf')
    
    for move in get_available_moves(board):
        test_board = [row[:] for row in board]
        test_board[move[0]][move[1]] = 1
        score = minimax(test_board, 0, False, float('-inf'), float('inf'))
        
        if score > best_score:
            best_score = score
            best_move = move
    
    return best_move

def get_available_moves(board: list[list[int]]) -> list[tuple[int, int]]:
    """Return all empty cell positions."""
    moves = []
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                moves.append((i, j))
    return moves

def check_winner(board: list[list[int]]) -> int:
    """Check for winner: 1 if player 1 wins, -1 if player 2 wins, 0 for draw/none."""
    # Check rows
    for i in range(3):
        if board[i][0] != 0 and board[i][0] == board[i][1] == board[i][2]:
            return board[i][0]
    
    # Check columns
    for j in range(3):
        if board[0][j] != 0 and board[0][j] == board[1][j] == board[2][j]:
            return board[0][j]
    
    # Check diagonals
    if board[0][0] != 0 and board[0][0] == board[1][1] == board[2][2]:
        return board[0][0]
    if board[0][2] != 0 and board[0][2] == board[1][1] == board[2][0]:
        return board[0][2]
    
    # Check for draw
    if all(cell != 0 for row in board for cell in row):
        return 0
    
    return 0  # No winner yet

def minimax(board: list[list[int]], depth: int, is_maximizing: bool, alpha: float, beta: float) -> int:
    """Minimax algorithm with alpha-beta pruning."""
    winner = check_winner(board)
    
    if winner == 1:
        return 10 - depth
    elif winner == -1:
        return depth - 10
    elif winner == 0:
        return 0
    
    if is_maximizing:
        max_eval = float('-inf')
        for move in get_available_moves(board):
            board[move[0]][move[1]] = 1
            eval_score = minimax(board, depth + 1, False, alpha, beta)
            board[move[0]][move[1]] = 0
            max_eval = max(max_eval, eval_score)
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = float('inf')
        for move in get_available_moves(board):
            board[move[0]][move[1]] = -1
            eval_score = minimax(board, depth + 1, True, alpha, beta)
            board[move[0]][move[1]] = 0
            min_eval = min(min_eval, eval_score)
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        return min_eval
