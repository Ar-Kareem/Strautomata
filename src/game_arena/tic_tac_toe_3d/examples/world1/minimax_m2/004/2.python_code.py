
# Precompute all 49 winning lines for 3D Tic Tac Toe
def generate_winning_lines():
    lines = []
    # Rows in each layer (vary y, fixed x and z)
    for z in range(3):
        for x in range(3):
            line = [(z, x, y) for y in range(3)]
            lines.append(line)
    # Columns in each layer (vary x, fixed y and z)
    for z in range(3):
        for y in range(3):
            line = [(z, x, y) for x in range(3)]
            lines.append(line)
    # Vertical columns (vary z, fixed x and y)
    for x in range(3):
        for y in range(3):
            line = [(z, x, y) for z in range(3)]
            lines.append(line)
    # Diagonals in xy-planes (fixed z)
    for z in range(3):
        # Main diagonal: x=y
        line = [(z, i, i) for i in range(3)]
        lines.append(line)
        # Anti-diagonal: x+y=2
        line = [(z, i, 2-i) for i in range(3)]
        lines.append(line)
    # Diagonals in xz-planes (fixed y)
    for y in range(3):
        # Main diagonal: x=z
        line = [(i, i, y) for i in range(3)]
        lines.append(line)
        # Anti-diagonal: x+z=2
        line = [(2-i, i, y) for i in range(3)]
        lines.append(line)
    # Diagonals in yz-planes (fixed x)
    for x in range(3):
        # Main diagonal: y=z
        line = [(i, x, i) for i in range(3)]
        lines.append(line)
        # Anti-diagonal: y+z=2
        line = [(i, x, 2-i) for i in range(3)]
        lines.append(line)
    # Space diagonals
    lines.append([(0,0,0), (1,1,1), (2,2,2)])
    lines.append([(0,0,2), (1,1,1), (2,2,0)])
    lines.append([(0,2,0), (1,1,1), (2,0,2)])
    lines.append([(0,2,2), (1,1,1), (2,0,0)])
    return lines

WINNING_LINES = generate_winning_lines()

# Priority order for breaking ties (center, face centers, corners, edge centers)
PRIORITY_ORDER = [
    (1,1,1),
    (0,1,1), (2,1,1), (1,0,1), (1,2,1), (1,1,0), (1,1,2),
    (0,0,0), (0,0,2), (0,2,0), (0,2,2), (2,0,0), (2,0,2), (2,2,0), (2,2,2),
    (1,0,0), (1,2,0), (0,1,0), (2,1,0), (1,0,2), (1,2,2), (0,1,2), (2,1,2), 
    (0,0,1), (0,2,1), (2,0,1), (2,2,1)
]

def policy(board):
    # Find all empty cells
    empty_cells = []
    for z in range(3):
        for x in range(3):
            for y in range(3):
                if board[z][x][y] == 0:
                    empty_cells.append((z, x, y))
    
    # Step 1: Check for a winning move
    for (z, x, y) in empty_cells:
        for line in WINNING_LINES:
            if (z, x, y) in line:
                our_count = 0
                for (zz, xx, yy) in line:
                    if (zz, xx, yy) == (z, x, y):
                        continue
                    if board[zz][xx][yy] == 1:
                        our_count += 1
                if our_count == 2:
                    return (z, x, y)
    
    # Step 2: Check for a blocking move
    for (z, x, y) in empty_cells:
        for line in WINNING_LINES:
            if (z, x, y) in line:
                opp_count = 0
                for (zz, xx, yy) in line:
                    if (zz, xx, yy) == (z, x, y):
                        continue
                    if board[zz][xx][yy] == -1:
                        opp_count += 1
                if opp_count == 2:
                    return (z, x, y)
    
    # Step 3: Heuristic scoring for remaining moves
    scores = {}
    for (z, x, y) in empty_cells:
        score = 0
        for line in WINNING_LINES:
            if (z, x, y) in line:
                our_count = 0
                opp_count = 0
                for (zz, xx, yy) in line:
                    if (zz, xx, yy) == (z, x, y):
                        continue
                    if board[zz][xx][yy] == 1:
                        our_count += 1
                    elif board[zz][xx][yy] == -1:
                        opp_count += 1
                # Skip lines that would have been winning/blocking (handled in steps 1 and 2)
                if our_count == 2 or opp_count == 2:
                    continue
                if our_count == 1 and opp_count == 0:
                    score += 3
                elif our_count == 0 and opp_count == 0:
                    score += 1
                elif our_count == 0 and opp_count == 1:
                    score -= 1
                # If our_count==1 and opp_count==1, we skip (add 0)
        scores[(z, x, y)] = score
    
    # If no cell has a positive score, choose the highest score (could be negative) or the first in priority order?
    # We'll choose the cell with the highest score. If multiple, break ties by priority order.
    max_score = max(scores.values()) if scores else -10**9
    candidate_cells = [cell for cell, score in scores.items() if score == max_score]
    
    # If there are multiple candidates, choose the first one in the priority order that is in the candidate list.
    for priority_cell in PRIORITY_ORDER:
        if priority_cell in candidate_cells:
            return priority_cell
    
    # Fallback: return the first empty cell (should not happen if empty_cells is not empty)
    return empty_cells[0] if empty_cells else (0,0,0)
