
import random

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Returns the next move for a 4x4 Tic Tac Toe game.
    Prioritizes: 1. Win, 2. Block, 3. Center, 4. Corners/Edges.
    """
    size = 4
    
    def get_lines():
        # Rows
        for r in range(size):
            yield [(r, c) for c in range(size)]
        # Columns
        for c in range(size):
            yield [(r, c) for r in range(size)]
        # Diagonals
        yield [(i, i) for i in range(size)]
        yield [(i, size - 1 - i) for i in range(size)]

    empty_cells = [(r, c) for r in range(size) for c in range(size) if board[r][c] == 0]
    
    if not empty_cells:
        return (0, 0)

    # 1. Check for immediate win
    for move in empty_cells:
        r, c = move
        board[r][c] = 1
        for line in get_lines():
            if all(board[lr][lc] == 1 for lr, lc in line):
                board[r][c] = 0
                return move
        board[r][c] = 0

    # 2. Check for immediate block
    for move in empty_cells:
        r, c = move
        board[r][c] = -1
        for line in get_lines():
            if all(board[lr][lc] == -1 for lr, lc in line):
                board[r][c] = 0
                return move
        board[r][c] = 0

    # 3. Strategy: Prefer center positions (1,1), (1,2), (2,1), (2,2)
    center_spots = [(1, 1), (1, 2), (2, 1), (2, 2)]
    available_centers = [p for p in center_spots if p in empty_cells]
    if available_centers:
        return random.choice(available_centers)

    # 4. Fallback: Corners or any empty cell
    corners = [(0, 0), (0, 3), (3, 0), (3, 3)]
    available_corners = [p for p in corners if p in empty_cells]
    if available_corners:
        return random.choice(available_corners)

    return random.choice(empty_cells)
