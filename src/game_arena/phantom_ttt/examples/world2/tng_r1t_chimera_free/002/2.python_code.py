
import random

def policy(board: list[list[int]]) -> tuple[int, int]:
    available = [(r, c) for r in range(3) for c in range(3) if board[r][c] == 0]
    
    winning_moves = []
    for r, c in available:
        # Check row
        if sum(board[r]) == 2 and board[r][c] == 0:
            winning_moves.append((r, c))
            continue
        # Check column
        col_sum = board[0][c] + board[1][c] + board[2][c]
        if col_sum == 2 and board[r][c] == 0:
            winning_moves.append((r, c))
            continue
        # Check diagonal \
        if r == c:
            diag_sum = board[0][0] + board[1][1] + board[2][2]
            if diag_sum == 2 and board[r][c] == 0:
                winning_moves.append((r, c))
                continue
        # Check diagonal /
        if r + c == 2:
            diag_sum = board[0][2] + board[1][1] + board[2][0]
            if diag_sum == 2 and board[r][c] == 0:
                winning_moves.append((r, c))
    
    if winning_moves:
        return random.choice(winning_moves)
    
    # Prioritize center
    if (1, 1) in available:
        return (1, 1)
    
    # Next prioritize corners
    corners = [(0, 0), (0, 2), (2, 0), (2, 2)]
    available_corners = [cell for cell in corners if cell in available]
    if available_corners:
        return random.choice(available_corners)
    
    # Finally pick edges
    edges = [(0, 1), (1, 0), (1, 2), (2, 1)]
    available_edges = [cell for cell in edges if cell in available]
    if available_edges:
        return random.choice(available_edges)
    
    # Fallback (shouldn't be reached in valid game states)
    return available[0]
