
import numpy as np
import random

def policy(you: list[int], opponent: list[int]) -> str:
    """
    Smart policy for Clobber game on a 5x6 grid.
    Prioritizes aggressive moves, central control, and defensive blocking.
    """
    # Convert input lists to numpy arrays for easier manipulation
    you_board = np.array(you, dtype=int)
    opponent_board = np.array(opponent, dtype=int)

    # Get all your pieces' positions
    your_pieces = np.argwhere(you_board == 1)

    # Generate all legal moves (captures)
    legal_moves = []
    for (row, col) in your_pieces:
        for dir in ['U', 'R', 'D', 'L']:
            new_row, new_col = row, col
            if dir == 'U':
                new_row -= 1
            elif dir == 'R':
                new_col += 1
            elif dir == 'D':
                new_row += 1
            elif dir == 'L':
                new_col -= 1

            # Check if move is in bounds and captures opponent
            if 0 <= new_row < 5 and 0 <= new_col < 6 and opponent_board[new_row, new_col] == 1:
                legal_moves.append((row, col, dir))

    if not legal_moves:
        return "0,0,U"  # Should never happen (disqualification fallback)

    # Evaluate each move and select the best one
    best_move = None
    best_score = -float('inf')

    for move in legal_moves:
        row, col, dir = move
        new_row, new_col = row, col
        if dir == 'U':
            new_row -= 1
        elif dir == 'R':
            new_col += 1
        elif dir == 'D':
            new_row += 1
        elif dir == 'L':
            new_col -= 1

        # Simulate the move
        temp_you = you_board.copy()
        temp_you[row, col] = 0
        temp_you[new_row, new_col] = 1
        temp_opponent = opponent_board.copy()
        temp_opponent[new_row, new_col] = 0

        # Score the move
        score = evaluate_move(temp_you, temp_opponent)

        if score > best_score:
            best_score = score
            best_move = move

    # Return the best move found
    return f"{best_move[0]},{best_move[1]},{best_move[2]}"

def evaluate_move(you_board: np.ndarray, opponent_board: np.ndarray) -> float:
    """
    Evaluates a move by scoring the resulting board state.
    Higher score = better move (more aggressive, more central, more mobility).
    """
    # Get opponent's legal moves after this capture
    opponent_pieces = np.argwhere(opponent_board == 1)
    opponent_moves = []
    for (row, col) in opponent_pieces:
        for dir in ['U', 'R', 'D', 'L']:
            new_row, new_col = row, col
            if dir == 'U':
                new_row -= 1
            elif dir == 'R':
                new_col += 1
            elif dir == 'D':
                new_row += 1
            elif dir == 'L':
                new_col -= 1

            if 0 <= new_row < 5 and 0 <= new_col < 6 and you_board[new_row, new_col] == 1:
                opponent_moves.append((row, col, dir))

    # Score 1: Opponent's mobility (fewer moves = better)
    opponent_mobility = len(opponent_moves)
    score = 1000 / (opponent_mobility + 1)  # Avoid division by zero

    # Score 2: Centrality of the captured piece (center is rows 2-3, cols 2-3)
    # The piece we just captured is now at (row, col) in you_board
    captured_piece_pos = np.argwhere(you_board == 1)[-1]  # Last piece added (the captured one)
    row, col = captured_piece_pos
    centrality = min(abs(row - 2), abs(row - 3)) + min(abs(col - 2), abs(col - 3))
    score += 100 * (2 - centrality)  # Higher for more central pieces

    # Score 3: Mobility of the capturing piece (more moves = better)
    capturing_piece_pos = np.argwhere(you_board == 1)[:-1]  # All pieces except the last one
    mobility = 0
    for (row, col) in capturing_piece_pos:
        for dir in ['U', 'R', 'D', 'L']:
            new_row, new_col = row, col
            if dir == 'U':
                new_row -= 1
            elif dir == 'R':
                new_col += 1
            elif dir == 'D':
                new_row += 1
            elif dir == 'L':
                new_col -= 1

            if 0 <= new_row < 5 and 0 <= new_col < 6 and opponent_board[new_row, new_col] == 1:
                mobility += 1
    score += mobility * 5  # Reward mobility

    # Score 4: Threat creation (how many of our pieces can capture opponent pieces after this move)
    threats = 0
    for (row, col) in np.argwhere(you_board == 1):
        for dir in ['U', 'R', 'D', 'L']:
            new_row, new_col = row, col
            if dir == 'U':
                new_row -= 1
            elif dir == 'R':
                new_col += 1
            elif dir == 'D':
                new_row += 1
            elif dir == 'L':
                new_col -= 1

            if 0 <= new_row < 5 and 0 <= new_col < 6 and opponent_board[new_row, new_col] == 1:
                threats += 1
    score += threats * 10  # Strongly reward threat creation

    return score
