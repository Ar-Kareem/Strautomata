
import numpy as np

def policy(board: list[list[int]]) -> tuple[int, int]:
    # Convert to numpy array for easier manipulation
    board = np.array(board)
    
    # Get all empty (0) positions
    empty_positions = [(i, j) for i in range(3) for j in range(3) if board[i][j] == 0]
    
    # If no empty positions, this shouldn't happen per rules, but defend.
    if not empty_positions:
        return (0, 0)  # fallback, shouldn't be reached
    
    # Define winning lines: rows, cols, diagonals
    lines = [
        # Rows
        [(0,0), (0,1), (0,2)],
        [(1,0), (1,1), (1,2)],
        [(2,0), (2,1), (2,2)],
        # Cols
        [(0,0), (1,0), (2,0)],
        [(0,1), (1,1), (2,1)],
        [(0,2), (1,2), (2,2)],
        # Diagonals
        [(0,0), (1,1), (2,2)],
        [(0,2), (1,1), (2,0)]
    ]
    
    # Check for immediate win: if we can complete a line with one of our moves
    for line in lines:
        our_marks = [board[i][j] for i, j in line]
        # Count our confirmed marks in this line
        count_ours = sum(1 for x in our_marks if x == 1)
        # Count empty positions in this line
        count_empty = sum(1 for x in our_marks if x == 0)
        # If we have 2 of our own and 1 empty, we can win by playing there
        if count_ours == 2 and count_empty == 1:
            for i, j in line:
                if board[i][j] == 0:
                    return (i, j)
    
    # Check for immediate block: if opponent could complete a line by placing in an empty cell
    # We assume opponent has placed optimally. For each empty cell, check if filling it would complete a line for opponent
    # Since we don't know opponent marks, we must assume that any line with two 0s and one 1 could be threatening
    # Actually, opponent has placed in 0s — so if a line has two 0s and no 1s, it could be opponent's two-in-a-row
    # But we don't know if they have two. The safest heuristic: if a line has two 0s and we have zero marks, then it's highly dangerous
    # However, we must also consider: if a line has one 0 and two 1s? That's our win — already handled.
    # The threat: opponent has two in a line, and we have none. That line is blocked only if we fill the empty spot.
    for line in lines:
        our_marks = [board[i][j] for i, j in line]
        count_ours = sum(1 for x in our_marks if x == 1)
        count_empty = sum(1 for x in our_marks if x == 0)
        # If opponent has two marks and we have none, then we must block
        if count_ours == 0 and count_empty == 1:
            # In this case, if opponent has filled the other two, then we must place on the last one
            # But wait — we don't know if opponent filled them! So this is risky.
            # Alternate heuristic: if a line has two zeros, and we have zero, then it's a potential opponent win.
            # But that's always true if two zeros are present. So we use:
            # Only block if there's exactly one empty and we have zero: because then the opponent has two
            # But this is only valid if we assume opponent has filled those two. Since we don't see them,
            # we must assume the worst: if we see one zero and two empty, it's ambiguous.
            
            # Let's change strategy: check if any line has exactly two 0s and no 1s — then the opponent might have two there.
            # We need to block one of them. But we don't know which. So we block the first one we find in a line with two 0s and zero 1s?
            # Actually, we can't know. So a better heuristic: if multiple lines have two 0s and zero 1s, then all those empty cells are dangerous.
            # We'll pick the first dangerous cell (i.e., any empty cell that lies in a line with two other 0s and zero 1s).
            continue  # we'll handle below in the dangerous cells section
    
    # Check for any line with two 0s and zero 1s — these are dangerous
    dangerous_cells = set()
    for line in lines:
        our_marks = [board[i][j] for i, j in line]
        count_ours = sum(1 for x in our_marks if x == 1)
        count_empty = sum(1 for x in our_marks if x == 0)
        if count_ours == 0 and count_empty == 2:
            # This line has two empty cells — opponent might already have both? Not necessarily — but if they placed first, they might have two here.
            # We can't tell which one they took, so we treat all as potentially dangerous. But we can only block one.
            # Let's assume the opponent is trying to win. So they would have taken two in this line.
            # We must block one of them — we'll pick the one that is also part of the highest priority cell.
            # We'll record all cells in such lines as dangerous.
            for i, j in line:
                if board[i][j] == 0:
                    dangerous_cells.add((i, j))
    
    # Check for lines with three 0s: equally dangerous, but we can block by taking center or corner.
    
    # Prioritize: if we have a dangerous cell, block it — but only if it's in a line with two 0s and zero 1s
    if dangerous_cells:
        # Among dangerous cells, prefer center, then corners
        for cell in [(1,1), (0,0), (0,2), (2,0), (2,2), (0,1), (1,0), (1,2), (2,1)]:
            if cell in dangerous_cells:
                return cell
    
    # Check for immediate win already done.
    # Now check for center
    if board[1][1] == 0:
        return (1, 1)
    
    # Check for corners: (0,0), (0,2), (2,0), (2,2)
    corners = [(0,0), (0,2), (2,0), (2,2)]
    for corner in corners:
        if board[corner[0]][corner[1]] == 0:
            return corner
    
    # Otherwise, return any remaining empty cell (edge)
    return empty_positions[0]
