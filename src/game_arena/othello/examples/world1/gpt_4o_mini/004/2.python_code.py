
import numpy as np

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    def is_valid_move(x, y):
        return 0 <= x < 8 and 0 <= y < 8 and (you[x][y] == 0 and opponent[x][y] == 0)

    def can_flip(x, y, dx, dy):
        flips = 0
        x += dx
        y += dy
        while is_valid_move(x, y) is False and (you[x][y] == 0 and opponent[x][y] == 1):
            flips += 1
            x += dx
            y += dy
        return flips > 0 and is_valid_move(x, y) and you[x][y] == 1, flips
    
    def get_legal_moves():
        moves = []
        for i in range(8):
            for j in range(8):
                if you[i][j] == 0 and opponent[i][j] == 0:
                    # Check all 8 directions
                    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]:
                        can_flip_line, flips = can_flip(i, j, dx, dy)
                        if can_flip_line:
                            moves.append((i, j, flips))  # Store position and flips potential
        return moves
    
    def evaluate_move(move):
        x, y, flips = move
        score = flips
        # Additional scoring based on position
        if (x in [0, 7] and y in [0, 7]):  # corners
            score += 10
        elif (x in [0, 7] or y in [0, 7]):  # edges
            score += 5
        return score
    
    legal_moves = get_legal_moves()
    if not legal_moves:
        return "pass"
    
    best_move = max(legal_moves, key=evaluate_move)
    move_row, move_col, _ = best_move
    return f"{chr(move_col + 97)}{move_row + 1}"

