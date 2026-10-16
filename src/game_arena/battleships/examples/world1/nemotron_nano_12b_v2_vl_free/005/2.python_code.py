
import random

def policy(board: list[list[int]]) -> tuple[int, int]:
    # Collect all known hit positions
    hits = []
    for row in range(10):
        for col in range(10):
            if board[row][col] == 1:
                hits.append((row, col))
    
    # Check all hits in order for possible adjacent targets
    for (hit_row, hit_col) in hits:
        # Check directions in priority order: right, down, left, up
        for (dr, dc) in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            r, c = hit_row + dr, hit_col + dc
            if 0 <= r < 10 and 0 <= c < 10 and board[r][c] == 0:
                return (r, c)
    
    # If no suspicious cells found, select randomly from unshot cells
    possible_moves = [(r, c) for r in range(10) for c in range(10) if board[r][c] == 0]
    if possible_moves:
        return random.choice(possible_moves)
    else:
        # Fallback (shouldn't occur with legal moves remaining)
        return (0, 0)
