
import numpy as np
import random

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    # Convert board to numpy array for easier manipulation
    board_np = np.array(board)
    
    # Check all possible lines for a winning move or block
    lines = []
    
    # Add all rows, columns, and depths
    for i in range(3):
        for j in range(3):
            lines.append(board_np[i, j, :])  # depth lines
            lines.append(board_np[i, :, j])  # column lines
            lines.append(board_np[:, i, j])  # row lines
    
    # Add all 4 space diagonals per face
    lines.append(np.array([board_np[i, i, i] for i in range(3)]))  # main diagonal
    lines.append(np.array([board_np[i, i, 2-i] for i in range(3)]))  # anti-diagonal
    lines.append(np.array([board_np[i, 2-i, i] for i in range(3)]))  # other diagonal
    lines.append(np.array([board_np[2-i, i, i] for i in range(3)]))  # other anti-diagonal
    
    # Check for immediate winning move (two 1's and a 0)
    for line in lines:
        if np.sum(line == 1) == 2 and np.sum(line == 0) == 1:
            empty_pos = np.where(line == 0)[0][0]
            # Find which coordinates correspond to this position
            if line is board_np[i, j, :]: return (i, j, empty_pos)
            if line is board_np[i, :, j]: return (i, empty_pos, j)
            if line is board_np[:, i, j]: return (empty_pos, i, j)
            if line is np.array([board_np[i, i, i] for i in range(3)]):
                return (empty_pos, empty_pos, empty_pos)
            if line is np.array([board_np[i, i, 2-i] for i in range(3)]):
                return (empty_pos, empty_pos, 2-empty_pos)
            if line is np.array([board_np[i, 2-i, i] for i in range(3)]):
                return (empty_pos, 2-empty_pos, empty_pos)
            if line is np.array([board_np[2-i, i, i] for i in range(3)]):
                return (2-empty_pos, empty_pos, empty_pos)
    
    # Check for opponent's winning move (two -1's and a 0)
    for line in lines:
        if np.sum(line == -1) == 2 and np.sum(line == 0) == 1:
            empty_pos = np.where(line == 0)[0][0]
            # Find which coordinates correspond to this position
            if line is board_np[i, j, :]: return (i, j, empty_pos)
            if line is board_np[i, :, j]: return (i, empty_pos, j)
            if line is board_np[:, i, j]: return (empty_pos, i, j)
            if line is np.array([board_np[i, i, i] for i in range(3)]):
                return (empty_pos, empty_pos, empty_pos)
            if line is np.array([board_np[i, i, 2-i] for i in range(3)]):
                return (empty_pos, empty_pos, 2-empty_pos)
            if line is np.array([board_np[i, 2-i, i] for i in range(3)]):
                return (empty_pos, 2-empty_pos, empty_pos)
            if line is np.array([board_np[2-i, i, i] for i in range(3)]):
                return (2-empty_pos, empty_pos, empty_pos)
    
    # Prioritize center if available
    if board_np[1, 1, 1] == 0:
        return (1, 1, 1)
    
    # Then prioritize corners
    corners = [(0, 0, 0), (0, 0, 2), (0, 2, 0), (0, 2, 2),
               (2, 0, 0), (2, 0, 2), (2, 2, 0), (2, 2, 2)]
    random.shuffle(corners)
    for corner in corners:
        if board_np[corner] == 0:
            return corner
    
    # Then prioritize edges
    edges = [(0, 0, 1), (0, 1, 0), (0, 1, 2), (0, 2, 1),
             (1, 0, 0), (1, 0, 2), (1, 2, 0), (1, 2, 2),
             (2, 0, 1), (2, 1, 0), (2, 1, 2), (2, 2, 1)]
    random.shuffle(edges)
    for edge in edges:
        if board_np[edge] == 0:
            return edge
    
    # Finally, any empty cell
    empty_cells = []
    for i in range(3):
        for j in range(3):
            for k in range(3):
                if board_np[i, j, k] == 0:
                    empty_cells.append((i, j, k))
    if empty_cells:
        return random.choice(empty_cells)
    
    # Shouldn't reach here if board isn't full
    return (0, 0, 0)
