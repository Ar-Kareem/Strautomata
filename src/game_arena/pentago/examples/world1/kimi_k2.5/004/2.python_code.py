
import numpy as np

# Precompute all lines of 5 cells for win detection
LINES = []
# Horizontal: 6 rows, 2 starting positions per row (0-4, 1-5)
for r in range(6):
    for c in range(2):
        LINES.append([(r, c + i) for i in range(5)])
# Vertical: 6 cols, 2 starting positions per col
for r in range(2):
    for c in range(6):
        LINES.append([(r + i, c) for i in range(5)])
# Diagonal \ : top-left to bottom-right
for r in range(2):
    for c in range(2):
        LINES.append([(r + i, c + i) for i in range(5)])
# Diagonal / : top-right to bottom-left
for r in range(2):
    for c in range(4, 6):
        LINES.append([(r + i, c - i) for i in range(5)])

def has_five(board):
    """Check if player has 5 in a row on the board."""
    for line in LINES:
        s = 0
        for r, c in line:
            s += board[r, c]
        if s == 5:
            return True
    return False

def rotate_boards(you, opp, quad, direction):
    """Rotate specified quadrant for both players. Returns new boards."""
    you = you.copy()
    opp = opp.copy()
    
    # Quadrant top-left corners (0-indexed)
    qs = [(0, 0), (0, 3), (3, 0), (3, 3)]
    r, c = qs[quad]
    
    # Extract subgrids
    sub_you = you[r:r+3, c:c+3].copy()
    sub_opp = opp[r:r+3, c:c+3].copy()
    
    # Rotate: L=90° CCW (k=1), R=90° CW (k=-1 or 3)
    if direction == 'L':
        sub_you = np.rot90(sub_you, 1)
        sub_opp = np.rot90(sub_opp, 1)
    else:
        sub_you = np.rot90(sub_you, -1)
        sub_opp = np.rot90(sub_opp, -1)
    
    you[r:r+3, c:c+3] = sub_you
    opp[r:r+3, c:c+3] = sub_opp
    
    return you, opp

def evaluate_position(you, opp):
    """Heuristic evaluation: count threats (4,3,2 in a row)."""
    score = 0
    
    for line in LINES:
        my_count = 0
        opp_count = 0
        
        for r, c in line:
            if you[r, c]:
                my_count += 1
            elif opp[r, c]:
                opp_count += 1
        
        # Only score if line is not blocked by opponent
        if opp_count == 0:
            if my_count == 4:
                score += 10000  # Winning threat
            elif my_count == 3:
                score += 100
            elif my_count == 2:
                score += 10
        # Penalize opponent threats
        elif my_count == 0:
            if opp_count == 4:
                score -= 10000
            elif opp_count == 3:
                score -= 100
            elif opp_count == 2:
                score -= 10
    
    return score

def policy(you, opponent):
    you = np.array(you, dtype=np.int8)
    opponent = np.array(opponent, dtype=np.int8)
    
    # Find empty cells
    empty_mask = (you == 0) & (opponent == 0)
    empty_cells = list(zip(*np.where(empty_mask)))
    
    best_move = None
    best_score = -float('inf')
    
    # Try all possible moves
    for r, c in empty_cells:
        for quad in range(4):
            for rot in ['L', 'R']:
                # Simulate: place then rotate
                temp_you = you.copy()
                temp_you[r, c] = 1
                temp_opp = opponent.copy()
                
                new_you, new_opp = rotate_boards(temp_you, temp_opp, quad, rot)
                
                me_win = has_five(new_you)
                opp_win = has_five(new_opp)
                
                # Immediate win
                if me_win and not opp_win:
                    return f"{r+1},{c+1},{quad},{rot}"
                
                # Skip moves that let opponent win immediately
                if opp_win and not me_win:
                    continue
                
                # Evaluate position
                score = evaluate_position(new_you, new_opp)
                
                # Positional bonus: prefer center (2.5 is center of 0-5)
                score += (3 - abs(r - 2.5)) * 5
                score += (3 - abs(c - 2.5)) * 5
                
                if score > best_score:
                    best_score = score
                    best_move = (r, c, quad, rot)
    
    # If all moves are losing (or draw), pick first legal
    if best_move is None:
        r, c = empty_cells[0]
        return f"{r+1},{c+1},0,L"
    
    r, c, quad, rot = best_move
    return f"{r+1},{c+1},{quad},{rot}"
