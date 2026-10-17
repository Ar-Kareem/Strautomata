
import numpy as np

def policy(board: list[list[int]], legal_moves: list[int]) -> int:
    # Convert legal_moves to (row, col) pairs for easier handling
    move_to_coord = {i: (i // 3, i % 3) for i in range(9)}
    coord_to_move = {(r, c): r * 3 + c for r in range(3) for c in range(3)}
    
    # Separate legal moves into coordinates
    legal_coords = [move_to_coord[m] for m in legal_moves]

    # Define all lines (rows, cols, diagonals)
    lines = [
        # Rows
        [(0, 0), (0, 1), (0, 2)],
        [(1, 0), (1, 1), (1, 2)],
        [(2, 0), (2, 1), (2, 2)],
        # Columns
        [(0, 0), (1, 0), (2, 0)],
        [(0, 1), (1, 1), (2, 1)],
        [(0, 2), (1, 2), (2, 2)],
        # Diagonals
        [(0, 0), (1, 1), (2, 2)],
        [(0, 2), (1, 1), (2, 0)]
    ]

    # Step 1: Check for immediate winning moves (two of our marks + one legal unknown)
    for line in lines:
        our_marks = 0
        unknowns = []
        for r, c in line:
            if board[r][c] == 1:
                our_marks += 1
            elif (r, c) in legal_coords:
                unknowns.append((r, c))
        if our_marks == 2 and len(unknowns) == 1:
            # We can win by playing this unknown
            return coord_to_move[unknowns[0]]

    # Step 2: Prioritize center
    if (1, 1) in legal_coords:
        return coord_to_move[(1, 1)]

    # Step 3: Prioritize corners
    corners = [(0, 0), (0, 2), (2, 0), (2, 2)]
    available_corners = [c for c in corners if c in legal_coords]
    if available_corners:
        return coord_to_move[available_corners[0]]

    # Step 4: Fall back to any legal move (edges)
    return coord_to_move[legal_coords[0]]
