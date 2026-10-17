
import numpy as np
import random

def policy(you: list[int], opponent: list[int]) -> str:
    # Convert to numpy arrays for easier manipulation
    you_board = np.array(you).reshape(5, 6)
    opp_board = np.array(opponent).reshape(5, 6)

    # Directions: U, R, D, L
    directions = [(-1, 0, 'U'), (0, 1, 'R'), (1, 0, 'D'), (0, -1, 'L')]

    # Find all possible moves
    possible_moves = []
    for row in range(5):
        for col in range(6):
            if you_board[row, col] == 1:
                for dr, dc, dir in directions:
                    new_row, new_col = row + dr, col + dc
                    if 0 <= new_row < 5 and 0 <= new_col < 6:
                        if opp_board[new_row, new_col] == 1:
                            possible_moves.append((row, col, dir))

    if not possible_moves:
        # This should never happen as per problem statement
        return "0,0,U"

    # Evaluate moves based on strategy
    def evaluate_move(row, col, dir):
        # Center control bonus
        center_bonus = 0
        if 1 <= row <= 3 and 1 <= col <= 4:
            center_bonus = 2

        # Edge penalty
        edge_penalty = 0
        if row in [0, 4] or col in [0, 5]:
            edge_penalty = -1

        # Mobility consideration
        mobility = 0
        for dr, dc, _ in directions:
            new_row, new_col = row + dr, col + dc
            if 0 <= new_row < 5 and 0 <= new_col < 6:
                if opp_board[new_row, new_col] == 1:
                    mobility += 1

        return center_bonus + edge_penalty + mobility

    # Score all moves
    scored_moves = []
    for move in possible_moves:
        row, col, dir = move
        score = evaluate_move(row, col, dir)
        scored_moves.append((score, move))

    # Sort by score (descending)
    scored_moves.sort(key=lambda x: (-x[0], random.random()))

    # Return the best move
    best_move = scored_moves[0][1]
    return f"{best_move[0]},{best_move[1]},{best_move[2]}"
