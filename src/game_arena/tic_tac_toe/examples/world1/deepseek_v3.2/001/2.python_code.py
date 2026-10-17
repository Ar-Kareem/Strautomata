
def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Determine the optimal move for the AI player (represented by 1) on a 3x3 Tic Tac Toe board.
    
    Args:
        board: A 3x3 list of lists with values 0 (empty), 1 (AI), or -1 (opponent).
    
    Returns:
        A tuple (row, column) indicating the chosen move (indices 0–2).
    """
    # Helper function to check if a player has won
    def is_winner(b: list[list[int]], player: int) -> bool:
        # Check rows, columns, and diagonals
        for i in range(3):
            if all(b[i][j] == player for j in range(3)):
                return True
            if all(b[j][i] == player for j in range(3)):
                return True
        if all(b[i][i] == player for i in range(3)):
            return True
        if all(b[i][2 - i] == player for i in range(3)):
            return True
        return False

    # Helper function to check if the board is full
    def is_full(b: list[list[int]]) -> bool:
        return all(b[i][j] != 0 for i in range(3) for j in range(3))

    # Helper function to get list of empty cells
    def available_moves(b: list[list[int]]) -> list[tuple[int, int]]:
        return [(i, j) for i in range(3) for j in range(3) if b[i][j] == 0]

    # Minimax with alpha-beta pruning
    def minimax(b: list[list[int]], depth: int, alpha: float, beta: float, maximizing: bool) -> float:
        # Terminal state evaluations
        if is_winner(b, 1):
            return 10 - depth   # Prefer faster wins
        if is_winner(b, -1):
            return depth - 10   # Prefer slower losses
        if is_full(b):
            return 0

        if maximizing:
            max_eval = -float('inf')
            for i, j in available_moves(b):
                b[i][j] = 1
                eval = minimax(b, depth + 1, alpha, beta, False)
                b[i][j] = 0
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for i, j in available_moves(b):
                b[i][j] = -1
                eval = minimax(b, depth + 1, alpha, beta, True)
                b[i][j] = 0
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha:
                    break
            return min_eval

    # Main decision logic
    best_score = -float('inf')
    best_move = None
    moves = available_moves(board)
    # If no moves are available (should not happen in a valid game state), return a default move
    if not moves:
        return (0, 0)

    for i, j in moves:
        board[i][j] = 1
        score = minimax(board, 0, -float('inf'), float('inf'), False)
        board[i][j] = 0
        if score > best_score:
            best_score = score
            best_move = (i, j)

    return best_move
