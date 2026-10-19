
import math

def _check_winner(board: list[list[int]]) -> None:
    """
    Checks the current board state for a winner or draw.
    Returns:
        1: Player 1 (AI) wins
        -1: Player -1 (Opponent) wins
        0: Draw
        None: Game is still ongoing
    """
    # Check rows
    for row in board:
        if sum(row) == 3:
            return 1
        if sum(row) == -3:
            return -1

    # Check columns
    for col_idx in range(3):
        col_sum = board[0][col_idx] + board[1][col_idx] + board[2][col_idx]
        if col_sum == 3:
            return 1
        if col_sum == -3:
            return -1

    # Check diagonals
    diag1_sum = board[0][0] + board[1][1] + board[2][2]
    diag2_sum = board[0][2] + board[1][1] + board[2][0]
    if diag1_sum == 3 or diag2_sum == 3:
        return 1
    if diag1_sum == -3 or diag2_sum == -3:
        return -1

    # Check for draw (no winner and board is full)
    is_full = True
    for r in range(3):
        for c in range(3):
            if board[r][c] == 0:
                is_full = False
                break
        if not is_full:
            break

    if is_full:
        return 0

    return None # Game not over yet

def _minimax(board: list[list[int]], current_player: int) -> int:
    """
    Minimax algorithm to determine the best score for the current player.
    Scores are from the perspective of the AI (player 1).
    """
    winner = _check_winner(board)

    if winner is not None:
        if winner == 1:
            return 10  # AI wins
        elif winner == -1:
            return -10 # Opponent wins
        else: # winner == 0 (draw)
            return 0

    if current_player == 1:  # AI's turn (Maximizing player)
        best_score = -math.inf
        for r in range(3):
            for c in range(3):
                if board[r][c] == 0:
                    board[r][c] = 1  # Make the move for AI
                    score = _minimax(board, -1) # Recurse for opponent
                    board[r][c] = 0  # Undo the move
                    best_score = max(best_score, score)
        return best_score
    else:  # Opponent's turn (Minimizing player from AI's perspective)
        best_score = math.inf
        for r in range(3):
            for c in range(3):
                if board[r][c] == 0:
                    board[r][c] = -1 # Make the move for opponent
                    score = _minimax(board, 1) # Recurse for AI
                    board[r][c] = 0  # Undo the move
                    best_score = min(best_score, score)
        return best_score


def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Determines the best move for the AI using the Minimax algorithm.

    Args:
        board: A 3x3 list of lists representing the Tic-Tac-Toe board.
               0 for empty, 1 for AI, -1 for opponent.

    Returns:
        A tuple (row, col) indicating the chosen move.
    """
    best_move = (-1, -1) # Default invalid move, should be overwritten by a valid one.
    best_score = -math.inf

    # Iterate through all empty cells to find the best move
    for r in range(3):
        for c in range(3):
            if board[r][c] == 0:
                # Try this move for the AI (player 1)
                board[r][c] = 1
                # Evaluate this move by calling minimax for the opponent's turn (-1)
                # The score returned is always from AI's perspective.
                score = _minimax(board, -1)
                board[r][c] = 0  # Undo the move to restore the board state

                if score > best_score:
                    best_score = score
                    best_move = (r, c)
                # In case of multiple moves with the same best_score,
                # the first one encountered will be returned. This is acceptable.

    return best_move
