
import random

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    A Battleship-playing policy that combines hunting and targeting strategies.
    """

    def get_neighbors(row, col):
        neighbors = []
        if row > 0:
            neighbors.append((row - 1, col))
        if row < 9:
            neighbors.append((row + 1, col))
        if col > 0:
            neighbors.append((row, col - 1))
        if col < 9:
            neighbors.append((row, col + 1))
        return neighbors

    def get_legal_moves():
        legal_moves = []
        for r in range(10):
            for c in range(10):
                if board[r][c] == 0:
                    legal_moves.append((r, c))
        return legal_moves

    # Targeting Phase: If there are hits, prioritize neighbors
    hit_cells = []
    for r in range(10):
        for c in range(10):
            if board[r][c] == 1:
                hit_cells.append((r, c))

    if hit_cells:
        potential_targets = []
        for r, c in hit_cells:
            neighbors = get_neighbors(r, c)
            for nr, nc in neighbors:
                if board[nr][nc] == 0:
                    potential_targets.append((nr, nc))
        if potential_targets:
            return random.choice(potential_targets)
    
    # Hunting Phase: Use checkerboard pattern
    legal_moves = get_legal_moves()
    if legal_moves:
        checkerboard_moves = []
        for r, c in legal_moves:
            if (r + c) % 2 == 0:  # Choose one checkerboard pattern
                checkerboard_moves.append((r, c))
        if checkerboard_moves:
            return random.choice(checkerboard_moves)
        else:
            return random.choice(legal_moves) # If no checkerboard moves left

    # Fallback: If no legal moves are found (should not happen)
    return (0, 0)
