
import numpy as np

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    # Generate all legal moves
    legal_moves = []
    # Horizontal edges: row 0-4, col 0-3
    for i in range(5):
        for j in range(4):
            if horizontal[i, j] == 0:
                legal_moves.append(('H', i, j))
    # Vertical edges: row 0-3, col 0-4
    for i in range(4):
        for j in range(5):
            if vertical[i, j] == 0:
                legal_moves.append(('V', i, j))

    # If no legal moves, return None (should not happen in a valid game)
    if not legal_moves:
        return None

    # Check for capturing moves
    capturing_moves = []
    for move in legal_moves:
        dir, i, j = move
        # Simulate drawing the edge
        h_copy = horizontal.copy()
        v_copy = vertical.copy()
        cap_copy = capture.copy()
        
        if dir == 'H':
            h_copy[i, j] = 1
        else:
            v_copy[i, j] = 1

        # Check for completed boxes
        boxes_captured = 0
        for x in range(4):
            for y in range(4):
                if cap_copy[x, y] == 0:
                    # Count the number of drawn edges for box (x,y)
                    count = 0
                    if h_copy[x, y] != 0:
                        count += 1
                    if h_copy[x+1, y] != 0:
                        count += 1
                    if v_copy[x, y] != 0:
                        count += 1
                    if v_copy[x, y+1] != 0:
                        count += 1
                    if count == 4:
                        cap_copy[x, y] = 1
                        boxes_captured += 1
        
        if boxes_captured > 0:
            capturing_moves.append((move, boxes_captured))
    
    # If there are capturing moves, choose the one with the most captures
    if capturing_moves:
        # Find the maximum number of captures
        max_captures = max(capture_count for _, capture_count in capturing_moves)
        # Filter moves with max_captures
        best_moves = [move for move, count in capturing_moves if count == max_captures]
        # Choose randomly among best_moves
        chosen_move = best_moves[np.random.randint(0, len(best_moves))]
        return f"{chosen_move[1]},{chosen_move[2]},{chosen_move[0]}"
    
    # No capturing moves, so evaluate each move for threatened boxes
    min_threats = float('inf')
    safe_moves = []
    for move in legal_moves:
        dir, i, j = move
        # Simulate drawing the edge
        h_copy = horizontal.copy()
        v_copy = vertical.copy()
        cap_copy = capture.copy()
        
        if dir == 'H':
            h_copy[i, j] = 1
        else:
            v_copy[i, j] = 1

        # Count threatened boxes after this move
        threats = 0
        for x in range(4):
            for y in range(4):
                if cap_copy[x, y] == 0:
                    count = 0
                    if h_copy[x, y] != 0:
                        count += 1
                    if h_copy[x+1, y] != 0:
                        count += 1
                    if v_copy[x, y] != 0:
                        count += 1
                    if v_copy[x, y+1] != 0:
                        count += 1
                    if count == 3:
                        threats += 1
        
        if threats == 0:
            safe_moves.append(move)
        if threats < min_threats:
            min_threats = threats
            best_moves = [move]
        elif threats == min_threats:
            best_moves.append(move)
    
    # If there are safe moves (threats==0), choose one of them randomly
    if safe_moves:
        chosen_move = safe_moves[np.random.randint(0, len(safe_moves))]
    else:
        # Choose among the best_moves (with min_threats)
        chosen_move = best_moves[np.random.randint(0, len(best_moves))]
    
    return f"{chosen_move[1]},{chosen_move[2]},{chosen_move[0]}"
