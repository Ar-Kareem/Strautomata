
import numpy as np

def get_flips(board, row, col, player):
    opponent = 1 - player
    flips = []
    directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]

    for d_row, d_col in directions:
        r, c = row + d_row, col + d_col
        temp_flips = []
        while 0 <= r < 8 and 0 <= c < 8:
            if board[r][c] == opponent:
                temp_flips.append((r, c))
            elif board[r][c] == player:
                flips.extend(temp_flips)
                break
            else:
                break
            r += d_row
            c += d_col

    return flips

def find_legal_moves(you, opponent):
    legal_moves = []
    for r in range(8):
        for c in range(8):
            if you[r][c] == 0 and opponent[r][c] == 0:
                flips = get_flips(np.add(you, opponent), r, c, 1)
                if flips:
                    legal_moves.append((r, c, len(flips)))
    return legal_moves

def evaluate_move(you, opponent, row, col):
    flips = get_flips(np.add(you, opponent), row, col, 1)
    return len(flips)

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    legal_moves = find_legal_moves(you, opponent)
    
    if not legal_moves:
        return "pass"

    # Sort moves based on the number of flips and prioritize corner captures
    corner_positions = [(0, 0), (0, 7), (7, 0), (7, 7)]
    priorities = []

    for r, c, flip_count in legal_moves:
        priority = flip_count
        if (r, c) in corner_positions:
            priority += 10  # add extra score for corners
        priorities.append((priority, r, c))

    # Sort by highest priority first
    priorities.sort(reverse=True)

    best_move = priorities[0]
    row, col = best_move[1], best_move[2]
    
    # Convert to algebraic notation
    col_letter = chr(col + ord('a'))
    row_number = str(row + 1)
    
    return f"{col_letter}{row_number}"
