
import random
from typing import List, Tuple

def policy(me: List[Tuple[int, int]], opp: List[Tuple[int, int]], color: str) -> Tuple[int, int]:
    """
    Hex policy for 11x11 board. Returns the next move as (row, col).
    Strategy:
    1. Check if current move can win (top-bottom for black, left-right for white).
    2. Block opponent's winning threats if no immediate win.
    3. Extend own paths or control center.
    4. Fallback to random legal move if no clear strategy.
    """
    board_size = 11
    my_color = color
    opp_color = 'w' if color == 'b' else 'b'

    # Generate all possible legal moves (empty cells)
    all_cells = set((i, j) for i in range(board_size) for j in range(board_size))
    occupied_cells = set(me).union(set(opp))
    legal_moves = list(all_cells - occupied_cells)

    # Check if current move can win
    for move in legal_moves:
        if can_win(me + [move], opp, my_color):
            return move

    # Check if opponent has a winning threat and block it
    for move in legal_moves:
        if can_win(opp + [move], me, opp_color):
            return move

    # If no immediate win/block, prioritize strategic moves
    # Heuristic 1: Center control (highest value cells)
    center_priority = []
    for i in range(board_size):
        for j in range(board_size):
            # Distance to center (5,5)
            dist = abs(i - 5) + abs(j - 5)
            if dist <= 2:  # Cells near center
                center_priority.append((i, j))

    # Heuristic 2: Adjacent to own stones (path extension)
    adjacent_to_me = []
    for (i, j) in me:
        for di, dj in [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, 1), (1, -1)]:
            ni, nj = i + di, j + dj
            if 0 <= ni < board_size and 0 <= nj < board_size and (ni, nj) not in occupied_cells:
                adjacent_to_me.append((ni, nj))

    # Heuristic 3: Avoid giving opponent too many adjacent empty cells
    avoid_moves = []
    for (i, j) in legal_moves:
        # Count opponent's adjacent empty cells
        opp_adjacent = 0
        for di, dj in [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, 1), (1, -1)]:
            ni, nj = i + di, j + dj
            if 0 <= ni < board_size and 0 <= nj < board_size and (ni, nj) not in occupied_cells:
                if any((ni, nj) in neighbors for (x, y) in opp for (ni, nj) in neighbors((x, y))):
                    opp_adjacent += 1
        if opp_adjacent >= 3:  # High risk, avoid
            avoid_moves.append((i, j))

    # Combine heuristics: prioritize center, then adjacent, then avoid risky moves
    prioritized_moves = []
    for move in center_priority:
        if move not in occupied_cells and move not in avoid_moves:
            prioritized_moves.append(move)
    for move in adjacent_to_me:
        if move not in occupied_cells and move not in avoid_moves and move not in prioritized_moves:
            prioritized_moves.append(move)

    # Fallback to random legal move if no prioritized move found
    if not prioritized_moves:
        return random.choice(legal_moves)
    else:
        return prioritized_moves[0]

def neighbors(cell: Tuple[int, int]) -> List[Tuple[int, int]]:
    """Returns all 6 neighbors of a cell in Hex grid."""
    i, j = cell
    board_size = 11
    return [
        (i - 1, j), (i + 1, j),  # Top and bottom row
        (i, j - 1), (i, j + 1),  # Left and right column
        (i - 1, j + 1), (i + 1, j - 1)  # Diagonal neighbors
    ]

def can_win(me: List[Tuple[int, int]], opp: List[Tuple[int, int]], color: str) -> bool:
    """
    Checks if `me` has a winning path (top-bottom for black, left-right for white).
    Uses DFS to explore all possible connected paths.
    """
    board_size = 11
    occupied = set(me).union(set(opp))
    my_stones = set(me)
    opp_stones = set(opp)

    # Determine start and end rows/cols based on color
    if color == 'b':  # Black: top (0) to bottom (10)
        start_side = {(0, j) for j in range(board_size)}
        end_side = {(10, j) for j in range(board_size)}
    else:  # White: left (0) to right (10)
        start_side = {(i, 0) for i in range(board_size)}
        end_side = {(i, 10) for i in range(board_size)}

    # Check if any stone in start_side is connected to end_side via my stones
    for start in start_side:
        if start in my_stones:
            visited = set()
            stack = [start]
            while stack:
                current = stack.pop()
                if current in visited:
                    continue
                visited.add(current)
                for neighbor in neighbors(current):
                    if neighbor in my_stones and neighbor not in visited:
                        stack.append(neighbor)
                    if neighbor in end_side and neighbor in my_stones:
                        return True
    return False
