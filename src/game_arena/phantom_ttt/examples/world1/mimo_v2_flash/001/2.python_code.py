
import random

def policy(board: list[list[int]], legal_moves: list[int]) -> tuple[int, int]:
    """
    Plays Phantom Tic Tac Toe.
    Strategy:
    1. Check for immediate win (2 marks in a line, 1 empty).
    2. Block immediate loss (implied, though opponent is hidden, we focus on our offense).
    3. Place Center (1,1) if free.
    4. Place Corner if free.
    5. Place Side if free.
    Uses 'legal_moves' to filter moves allowed by the game engine.
    """
    
    # Helper to convert (row, col) to index 0-8
    def to_idx(r, c): return r * 3 + c
    
    # Helper to convert index 0-8 to (row, col)
    def to_pos(i): return (i // 3, i % 3)

    # Helper to check if a specific cell is confirmed mine on the board
    def is_my_mark(r, c): return board[r][c] == 1
    
    # Helper to get lines (list of (r, c) tuples)
    def get_lines():
        lines = []
        # Rows and Cols
        for i in range(3):
            lines.append([(i, 0), (i, 1), (i, 2)]) # Row
            lines.append([(0, i), (1, i), (2, i)]) # Col
        # Diagonals
        lines.append([(0, 0), (1, 1), (2, 2)])
        lines.append([(0, 2), (1, 1), (2, 0)])
        return lines

    # 1. Identify available actions based on board knowledge and engine constraints
    # We must filter legal_moves to exclude cells we *know* we occupy (though unlikely to be in legal_moves)
    # And specifically look for moves we can attempt.
    valid_moves = []
    for move_idx in legal_moves:
        r, c = to_pos(move_idx)
        if not is_my_mark(r, c): # Don't attempt to overwrite my own mark
            valid_moves.append((r, c))
    
    if not valid_moves:
        # Should not happen if engine is correct, but fallback to any legal move if forced
        return to_pos(legal_moves[0])

    # 2. Check for Win: Do I have 2 in a line with 1 empty?
    # Iterate all lines
    potential_wins = []
    for line in get_lines():
        my_count = 0
        empty_in_line = []
        for r, c in line:
            if is_my_mark(r, c):
                my_count += 1
            elif (r, c) in valid_moves: # Only count if valid move (not blocked by known logic)
                empty_in_line.append((r, c))
        
        # If I have 2 marks and exactly 1 empty spot in that line, I must play there.
        if my_count == 2 and len(empty_in_line) == 1:
            return empty_in_line[0]
        # If I have 2 marks but >1 empty, it implies I don't have enough info to win (unlikely in 3x3 usually 1 empty)
        # If I have 2 marks but 0 empty in my valid_moves, it's blocked.
        
    # 3. Strategic Placement
    
    # Define priorities
    center = (1, 1)
    corners = [(0, 0), (0, 2), (2, 0), (2, 2)]
    sides = [(0, 1), (1, 0), (1, 2), (2, 1)]

    # Priority 1: Center
    if center in valid_moves:
        return center

    # Priority 2: Corners
    available_corners = [c for c in corners if c in valid_moves]
    if available_corners:
        return random.choice(available_corners)

    # Priority 3: Sides
    available_sides = [s for s in sides if s in valid_moves]
    if available_sides:
        return random.choice(available_sides)

    # Fallback (shouldn't reach here if valid_moves is populated)
    return valid_moves[0]
