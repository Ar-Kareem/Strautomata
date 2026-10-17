
import numpy as np
from collections import deque

def policy(you: list[int], opponent: list[int]) -> str:
    # Convert to numpy arrays for easier manipulation
    you_board = np.array(you, dtype=int)
    opponent_board = np.array(opponent, dtype=int)

    # Directions: U, R, D, L
    directions = [(-1, 0, 'U'), (0, 1, 'R'), (1, 0, 'D'), (0, -1, 'L')]

    # Generate all possible legal moves
    legal_moves = []
    for row in range(5):
        for col in range(6):
            if you_board[row, col] == 1:
                for dr, dc, dir in directions:
                    nr, nc = row + dr, col + dc
                    if 0 <= nr < 5 and 0 <= nc < 6 and opponent_board[nr, nc] == 1:
                        legal_moves.append((row, col, dir))

    if not legal_moves:
        return ""  # Should not happen as per problem statement

    # If no legal moves, return empty string (though problem says you always have a move)
    if not legal_moves:
        return ""

    # Evaluate each move using a heuristic
    best_move = None
    best_score = -float('inf')

    for move in legal_moves:
        row, col, dir = move
        dr, dc, _ = next((d for d in directions if d[2] == dir), (0, 0, ''))
        nr, nc = row + dr, col + dc

        # Simulate the move
        new_you = you_board.copy()
        new_opponent = opponent_board.copy()
        new_you[row, col] = 0
        new_you[nr, nc] = 1
        new_opponent[nr, nc] = 0

        # Evaluate the new board state
        score = evaluate_board(new_you, new_opponent)

        if score > best_score:
            best_score = score
            best_move = move

    return f"{best_move[0]},{best_move[1]},{best_move[2]}"

def evaluate_board(you_board, opponent_board):
    # Heuristic evaluation function
    score = 0

    # Piece count difference
    score += np.sum(you_board) - np.sum(opponent_board)

    # Center control (center is roughly rows 1-3, cols 2-3)
    center_you = np.sum(you_board[1:4, 2:4])
    center_opponent = np.sum(opponent_board[1:4, 2:4])
    score += 2 * (center_you - center_opponent)  # Weight center more

    # Corner control (corners are strategic)
    corners = [(0, 0), (0, 5), (4, 0), (4, 5)]
    corner_you = sum(you_board[r, c] for r, c in corners)
    corner_opponent = sum(opponent_board[r, c] for r, c in corners)
    score += 3 * (corner_you - corner_opponent)  # Weight corners more

    # Edge control (edges are also important)
    edges = [(0, 1), (0, 4), (1, 0), (1, 5), (3, 0), (3, 5), (4, 1), (4, 4)]
    edge_you = sum(you_board[r, c] for r, c in edges)
    edge_opponent = sum(opponent_board[r, c] for r, c in edges)
    score += 2 * (edge_you - edge_opponent)  # Weight edges

    # Mobility: number of legal moves for you and opponent
    you_moves = count_legal_moves(you_board, opponent_board)
    opponent_moves = count_legal_moves(opponent_board, you_board)
    score += you_moves - opponent_moves

    return score

def count_legal_moves(you_board, opponent_board):
    # Count legal moves for the given player
    directions = [(-1, 0), (0, 1), (1, 0), (0, -1)]
    count = 0
    for row in range(5):
        for col in range(6):
            if you_board[row, col] == 1:
                for dr, dc in directions:
                    nr, nc = row + dr, col + dc
                    if 0 <= nr < 5 and 0 <= nc < 6 and opponent_board[nr, nc] == 1:
                        count += 1
    return count
