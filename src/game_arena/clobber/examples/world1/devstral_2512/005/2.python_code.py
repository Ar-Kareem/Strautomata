
import random
import numpy as np
from typing import List, Tuple

def policy(you: List[List[int]], opponent: List[List[int]]) -> str:
    # Convert to numpy arrays for easier manipulation
    you_board = np.array(you)
    opp_board = np.array(opponent)
    rows, cols = you_board.shape

    # Directions: U, R, D, L
    directions = [(-1, 0), (0, 1), (1, 0), (0, -1)]
    dir_chars = ['U', 'R', 'D', 'L']

    # Generate all legal moves
    legal_moves = []
    for r in range(rows):
        for c in range(cols):
            if you_board[r, c] == 1:
                for i, (dr, dc) in enumerate(directions):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < rows and 0 <= nc < cols:
                        if opp_board[nr, nc] == 1:
                            legal_moves.append((r, c, dir_chars[i]))

    # If no legal moves, return any (shouldn't happen as per problem statement)
    if not legal_moves:
        return "0,0,U"

    # Evaluate each move
    best_move = None
    best_score = -float('inf')

    for move in legal_moves:
        r, c, dir = move
        dr, dc = directions[dir_chars.index(dir)]
        nr, nc = r + dr, c + dc

        # Simulate the move
        temp_you = you_board.copy()
        temp_opp = opp_board.copy()

        # Execute the move
        temp_you[r, c] = 0
        temp_you[nr, nc] = 1
        temp_opp[nr, nc] = 0

        # Calculate score for this move
        score = evaluate_move(temp_you, temp_opp, r, c, nr, nc)

        if score > best_score:
            best_score = score
            best_move = move

    # Format the best move
    return f"{best_move[0]},{best_move[1]},{best_move[2]}"

def evaluate_move(you_board: np.ndarray, opp_board: np.ndarray,
                 from_r: int, from_c: int, to_r: int, to_c: int) -> float:
    rows, cols = you_board.shape
    score = 0

    # 1. Center control bonus
    center_rows = range(1, 4)
    center_cols = range(1, 5)
    if to_r in center_rows and to_c in center_cols:
        score += 2.0

    # 2. Edge penalty (unless it's a winning move)
    if to_r == 0 or to_r == rows-1 or to_c == 0 or to_c == cols-1:
        score -= 0.5

    # 3. Mobility - count potential future moves
    your_moves = count_potential_moves(you_board, opp_board)
    opp_moves = count_potential_moves(opp_board, you_board)
    score += (your_moves - opp_moves) * 0.3

    # 4. Check if this move leaves opponent with no moves (immediate win)
    if opp_moves == 0:
        score += 100  # Very high priority for winning move

    # 5. Distance from original position (encourage movement toward center)
    center_r, center_c = rows // 2, cols // 2
    dist_before = abs(from_r - center_r) + abs(from_c - center_c)
    dist_after = abs(to_r - center_r) + abs(to_c - center_c)
    if dist_after < dist_before:
        score += 0.2

    return score

def count_potential_moves(board: np.ndarray, opponent_board: np.ndarray) -> int:
    """Count how many potential moves a player has from the given board state."""
    rows, cols = board.shape
    directions = [(-1, 0), (0, 1), (1, 0), (0, -1)]
    count = 0

    for r in range(rows):
        for c in range(cols):
            if board[r, c] == 1:
                for dr, dc in directions:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < rows and 0 <= nc < cols:
                        if opponent_board[nr, nc] == 1:
                            count += 1
    return count
