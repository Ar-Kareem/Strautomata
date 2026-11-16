
def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Returns the optimal move for the player represented by 1
    on the provided 3x3 tic-tac-toe board.
    """
    
    def check_winner(b: list[list[int]]) -> int:
        """
        Checks the board for a winner.
        Returns 1 if player 1 wins, -1 if player -1 wins, 0 otherwise.
        """
        # Check rows
        for row in b:
            if row[0] == row[1] == row[2] != 0:
                return row[0]
        
        # Check columns
        for col in range(3):
            if b[0][col] == b[1][col] == b[2][col] != 0:
                return b[0][col]
        
        # Check diagonals
        if b[0][0] == b[1][1] == b[2][2] != 0:
            return b[0][0]
        if b[0][2] == b[1][1] == b[2][0] != 0:
            return b[0][2]
            
        return 0

    def get_available_moves(b: list[list[int]]) -> list[tuple[int, int]]:
        """Returns a list of (row, col) tuples for empty cells."""
        moves = []
        for r in range(3):
            for c in range(3):
                if b[r][c] == 0:
                    moves.append((r, c))
        return moves

    def minimax(b: list[list[int]], depth: int, is_maximizing: bool) -> int:
        """
        Recursive Minimax algorithm.
        is_maximizing: True if it's the AI's (1) turn, False if opponent's (-1).
        """
        winner = check_winner(b)
        
        # Terminal states
        if winner == 1:
            return 10 - depth  # Prefer winning sooner
        if winner == -1:
            return depth - 10  # Prefer losing later
        if not get_available_moves(b):
            return 0  # Draw

        if is_maximizing:
            best_score = -float('inf')
            for r, c in get_available_moves(b):
                b[r][c] = 1
                score = minimax(b, depth + 1, False)
                b[r][c] = 0
                best_score = max(score, best_score)
            return best_score
        else:
            best_score = float('inf')
            for r, c in get_available_moves(b):
                b[r][c] = -1
                score = minimax(b, depth + 1, True)
                b[r][c] = 0
                best_score = min(score, best_score)
            return best_score

    # Main policy logic
    best_score = -float('inf')
    best_move = None
    available_moves = get_available_moves(board)
    
    # If no moves available (board full), return center as a fallback (shouldn't happen in live game)
    if not available_moves:
        return (1, 1)

    # Find the move with the highest minimax score
    for r, c in available_moves:
        board[r][c] = 1
        score = minimax(board, 0, False)
        board[r][c] = 0
        
        if score > best_score:
            best_score = score
            best_move = (r, c)

    return best_move
