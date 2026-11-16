
def policy(state: list[list[object]], role: str) -> str:
    # Extract board state
    board = {}
    available_cells = []
    
    for cell in state:
        if cell[0] == "cell":
            row, col, owner = int(cell[1]), int(cell[2]), cell[3]
            board[(row, col)] = owner
            if owner == "b":
                available_cells.append((row, col))
    
    # If no cells available (shouldn't happen), return any valid move
    if not available_cells:
        return "mark(1,1)"
    
    # Collect cards for each player
    my_cards = [(r, c) for (r, c), owner in board.items() if owner == role]
    opp_role = "o" if role == "x" else "x"
    opp_cards = [(r, c) for (r, c), owner in board.items() if owner == opp_role]
    
    # Try to find winning move
    for row, col in available_cells:
        test_cards = my_cards + [(row, col)]
        if is_winning(test_cards):
            return f"mark({row},{col})"
    
    # Try to block opponent's winning move
    for row, col in available_cells:
        test_cards = opp_cards + [(row, col)]
        if is_winning(test_cards):
            return f"mark({row},{col})"
    
    # Prefer center and corners (more combinations possible)
    priority_moves = [(2, 2), (1, 1), (1, 3), (3, 1), (3, 3), (1, 2), (2, 1), (2, 3), (3, 2)]
    for move in priority_moves:
        if move in available_cells:
            return f"mark({move[0]},{move[1]})"
    
    # Fallback to first available
    row, col = available_cells[0]
    return f"mark({row},{col})"

def is_winning(cards):
    """Check if three cards form a winning combination based on position patterns."""
    if len(cards) < 3:
        return False
    
    # Check for three cards in same row
    rows = {}
    cols = {}
    for r, c in cards:
        rows[r] = rows.get(r, 0) + 1
        cols[c] = cols.get(c, 0) + 1
    
    if any(count >= 3 for count in rows.values()):
        return True
    if any(count >= 3 for count in cols.values()):
        return True
    
    # Check diagonals
    diag1 = sum(1 for r, c in cards if r == c)
    diag2 = sum(1 for r, c in cards if r + c == 4)
    
    if diag1 >= 3 or diag2 >= 3:
        return True
    
    # Check position-based patterns (assuming attributes map to positions)
    # Pattern: corners share a property
    corners = {(1,1), (1,3), (3,1), (3,3)}
    if len([card for card in cards if card in corners]) >= 3:
        return True
    
    # Pattern: edges share a property
    edges = {(1,2), (2,1), (2,3), (3,2)}
    if len([card for card in cards if card in edges]) >= 3:
        return True
    
    return False
