
import numpy as np

def policy(board: list[list[int]], legal_moves: list[int]) -> int:
    # Convert board to numpy array for easier manipulation
    board_np = np.array(board)
    legal_moves_np = np.array([(move // 3, move % 3) for move in legal_moves])
    
    # Check for winning moves (complete a line with two 1s and one empty)
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
    
    for line in lines:
        values = [board_np[row, col] for row, col in line]
        if values.count(1) == 2 and 0 in values:
            empty_pos = line[values.index(0)]
            if empty_pos in legal_moves_np:
                return empty_pos
    
    # Check for blocking moves (two 0s and no 1s in a line)
    for line in lines:
        values = [board_np[row, col] for row, col in line]
        if values.count(0) == 2 and 1 not in values:
            empty_pos = line[values.index(0)]
            if empty_pos in legal_moves_np:
                return empty_pos
    
    # Prefer center if available
    center = (1, 1)
    if center in legal_moves_np and board_np[1, 1] == 0:
        return center
    
    # Prefer corners
    corners = [(0, 0), (0, 2), (2, 0), (2, 2)]
    for corner in corners:
        if corner in legal_moves_np and board_np[corner] == 0:
            return corner
    
    # Prefer edges
    edges = [(0, 1), (1, 0), (1, 2), (2, 1)]
    for edge in edges:
        if edge in legal_moves_np and board_np[edge] == 0:
            return edge
    
    # Fallback: choose first legal move (shouldn't happen if legal_moves is correct)
    return legal_moves_np[0]
