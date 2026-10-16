
import numpy as np

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    # Find all legal moves (edges that are empty)
    candidate_moves = []
    for row in range(5):
        for col in range(4):
            if horizontal[row, col] == 0:
                candidate_moves.append(('H', row, col))
    for row in range(4):
        for col in range(5):
            if vertical[row, col] == 0:
                candidate_moves.append(('V', row, col))
    
    if not candidate_moves:
        return '0,0,H'  # Fallback (shouldn't occur in valid games)
    
    # Evaluate each candidate move
    move_details = []
    for move in candidate_moves:
        typ, row, col = move
        boxes = []
        if typ == 'H':
            if row == 0:
                boxes = [(0, col)]
            elif row == 1:
                boxes = [(0, col), (1, col)]
            elif row == 2:
                boxes = [(1, col), (2, col)]
            elif row == 3:
                boxes = [(2, col), (3, col)]
            elif row == 4:
                boxes = [(3, col)]
        else:  # 'V'
            if col == 0:
                boxes = [(row, 0)]
            elif col == 1:
                boxes = [(row, 0), (row, 1)]
            elif col == 2:
                boxes = [(row, 1), (row, 2)]
            elif col == 3:
                boxes = [(row, 2), (row, 3)]
            elif col == 4:
                boxes = [(row, 3)]
        
        captures = 0
        for (i, j) in boxes:
            # Check if this move completes any boxes
            if typ == 'H':
                if row == i and col == j:  # Top edge
                    if horizontal[i+1, j] == 1 and vertical[i, j] == 1 and vertical[i, j+1] == 1:
                        captures += 1
                elif row == i+1 and col == j:  # Bottom edge
                    if horizontal[i, j] == 1 and vertical[i, j] == 1 and vertical[i, j+1] == 1:
                        captures += 1
            else:  # 'V'
                if col == j and row == i:  # Left edge
                    if horizontal[i, j] == 1 and horizontal[i+1, j] == 1 and vertical[i, j+1] == 1:
                        captures += 1
                elif col == j+1 and row == i:  # Right edge
                    if horizontal[i, j] == 1 and horizontal[i+1, j] == 1 and vertical[i, j] == 1:
                        captures += 1
        
        # Priority 1: Capture boxes
        if captures >= 1:
            move_details.append((captures, 1, move, boxes))
        else:
            # Priority 2: Avoid completing opponent's boxes
            # Priority 3: Choose boxes with fewest edges
            min_edges = float('inf')
            for (i, j) in boxes:
                edges = horizontal[i, j] + horizontal[i+1, j] + vertical[i, j] + vertical[i, j+1]
                if edges < min_edges:
                    min_edges = edges
            move_details.append((captures, min_edges, move, boxes))
    
    # Select best move
    best_move = None
    best_captures = -1
    for details in move_details:
        captures, _, move, _ = details
        if captures > best_captures:
            best_captures = captures
            best_move = move
    if best_move is None:
        best_move = candidate_moves[0]
    return f"{best_move[1]},{best_move[2]},{best_move[0]}"
