
import numpy as np

def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    board_size = 19
    board = np.zeros((board_size, board_size), dtype=int)

    # Mark my stones and opponent's stones on the board
    for r, c in me:
        board[r-1, c-1] = 1  # My stones
    for r, c in opponent:
        board[r-1, c-1] = -1  # Opponent's stones

    # Function to evaluate a move
    def evaluate_move(r, c):
        if board[r, c] != 0:  # Illegal move (occupied)
            return float('-inf')
        
        score = 0

        # Check for capturing the opponent stones
        # Check all four directions for surrounding
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        for dr, dc in directions:
            surrounding = []
            for d in range(1, 3):  # Check for 1, 2 spaces around the move
                nr, nc = r + dr * d, c + dc * d
                if 0 <= nr < board_size and 0 <= nc < board_size:
                    if board[nr, nc] == -1:
                        surrounding.append(-1)  # Opponent stone
                    elif board[nr, nc] == 1:
                        surrounding.append(1)   # My stone
                    else:
                        surrounding.append(0)   # Empty
                else:
                    surrounding.append(0)       # Out of bounds

            # If we surround opponent stones, we can count this as score
            if surrounding.count(-1) == 2 and surrounding.count(1) == 0:
                score += 5  # Capturing stones
            if surrounding.count(1) == 2 and surrounding.count(-1) == 0:
                score -= 1  # Avoid losing stones

        return score

    best_move = (0, 0)  # Default to pass
    best_score = float('-inf')

    # Evaluate all possible moves
    for r in range(board_size):
        for c in range(board_size):
            score = evaluate_move(r, c)
            if score > best_score:
                best_score = score
                best_move = (r + 1, c + 1)  # Move from 0-indexed to 1-indexed

    return best_move
