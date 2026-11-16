
import random
from collections import deque

def is_legal_move(row: int, col: int, me: list[tuple[int, int]], opp: list[tuple[int, int]]) -> bool:
    """Check if a move is legal (within bounds and empty)."""
    return 0 <= row <= 10 and 0 <= col <= 10 and (row, col) not in me and (row, col) not in opp

def get_neighbors(row: int, col: int) -> list[tuple[int, int]]:
    """Return all 6 neighbors of a hexagonal cell (i, j)."""
    neighbors = [
        (row - 1, col), (row - 1, col + 1),
        (row, col - 1), (row, col + 1),
        (row + 1, col - 1), (row + 1, col)
    ]
    return [(r, c) for r, c in neighbors if 0 <= r <= 10 and 0 <= c <= 10]

def has_winning_path(board: dict[tuple[int, int], str], color: str) -> bool:
    """Check if the given color has a winning path using BFS."""
    if color == 'b':
        target_rows = {0, 10}  # Top and bottom for black
    else:
        target_rows = {0, 10}  # Left and right for white (columns 0 and 10)

    # Collect all cells of the given color
    color_cells = set(cell for cell, c in board.items() if c == color)

    # Check if any target cell is already occupied
    for cell in color_cells:
        if cell[0] in target_rows or (color == 'w' and cell[1] in {0, 10}):
            return True

    # BFS to find a path
    visited = set()
    queue = deque(color_cells)

    while queue:
        current = queue.popleft()
        if current in visited:
            continue
        visited.add(current)

        for neighbor in get_neighbors(*current):
            if neighbor in color_cells:
                if color == 'b' and neighbor[0] in target_rows:
                    return True
                if color == 'w' and neighbor[1] in {0, 10}:
                    return True
            elif neighbor not in visited:
                queue.append(neighbor)

    return False

def evaluate_move(row: int, col: int, me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> int:
    """Evaluate a move's potential to create a winning path or block the opponent."""
    # Simulate the move
    simulated_me = me.copy()
    simulated_me.append((row, col))
    simulated_board = {(r, c): color for r, c in simulated_me}
    simulated_board.update({(r, c): 'w' if (r, c) in opp else 'b' for r, c in opp})

    # Check if the move creates a winning path for me
    if has_winning_path(simulated_board, color):
        return 1000  # Highest priority: winning move

    # Check if the move blocks the opponent's winning path
    simulated_opp = opp.copy()
    simulated_opp.append((row, col))
    simulated_opp_board = {(r, c): 'w' if color == 'b' else 'b' for r, c in simulated_opp}
    simulated_opp_board.update({(r, c): color for r, c in simulated_me})

    opponent_color = 'w' if color == 'b' else 'b'
    if has_winning_path(simulated_opp_board, opponent_color):
        return -1000  # Highest priority to block opponent

    # Heuristic: prefer moves near the center
    center_score = min(row, col) + min(row, 10 - col) + min(col, 10 - col)
    return center_score

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:
    """Generate the next move using a heuristic-based policy."""
    best_move = None
    best_score = -float('inf')

    # Iterate over all empty cells
    for row in range(11):
        for col in range(11):
            if is_legal_move(row, col, me, opp):
                score = evaluate_move(row, col, me, opp, color)
                if score > best_score:
                    best_score = score
                    best_move = (row, col)

    # If no winning/blocking move found, fall back to randomness
    if best_move is None:
        empty_cells = [(r, c) for r in range(11) for c in range(11) if is_legal_move(r, c, me, opp)]
        best_move = random.choice(empty_cells)

    return best_move
