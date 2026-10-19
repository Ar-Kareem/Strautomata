
import numpy as np
from itertools import product

def policy(you, opponent) -> str:
    you = np.array(you)
    opponent = np.array(opponent)
    board = you + opponent  # Combined board (1 = you, 2 = opponent)

    # Check all possible moves for immediate win
    for row, col in product(range(1, 7), range(1, 7)):
        if you[row-1, col-1] == 0 and board[row-1, col-1] == 0:
            for quad in range(4):
                for dir in ['L', 'R']:
                    new_board = simulate_move(you, opponent, row, col, quad, dir)
                    if check_win(new_board, 1):
                        return f"{row},{col},{quad},{dir}"

    # Block opponent's immediate win
    for row, col in product(range(1, 7), range(1, 7)):
        if opponent[row-1, col-1] == 0 and board[row-1, col-1] == 0:
            for quad in range(4):
                for dir in ['L', 'R']:
                    new_board = simulate_move(you, opponent, row, col, 2, dir)  # 2 = opponent
                    if check_win(new_board, 2):
                        return f"{row},{col},{quad},{dir}"

    # Strategy 1: Place in quadrant with least opponent advantage
    quad_scores = []
    for quad in range(4):
        you_count = np.sum(you[quad//3*3:quad//3*3+3, quad%2*3:quad%2*3+3])
        opp_count = np.sum(opponent[quad//3*3:quad//3*3+3, quad%2*3:quad%2*3+3])
        quad_scores.append(opp_count - you_count)  # Prefer quadrants where opponent has more marbles

    best_quad = np.argmin(quad_scores) if quad_scores else 0

    # Strategy 2: Place in center or high-opportunity cells
    empty_cells = np.argwhere(you == 0)
    center_cells = [(r, c) for r, c in empty_cells if 2 <= r < 5 and 2 <= c < 5]
    edge_cells = [(r, c) for r, c in empty_cells if (r in [0, 5] or c in [0, 5]) and (r not in [0, 5] or c not in [0, 5])]
    corner_cells = [(r, c) for r, c in empty_cells if (r in [0, 5] and c in [0, 5])]

    # Prioritize center > edge > corner
    candidates = center_cells if center_cells else edge_cells if edge_cells else corner_cells
    if not candidates:
        candidates = list(empty_cells)

    # Strategy 3: Evaluate potential moves for best line formation
    best_move = None
    best_score = -float('inf')

    for row, col in candidates:
        for quad in range(4):
            for dir in ['L', 'R']:
                new_board = simulate_move(you, opponent, row, col, quad, dir)
                score = evaluate_move(new_board, 1)
                if score > best_score:
                    best_score = score
                    best_move = f"{row+1},{col+1},{quad},{dir}"

    return best_move if best_move else "3,3,0,L"  # Fallback to center if no clear move

def simulate_move(you, opponent, row, col, quad, dir):
    """Simulate placing a marble and rotating a quadrant."""
    board = you + opponent
    new_you = you.copy()
    new_you[row, col] = 1
    new_board = new_you + opponent

    # Rotate the quadrant
    if dir == 'L':
        new_board[quad//3*3:quad//3*3+3, quad%2*3:quad%2*3+3] = np.rot90(
            new_board[quad//3*3:quad//3*3+3, quad%2*3:quad%2*3+3], -1)
    else:  # 'R'
        new_board[quad//3*3:quad//3*3+3, quad%2*3:quad%2*3+3] = np.rot90(
            new_board[quad//3*3:quad//3*3+3, quad%2*3:quad%2*3+3], 1)

    # Update you's board (since opponent's marbles are unchanged)
    new_you = new_board - opponent
    return new_you

def check_win(board, player):
    """Check if `player` (1 or 2) has a 5-in-a-row."""
    # Directions: horizontal, vertical, diagonal (2), anti-diagonal (2)
    directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
    for r, c in product(range(6), range(6)):
        if board[r, c] != player:
            continue
        for dr, dc in directions:
            count = 1
            for step in range(1, 5):
                nr, nc = r + step * dr, c + step * dc
                if 0 <= nr < 6 and 0 <= nc < 6 and board[nr, nc] == player:
                    count += 1
                else:
                    break
            for step in range(1, 5):
                nr, nc = r - step * dr, c - step * dc
                if 0 <= nr < 6 and 0 <= nc < 6 and board[nr, nc] == player:
                    count += 1
                else:
                    break
            if count >= 5:
                return True
    return False

def evaluate_move(board, player):
    """Evaluate how good a move is for `player` (1 or 2). Higher score = better."""
    score = 0
    # Check for potential lines (3, 4, or 5 in a row)
    directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
    for r, c in product(range(6), range(6)):
        if board[r, c] != player:
            continue
        for dr, dc in directions:
            count = 1
            for step in range(1, 5):
                nr, nc = r + step * dr, c + step * dc
                if 0 <= nr < 6 and 0 <= nc < 6 and board[nr, nc] == player:
                    count += 1
                else:
                    break
            for step in range(1, 5):
                nr, nc = r - step * dr, c - step * dc
                if 0 <= nr < 6 and 0 <= nc < 6 and board[nr, nc] == player:
                    count += 1
                else:
                    break
            if count >= 3:
                score += (count - 2) ** 2  # Bonus for longer lines
    return score
