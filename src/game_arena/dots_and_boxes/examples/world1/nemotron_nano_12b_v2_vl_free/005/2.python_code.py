
import numpy as np

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    # Generate all legal moves
    legal_moves = []
    # Check horizontal edges (H)
    for row in range(5):
        for col in range(5):
            if horizontal[row, col] == 0:
                legal_moves.append((row, col, 'H'))
    # Check vertical edges (V)
    for row in range(5):
        for col in range(5):
            if vertical[row, col] == 0:
                legal_moves.append((row, col, 'V'))
    
    candidate_moves = []
    
    # Evaluate each move
    for move in legal_moves:
        row, col, dir = move
        
        # Create copies to simulate the move
        new_h = np.copy(horizontal)
        new_v = np.copy(vertical)
        new_c = np.copy(capture)
        
        # Apply the move
        if dir == 'H':
            new_h[row, col] = 1
        else:
            new_v[row, col] = 1
        
        # Find captured boxes
        captured = 0
        boxes_to_check = []
        
        if dir == 'H':
            if row > 0:
                boxes_to_check.append((row - 1, col))
            if row < 4:
                boxes_to_check.append((row, col))
        else:  # dir == 'V'
            if col > 0:
                boxes_to_check.append((row, col - 1))
            if col < 4:
                boxes_to_check.append((row, col))
        
        # Check each relevant box for completion
        for i, j in boxes_to_check:
            if new_c[i, j] != 0:
                continue  # Already captured
            top = new_h[i][j]
            bottom = new_h[i+1][j]
            left = new_v[i][j]
            right = new_v[i][j+1]
            if all([top != 0, bottom != 0, left != 0, right != 0]):
                new_c[i][j] = 1
                captured += 1
        
        # Count threes after applying the move
        threes = 0
        for i in range(4):
            for j in range(4):
                if new_c[i][j] != 0:
                    continue
                top = new_h[i][j]
                bottom = new_h[i+1][j]
                left = new_v[i][j]
                right = new_v[i][j+1]
                cnt = (top != 0) + (bottom != 0) + (left != 0) + (right != 0)
                if cnt == 3:
                    threes += 1
        
        candidate_moves.append((captured, threes, move))
    
    # Select the best move
    if not candidate_moves:
        return None  # Edge case: no moves possible (shouldn't happen in valid game)
    
    capturing_moves = [cm for cm in candidate_moves if cm[0] > 0]
    if capturing_moves:
        # Sort capturing moves by captured first, then threes ascending
        capturing_moves.sort(key=lambda x: (-x[0], x[1]))
        return process_move(capturing_moves[0][2])
    else:
        # No capturing moves, minimize threes created
        non_capturing = [(t, m) for c, t, m in candidate_moves]
        if not non_capturing:
            return None  # Edge case (shouldn't happen)
        non_capturing.sort(key=lambda x: (x[0], x[1]))
        return process_move(non_capturing[0][1])

def process_move(move):
    row, col, dir = move
    return f"{row},{col},{dir}"
